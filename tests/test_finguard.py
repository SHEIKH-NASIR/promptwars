"""
tests/test_finguard.py - FinGuard AI Automated Verification & Quality Assurance Suite
Validates all 11+ operational requirements:
1. Normal transaction
2. Abnormally large transaction
3. Repeated rapid transactions
4. Structuring detection
5. Mule account detection
6. Circular transfers
7. Normal account activity
8. Risk score bounds & categorization
9. CSV upload audit
10. Database insertion & KPI queries
11. Live streaming simulation
12. Explainability & SHAP feature attributions
"""

import unittest
import sys
from pathlib import Path
from datetime import datetime, timedelta

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
import numpy as np

import database
from generator import TransactionGenerator
from fraud_engine import FraudEngine
from aml_engine import AMLEngine
from risk_engine import RiskEngine
from explainability import ExplainabilityEngine
from simulation import TransactionStreamSimulator

TEST_DB_PATH = ROOT_DIR / "data" / "test_finguard.db"


class TestFinGuardAI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        database.init_database(db_path=TEST_DB_PATH)
        cls.generator = TransactionGenerator(seed=999)
        cls.fraud_engine = FraudEngine()
        cls.aml_engine = AMLEngine()
        cls.risk_engine = RiskEngine()
        cls.explain_engine = ExplainabilityEngine(fraud_engine=cls.fraud_engine)
        cls.stream_sim = TransactionStreamSimulator(seed=999)

    @classmethod
    def tearDownClass(cls):
        if TEST_DB_PATH.exists():
            try:
                TEST_DB_PATH.unlink()
            except Exception:
                pass

    # 1. Normal Transaction Test
    def test_01_normal_transaction(self):
        now = datetime.now()
        txn = self.generator.generate_normal_transaction(now)
        ml_pred = self.fraud_engine.predict_transaction(txn)
        risk_eval = self.risk_engine.evaluate_transaction(txn, ml_pred)

        self.assertLess(risk_eval["risk_score"], 50.0, "Normal transaction should not receive high risk")
        self.assertIn(risk_eval["risk_category"], ["LOW", "MEDIUM"])
        self.assertFalse(ml_pred["statistical_anomaly"]["is_anomaly"])

    # 2. Abnormally Large Transaction Test
    def test_02_abnormally_large_transaction(self):
        now = datetime.now()
        spike = self.generator.generate_high_value_spike(now)[0]
        ml_pred = self.fraud_engine.predict_transaction(spike)
        risk_eval = self.risk_engine.evaluate_transaction(spike, ml_pred)

        self.assertGreaterEqual(risk_eval["risk_score"], 65.0, "High value spike must receive high/critical score")
        self.assertIn(risk_eval["risk_category"], ["HIGH", "CRITICAL"])
        self.assertTrue(ml_pred["statistical_anomaly"]["is_anomaly"])

    # 3. Repeated Rapid Transactions (Velocity Burst) Test
    def test_03_repeated_rapid_transactions(self):
        now = datetime.now()
        burst = self.generator.generate_rapid_velocity_burst(now)
        # Pass prior burst items as recent history
        last_txn = burst[-1]
        vel = self.fraud_engine.detect_velocity_anomaly(last_txn, recent_txns=burst)

        self.assertTrue(vel["is_spike"], "Velocity burst must trigger velocity spike flag")
        self.assertGreaterEqual(vel["count_5m"], 3)

    # 4. Structuring Detection Test
    def test_04_structuring_detection(self):
        now = datetime.now()
        struc_txns = self.generator.generate_structuring_scenario(now)
        df_struc = pd.DataFrame(struc_txns)
        cases = self.aml_engine.detect_structuring(df_struc)

        self.assertGreaterEqual(len(cases), 1, "AML engine must detect structuring scenario")
        self.assertEqual(cases[0]["case_type"], "STRUCTURING")
        self.assertIn("smurfing", cases[0]["evidence_summary"].lower())

    # 5. Mule Account Detection Test
    def test_05_mule_account_detection(self):
        now = datetime.now()
        mule_txns = self.generator.generate_mule_account_scenario(now)
        df_mule = pd.DataFrame(mule_txns)
        cases = self.aml_engine.detect_mule_accounts(df_mule)

        self.assertGreaterEqual(len(cases), 1, "AML engine must detect mule pass-through behavior")
        self.assertEqual(cases[0]["case_type"], "MULE_ACCOUNT")
        self.assertIn("pass-through", cases[0]["evidence_summary"].lower())

    # 6. Circular Transfers (Loops) Test
    def test_06_circular_transfers_detection(self):
        now = datetime.now()
        circ_txns = self.generator.generate_circular_movement_scenario(now)
        df_circ = pd.DataFrame(circ_txns)
        cases = self.aml_engine.detect_circular_money_movement(df_circ)

        self.assertGreaterEqual(len(cases), 1, "AML engine must detect directed circular cycles")
        self.assertEqual(cases[0]["case_type"], "CIRCULAR_TRANSFERS")
        self.assertEqual(cases[0]["severity"], "CRITICAL")

    # 7. Normal Account Activity Test
    def test_07_normal_account_activity(self):
        now = datetime.now()
        normal_txns = [self.generator.generate_normal_transaction(now + timedelta(hours=i*6)) for i in range(5)]
        df_norm = pd.DataFrame(normal_txns)
        res = self.aml_engine.run_all_checks(df_norm)

        self.assertEqual(len(res["circular_cases"]), 0, "Normal activity should have no circular cases")
        self.assertEqual(len(res["mule_cases"]), 0, "Normal activity should have no mule cases")

    # 8. Risk Score Calculation & Categorization Test
    def test_08_risk_score_bounds_and_categorization(self):
        test_scores = [-10.0, 0.0, 15.5, 25.0, 49.9, 50.0, 74.9, 75.0, 99.9, 150.0]
        for s in test_scores:
            cat = self.risk_engine.categorize_risk(s)
            self.assertIn(cat, ["LOW", "MEDIUM", "HIGH", "CRITICAL"])

        # Extreme synthetic transaction
        extreme_txn = {"transaction_id": "TXN-EXTREME", "amount": 99999999.0}
        ml_pred = {"fraud_probability": 1.0, "anomaly_score": 1.0}
        aml_tags = {"is_circular": True, "is_mule": True}
        res = self.risk_engine.evaluate_transaction(extreme_txn, ml_pred, aml_tags)

        self.assertLessEqual(res["risk_score"], 100.0, "Risk score must never exceed 100.0")
        self.assertGreaterEqual(res["risk_score"], 0.0, "Risk score must be non-negative")
        self.assertEqual(res["risk_category"], "CRITICAL")

    # 9. CSV Batch Audit Test (Indian Banking Multi-Rail Format with Column Normalization)
    def test_09_csv_batch_audit(self):
        batch = [self.generator.generate_normal_transaction(datetime.now()) for _ in range(10)]
        df_raw = pd.DataFrame(batch)
        # Test casing variation and whitespace in column names
        df_raw.rename(columns={
            "amount": " Amount ",
            "sender_account": "Sender_Account",
            "receiver_account": "RECEIVER_ACCOUNT",
            "timestamp": " Timestamp "
        }, inplace=True)
        scored_df = self.risk_engine.score_dataframe(df_raw, self.fraud_engine, self.aml_engine)

        self.assertEqual(len(scored_df), 10)
        self.assertIn("amount", scored_df.columns)
        self.assertIn("risk_score", scored_df.columns)
        self.assertIn("risk_category", scored_df.columns)
        self.assertIn("detection_reasons", scored_df.columns)
        self.assertIn("recommended_action", scored_df.columns)

    # 10. Database Insertion & Query Test
    def test_10_database_crud(self):
        txn = self.generator.generate_normal_transaction(datetime.now())
        txn["risk_score"] = 12.0
        txn["risk_category"] = "LOW"

        # Insert single
        ok = database.insert_transaction(txn, db_path=TEST_DB_PATH)
        self.assertTrue(ok)

        # Insert alert
        alert = {
            "transaction_id": txn["transaction_id"],
            "risk_score": 85.0,
            "risk_category": "CRITICAL",
            "primary_reason": "Automated unit test alert",
            "evidence": {"test": True},
            "recommended_action": "Verify in test suite"
        }
        ok_alert = database.insert_fraud_alert(alert, db_path=TEST_DB_PATH)
        self.assertTrue(ok_alert)

        # Query
        df = database.fetch_transactions_df(db_path=TEST_DB_PATH)
        self.assertGreaterEqual(len(df), 1)

        alerts = database.fetch_fraud_alerts(db_path=TEST_DB_PATH)
        self.assertGreaterEqual(len(alerts), 1)

        kpis = database.fetch_kpis(db_path=TEST_DB_PATH)
        self.assertGreaterEqual(kpis["total_transactions"], 1)
        self.assertIn("fraud_alerts_pending", kpis)
        self.assertIn("aml_structuring_count", kpis)
        self.assertIn("high_risk_accounts_count", kpis)
        self.assertIn("high_risk_exposure_formula", kpis)

        crit_alerts = database.fetch_recent_critical_alerts(limit=5, db_path=TEST_DB_PATH)
        self.assertGreaterEqual(len(crit_alerts), 1)
        self.assertEqual(crit_alerts[0]["transaction_id"], txn["transaction_id"])

    # 11. Live Stream Simulation Test
    def test_11_streaming_simulation(self):
        txns = self.stream_sim.get_next_transaction_batch(count=3)
        self.assertEqual(len(txns), 3)

        processed = self.stream_sim.process_and_persist(
            txns, self.fraud_engine, self.aml_engine, self.risk_engine, db_path=TEST_DB_PATH
        )
        self.assertEqual(len(processed), 3)
        self.assertIn("risk_score", processed[0])

    # 12. Explainability & SHAP Feature Attributions Test
    def test_12_explainability(self):
        txn = self.generator.generate_normal_transaction(datetime.now())
        exp = self.explain_engine.explain_transaction(txn)

        self.assertIn("feature_contributions", exp)
        self.assertIn("detection_reasons", exp)
        self.assertIn("recommended_action", exp)
        self.assertGreater(len(exp["feature_contributions"]), 0)

    # 13. Network Graph Cycle Detection Consistency Test (A -> B -> C -> A)
    def test_13_network_cycle_consistency(self):
        import networkx as nx
        # Small synthetic cycle: A -> B -> C -> A
        G = nx.DiGraph()
        G.add_edge("ACC_A", "ACC_B", amount=50000, transaction_id="TXN-1")
        G.add_edge("ACC_B", "ACC_C", amount=49000, transaction_id="TXN-2")
        G.add_edge("ACC_C", "ACC_A", amount=48000, transaction_id="TXN-3")
        # Non-cycle external connections
        G.add_edge("ACC_EXTERNAL", "ACC_A", amount=100000, transaction_id="TXN-4")
        G.add_edge("ACC_C", "ACC_SINK", amount=5000, transaction_id="TXN-5")

        candidate_nodes = {n for n in G.nodes() if G.in_degree(n) > 0 and G.out_degree(n) > 0}
        H = G.subgraph(candidate_nodes)
        cycles = [cyc for cyc in nx.simple_cycles(H) if 2 <= len(cyc) <= 6]

        self.assertEqual(len(cycles), 1, "Exactly one A -> B -> C -> A cycle should be detected")
        self.assertEqual(set(cycles[0]), {"ACC_A", "ACC_B", "ACC_C"})

        cycle_edges = set()
        cycle_nodes = set()
        for cyc in cycles:
            for i in range(len(cyc)):
                cycle_edges.add((cyc[i], cyc[(i + 1) % len(cyc)]))
                cycle_nodes.add(cyc[i])

        # Verify only cycle edges are marked
        self.assertIn(("ACC_A", "ACC_B"), cycle_edges)
        self.assertIn(("ACC_B", "ACC_C"), cycle_edges)
        self.assertIn(("ACC_C", "ACC_A"), cycle_edges)
        self.assertNotIn(("ACC_EXTERNAL", "ACC_A"), cycle_edges)
        self.assertNotIn(("ACC_C", "ACC_SINK"), cycle_edges)

        # Verify only cycle nodes are marked
        self.assertIn("ACC_A", cycle_nodes)
        self.assertIn("ACC_B", cycle_nodes)
        self.assertIn("ACC_C", cycle_nodes)
        self.assertNotIn("ACC_EXTERNAL", cycle_nodes)
        self.assertNotIn("ACC_SINK", cycle_nodes)

    # 14. Timestamp Parsing Robustness (ISO8601, Space-Separated, Missing, Corrupted)
    def test_14_timestamp_parsing_robustness(self):
        sample_timestamps = [
            "2026-11-13T12:12:51.372787",
            "2026-11-13 12:12:51.372787",
            "2026-11-13T12:12:51",
            "2026-11-13 12:12:51",
            "invalid_date_xyz",
            None,
            ""
        ]
        df = pd.DataFrame({
            "timestamp": sample_timestamps,
            "transaction_id": [f"TX-{i}" for i in range(len(sample_timestamps))],
            "risk_category": ["LOW", "HIGH", "CRITICAL", "LOW", "MEDIUM", "HIGH", "LOW"]
        })

        df["dt"] = pd.to_datetime(df["timestamp"], format="mixed", errors="coerce")
        # Ensure 4 valid dates parsed
        valid_mask = df["dt"].notna()
        self.assertEqual(valid_mask.sum(), 4)

        # Ensure NaT for invalid/missing
        self.assertTrue(pd.isna(df.loc[4, "dt"]))
        self.assertTrue(pd.isna(df.loc[5, "dt"]))
        self.assertTrue(pd.isna(df.loc[6, "dt"]))

        # Ensure timeline resample executes safely without exception
        df_timeline = df[valid_mask]
        hourly = df_timeline.set_index("dt").resample("6h").agg(
            total_count=("transaction_id", "count"),
            high_risk_count=("risk_category", lambda s: (s.isin(["HIGH", "CRITICAL"])).sum())
        ).reset_index()

        self.assertGreaterEqual(len(hourly), 1)
        self.assertEqual(hourly["total_count"].sum(), 4)

    # 15. ULB Credit Card Fraud Dataset Forensic Scoring Test
    def test_15_ulb_credit_card_csv_audit(self):
        # Create synthetic ULB dataset structure: Time, V1-V28, Amount, Class
        np.random.seed(42)
        n = 30
        ulb_data = {
            "Time": np.random.uniform(0, 172800, n),
            "Amount": np.random.uniform(10, 800, n),
            "Class": [0] * 27 + [1] * 3  # 27 genuine, 3 known fraud
        }
        for i in range(1, 29):
            ulb_data[f"V{i}"] = np.random.normal(0, 1, n)

        # Inject extreme PCA deflections on key fraud components for Class 1 records
        ulb_data["V14"][27] = -9.2
        ulb_data["V17"][27] = -8.1
        ulb_data["V14"][28] = -11.5
        ulb_data["V17"][28] = -9.8
        ulb_data["V14"][29] = -8.7
        ulb_data["V17"][29] = -7.6
        ulb_data["Amount"][27] = 2450.0

        df_ulb = pd.DataFrame(ulb_data)

        # Verify scoring completes without KeyError: 'timestamp' or missing sender/receiver errors
        scored = self.risk_engine.score_dataframe(df_ulb, self.fraud_engine, self.aml_engine)

        self.assertEqual(len(scored), 30)
        self.assertIn("risk_score", scored.columns)
        self.assertIn("risk_category", scored.columns)
        self.assertIn("detection_reasons", scored.columns)
        self.assertIn("recommended_action", scored.columns)
        self.assertIn("elapsed_seconds", scored.columns)

        # Elapsed time preserved as relative seconds (no invented calendar timestamp)
        self.assertTrue(pd.api.types.is_numeric_dtype(scored["elapsed_seconds"]))

        # Known fraud records (Class 1) must be escalated to CRITICAL
        fraud_records = scored[scored["class"] == 1]
        self.assertEqual(len(fraud_records), 3)
        for _, r in fraud_records.iterrows():
            self.assertGreaterEqual(r["risk_score"], 75.0, "Class=1 records must receive CRITICAL score")
            self.assertEqual(r["risk_category"], "CRITICAL")
            self.assertIn("Confirmed Fraud Pattern", r["detection_reasons"])

        # Genuine records (Class 0) should have low/medium risk
        genuine_records = scored[scored["class"] == 0]
        self.assertLess(genuine_records["risk_score"].mean(), 40.0)

    # 16. Complete End-to-End 100-Row ULB Upload, Ingestion, Profiling, Scoring & Downstream Rendering Test
    def test_16_complete_ulb_100_workflow_and_rendering(self):
        # 1. Synthesize 100-row ULB Credit Card dataset (matching user scenario: 100 genuine, 0 fraud)
        np.random.seed(42)
        n = 100
        raw_dict = {
            "Time": np.sort(np.random.uniform(0, 172800, n)),
            "Amount": np.random.uniform(5.0, 450.0, n),
            "Class": [0] * n  # 100 genuine, 0 fraud
        }
        for i in range(1, 29):
            raw_dict[f"V{i}"] = np.random.normal(0, 1, n)

        df_upload = pd.DataFrame(raw_dict)

        # 2. Simulate complete dashboard ingestion & column normalization
        df_upload.columns = [str(c).strip().lower() for c in df_upload.columns]

        if "amount" not in df_upload.columns:
            for alias in ["amt", "trans_amount", "transaction_amount", "val", "value"]:
                if alias in df_upload.columns:
                    df_upload.rename(columns={alias: "amount"}, inplace=True)
                    break

        if "class" not in df_upload.columns:
            for alias in ["label", "target", "is_fraud", "fraud"]:
                if alias in df_upload.columns:
                    df_upload.rename(columns={alias: "class"}, inplace=True)
                    break

        if "time" not in df_upload.columns:
            for alias in ["elapsed_time", "seconds", "step"]:
                if alias in df_upload.columns:
                    df_upload.rename(columns={alias: "time"}, inplace=True)
                    break

        # Profiling
        pca_cols = [f"v{i}" for i in range(1, 29) if f"v{i}" in df_upload.columns]
        is_ulb = (
            len(pca_cols) >= 5
            or ("class" in df_upload.columns and len(pca_cols) >= 1)
            or ("time" in df_upload.columns and "sender_account" not in df_upload.columns)
        )
        self.assertTrue(is_ulb, "ULB dataset profile must be detected")
        self.assertEqual(len(df_upload), 100)
        self.assertEqual(int((df_upload["class"] == 0).sum()), 100)
        self.assertEqual(int((df_upload["class"] == 1).sum()), 0)

        # 3. Complete Forensic Scoring Execution
        scored_df = self.risk_engine.score_dataframe(df_upload, self.fraud_engine, self.aml_engine)
        self.assertEqual(len(scored_df), 100)

        # 4. Downstream Result Rendering Preparation (Metrics, DataFrame Slicing, CSV Export)
        crit_count = int((scored_df["risk_category"] == "CRITICAL").sum())
        high_count = int((scored_df["risk_category"] == "HIGH").sum())
        med_count = int((scored_df["risk_category"] == "MEDIUM").sum())
        low_count = int((scored_df["risk_category"] == "LOW").sum())
        self.assertEqual(crit_count + high_count + med_count + low_count, 100)

        disp_cols = [
            c for c in ["transaction_id", "time", "elapsed_seconds", "amount", "class", "risk_score", "risk_category", "detection_reasons", "recommended_action"]
            if c in scored_df.columns
        ]
        rendered_head = scored_df[disp_cols].head(100)
        self.assertEqual(len(rendered_head), 100)
        self.assertIn("elapsed_seconds", rendered_head.columns)

        # 5. Downstream CSV Export Serialization
        csv_bytes = scored_df.to_csv(index=False).encode("utf-8")
        self.assertGreater(len(csv_bytes), 1000)


if __name__ == "__main__":
    unittest.main(verbosity=2)
