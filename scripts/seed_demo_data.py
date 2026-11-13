"""
scripts/seed_demo_data.py - Seeds the SQLite database with rich initial demonstration data.
Populates:
- transactions (2,200+ scored records)
- fraud_alerts (high & critical alerts)
- aml_cases (structuring, mule, rapid movement, circular cases)
- suspicious_accounts (risk profiles and aggregates)
- system_activity
"""

from pathlib import Path
import sys
import json

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import numpy as np
import pandas as pd
import database
from generator import TransactionGenerator
from fraud_engine import FraudEngine
from aml_engine import AMLEngine
from risk_engine import RiskEngine

DATA_DIR = ROOT_DIR / "data"


def seed():
    print("[1/5] Initializing SQLite database...")
    database.init_database()
    database.reset_database()

    print("[2/5] Generating/Loading transactions...")
    csv_path = DATA_DIR / "finguard_transactions.csv"
    if not csv_path.exists():
        gen = TransactionGenerator(seed=42)
        df = gen.generate_full_dataset(total_normal=2000)
    else:
        df = pd.read_csv(csv_path)

    df["timestamp"] = pd.to_datetime(df["timestamp"])
    print(f"Loaded {len(df)} transactions.")

    print("[3/5] Initializing AI Engines...")
    fraud_engine = FraudEngine()
    aml_engine = AMLEngine()
    risk_engine = RiskEngine()

    print("[4/5] Executing AML detection on corpus...")
    aml_results = aml_engine.run_all_checks(df)
    print(f"Found {len(aml_results['all_cases'])} AML cases.")

    for case in aml_results["all_cases"]:
        database.insert_aml_case(case)

    struct_ids = set(t for c in aml_results["structuring_cases"] for t in c["related_txns"])
    mule_ids = set(t for c in aml_results["mule_cases"] for t in c["related_txns"])
    circ_ids = set(t for c in aml_results["circular_cases"] for t in c["related_txns"])
    rapid_ids = set(t for c in aml_results["rapid_movement_cases"] for t in c["related_txns"])

    print("[5/5] Scoring transactions with ML + AML and generating alerts...")

    # Fast vectorized ML feature extraction
    df_feat = df.copy()
    df_feat["hour_of_day"] = df_feat["timestamp"].dt.hour
    df_feat["is_night"] = df_feat["hour_of_day"].apply(lambda h: 1 if h >= 22 or h <= 5 else 0)
    df_feat["is_weekend"] = df_feat["timestamp"].dt.weekday.apply(lambda w: 1 if w >= 5 else 0)
    df_feat["is_cross_city"] = (df_feat["sender_location"] != df_feat["receiver_location"]).astype(int)
    df_feat["is_high_value"] = (df_feat["amount"] > 100000.0).astype(int)
    df_feat["velocity_sender_5m"] = 1
    df_feat["time_since_last_sender_txn"] = 99999.0
    df_feat["amount_ratio"] = df_feat["amount"] / 5000.0

    le_type = fraud_engine.encoders.get("transaction_type")
    le_cat = fraud_engine.encoders.get("merchant_category")

    if le_type:
        df_feat["transaction_type_enc"] = df_feat["transaction_type"].apply(
            lambda x: le_type.transform([str(x)])[0] if str(x) in le_type.classes_ else 0
        )
    else:
        df_feat["transaction_type_enc"] = 0

    if le_cat:
        df_feat["merchant_category_enc"] = df_feat["merchant_category"].apply(
            lambda x: le_cat.transform([str(x)])[0] if str(x) in le_cat.classes_ else 0
        )
    else:
        df_feat["merchant_category_enc"] = 0

    cols = fraud_engine.meta.get("feature_cols", [
        "amount", "hour_of_day", "is_night", "is_weekend",
        "is_cross_city", "is_high_value", "velocity_sender_5m",
        "time_since_last_sender_txn", "amount_ratio",
        "transaction_type_enc", "merchant_category_enc"
    ])

    X_mat = df_feat[cols].fillna(0)

    # Batch ML Predictions in 0.05 seconds
    fraud_probas = fraud_engine.xgb_model.predict_proba(X_mat)[:, 1] if fraud_engine.xgb_model else np.zeros(len(df))
    X_scaled = fraud_engine.scaler.transform(X_mat) if fraud_engine.scaler else X_mat
    raw_decisions = fraud_engine.iso_model.decision_function(X_scaled) if fraud_engine.iso_model else np.zeros(len(df))
    anomaly_scores = np.clip(0.5 - raw_decisions, 0.0, 1.0)

    scored_records = []
    alerts_to_insert = []
    account_stats = {}

    for idx, row in enumerate(df.to_dict(orient="records")):
        txn_id = row["transaction_id"]
        sender = row["sender_account"]
        receiver = row["receiver_account"]
        amt = float(row["amount"])

        if sender not in account_stats:
            account_stats[sender] = {"in_count": 0, "out_count": 0, "in_amt": 0.0, "out_amt": 0.0, "max_risk": 0.0, "patterns": set()}
        if receiver not in account_stats:
            account_stats[receiver] = {"in_count": 0, "out_count": 0, "in_amt": 0.0, "out_amt": 0.0, "max_risk": 0.0, "patterns": set()}

        account_stats[sender]["out_count"] += 1
        account_stats[sender]["out_amt"] += amt
        account_stats[receiver]["in_count"] += 1
        account_stats[receiver]["in_amt"] += amt

        f_prob = float(fraud_probas[idx])
        a_score = float(anomaly_scores[idx])

        ml_pred = {
            "fraud_probability": f_prob,
            "anomaly_score": a_score,
            "velocity_anomaly": {"count_5m": 1, "is_spike": False},
            "behavioral_anomaly": {"risk_flags": []}
        }

        aml_tags = {
            "is_structuring": txn_id in struct_ids,
            "is_mule": txn_id in mule_ids,
            "is_circular": txn_id in circ_ids,
            "is_rapid_movement": txn_id in rapid_ids
        }

        risk_eval = risk_engine.evaluate_transaction(row, ml_pred, aml_tags)
        score = risk_eval["risk_score"]
        cat = risk_eval["risk_category"]

        account_stats[sender]["max_risk"] = max(account_stats[sender]["max_risk"], score)
        account_stats[receiver]["max_risk"] = max(account_stats[receiver]["max_risk"], score * 0.7)

        for p in risk_eval["detection_reasons"]:
            if "normal" not in p.lower():
                account_stats[sender]["patterns"].add(p)

        row_to_insert = dict(row)
        row_to_insert["risk_score"] = score
        row_to_insert["risk_category"] = cat
        scored_records.append(row_to_insert)

        if score >= 50.0:
            alerts_to_insert.append({
                "transaction_id": txn_id,
                "risk_score": score,
                "risk_category": cat,
                "primary_reason": "; ".join(risk_eval["detection_reasons"][:2]),
                "evidence": risk_eval["supporting_evidence"],
                "recommended_action": risk_eval["recommended_action"],
                "status": "OPEN",
                "assigned_to": "Tier-2 AML Investigator" if score >= 75.0 else "Analyst Queue"
            })

    # Batch insert into database
    print(f"Inserting {len(scored_records)} transactions into SQLite...")
    database.insert_transactions_batch(scored_records)

    print(f"Inserting {len(alerts_to_insert)} fraud alerts into SQLite...")
    database.insert_fraud_alerts_batch(alerts_to_insert)

    print(f"Updating suspicious accounts...")
    for acc_id, stats in account_stats.items():
        if stats["max_risk"] >= 40.0 or stats["in_count"] + stats["out_count"] >= 4:
            database.update_suspicious_account({
                "account_id": acc_id,
                "incoming_count": stats["in_count"],
                "outgoing_count": stats["out_count"],
                "total_incoming_amount": stats["in_amt"],
                "total_outgoing_amount": stats["out_amt"],
                "risk_score": stats["max_risk"],
                "risk_level": risk_engine.categorize_risk(stats["max_risk"]),
                "suspicious_patterns": list(stats["patterns"])[:5],
                "investigation_status": "ESCALATED" if stats["max_risk"] >= 75.0 else ("UNDER_REVIEW" if stats["max_risk"] >= 50.0 else "NORMAL")
            })

    database.log_activity("DATABASE_SEED", f"Successfully seeded database with {len(scored_records)} scored transactions.")
    kpis = database.fetch_kpis()
    print("\n=== Seeding Finished Successfully ===")
    print("Database KPIs:", json.dumps(kpis, indent=2))


if __name__ == "__main__":
    seed()
