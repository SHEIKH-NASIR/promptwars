"""
scripts/train_finguard_models.py
Trains and persists:
1. FinGuard XGBoost Supervised Fraud Classifier
2. FinGuard Isolation Forest Unsupervised Anomaly Detector
3. Scaler and categorical feature encoders
Works on data/finguard_transactions.csv
"""

import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import classification_report, roc_auc_score
from xgboost import XGBClassifier

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT_DIR / "data" / "finguard_transactions.csv"
MODELS_DIR = ROOT_DIR / "models"
REPORTS_DIR = ROOT_DIR / "reports"
MODELS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def extract_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    df["hour_of_day"] = df["timestamp"].dt.hour
    df["is_night"] = df["hour_of_day"].apply(lambda h: 1 if h >= 22 or h <= 5 else 0)
    df["is_weekend"] = df["timestamp"].dt.weekday.apply(lambda w: 1 if w >= 5 else 0)
    df["is_cross_city"] = (df["sender_location"] != df["receiver_location"]).astype(int)
    df["is_high_value"] = (df["amount"] > 100000.0).astype(int)

    # Sort to compute rolling velocity
    df = df.sort_values(["sender_account", "timestamp"]).reset_index(drop=True)
    df["velocity_sender_5m"] = 0
    df["time_since_last_sender_txn"] = 99999.0

    # Calculate sender velocities
    sender_groups = df.groupby("sender_account")
    v_list = []
    t_diff_list = []
    for sender, group in sender_groups:
        diffs = group["timestamp"].diff().dt.total_seconds().fillna(99999.0).values
        # Count within 300s
        for idx, (t, d) in enumerate(zip(group["timestamp"].values, diffs)):
            # Window check
            window_start = t - np.timedelta64(5, 'm')
            cnt = np.sum((group["timestamp"].values >= window_start) & (group["timestamp"].values <= t))
            v_list.append((group.index[idx], cnt, d))

    v_df = pd.DataFrame(v_list, columns=["idx", "velocity_sender_5m", "time_since_last_sender_txn"]).set_index("idx")
    df["velocity_sender_5m"] = v_df["velocity_sender_5m"]
    df["time_since_last_sender_txn"] = v_df["time_since_last_sender_txn"]

    avg_amt = df["amount"].median()
    df["amount_ratio"] = df["amount"] / max(avg_amt, 1.0)

    return df


def main():
    if not DATA_PATH.exists():
        from generator import TransactionGenerator
        gen = TransactionGenerator(seed=42)
        gen.generate_full_dataset()

    raw_df = pd.read_csv(DATA_PATH)
    df = extract_features(raw_df)

    num_features = [
        "amount", "hour_of_day", "is_night", "is_weekend",
        "is_cross_city", "is_high_value", "velocity_sender_5m",
        "time_since_last_sender_txn", "amount_ratio"
    ]
    cat_features = ["transaction_type", "merchant_category"]

    encoders = {}
    for cat in cat_features:
        le = LabelEncoder()
        df[cat + "_enc"] = le.fit_transform(df[cat].astype(str))
        encoders[cat] = le

    feature_cols = num_features + [c + "_enc" for cat in cat_features for c in [cat]]

    X = df[feature_cols].fillna(0)
    y = df["fraud_label"].astype(int)

    # 1. Train Isolation Forest (unsupervised)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    iso = IsolationForest(contamination=0.10, random_state=42, n_estimators=150)
    iso.fit(X_scaled)
    joblib.dump(iso, MODELS_DIR / "finguard_isolation_forest.pkl")
    joblib.dump(scaler, MODELS_DIR / "finguard_scaler.pkl")

    # 2. Train XGBoost Classifier (supervised)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    scale_pos = (y_train == 0).sum() / max(1, (y_train == 1).sum())
    xgb = XGBClassifier(
        n_estimators=150,
        max_depth=4,
        learning_rate=0.08,
        scale_pos_weight=scale_pos,
        random_state=42,
        eval_metric="logloss"
    )
    xgb.fit(X_train, y_train)

    y_pred = xgb.predict(X_test)
    y_proba = xgb.predict_proba(X_test)[:, 1]

    auc = roc_auc_score(y_test, y_proba)
    report = classification_report(y_test, y_pred, output_dict=True)

    joblib.dump(xgb, MODELS_DIR / "finguard_xgboost.pkl")

    feature_meta = {
        "num_features": num_features,
        "cat_features": cat_features,
        "feature_cols": feature_cols,
        "classes": [0, 1]
    }
    joblib.dump(feature_meta, MODELS_DIR / "finguard_meta.pkl")
    joblib.dump(encoders, MODELS_DIR / "finguard_encoders.pkl")

    importances = dict(zip(feature_cols, xgb.feature_importances_.tolist()))
    importances = dict(sorted(importances.items(), key=lambda x: -x[1]))

    metrics = {
        "roc_auc": round(auc, 4),
        "precision": round(report["1"]["precision"], 4),
        "recall": round(report["1"]["recall"], 4),
        "f1_score": round(report["1"]["f1-score"], 4),
        "feature_importance": importances,
    }

    with open(REPORTS_DIR / "finguard_model_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    print("=== FinGuard Model Training Complete ===")
    print(f"XGBoost ROC-AUC: {metrics['roc_auc']}, Recall: {metrics['recall']}, F1: {metrics['f1_score']}")
    print("Top features:", list(importances.items())[:5])


if __name__ == "__main__":
    main()
