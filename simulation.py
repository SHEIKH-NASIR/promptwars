"""
simulation.py - FinGuard AI Simulated Real-Time Transaction Streaming & Monitoring
Generates realistic live financial transaction stream, runs real-time inference,
and logs alerts to SQLite.
Clearly labeled: SIMULATED REAL-TIME MONITORING.
"""

import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import pandas as pd
from generator import TransactionGenerator
from fraud_engine import FraudEngine
from aml_engine import AMLEngine
from risk_engine import RiskEngine
import database


class TransactionStreamSimulator:
    def __init__(self, seed: int = 101):
        self.generator = TransactionGenerator(seed=seed)
        self.scenario_cycle = [
            "NORMAL", "NORMAL", "NORMAL", "NORMAL", "HIGH_VALUE",
            "NORMAL", "NORMAL", "VELOCITY_BURST", "NORMAL", "STRUCTURING",
            "NORMAL", "NORMAL", "MULE_TRANSFER", "NORMAL", "CIRCULAR_STEP"
        ]
        self.cycle_index = 0
        self.cached_history = []

    def get_next_transaction_batch(self, count: int = 1) -> List[Dict[str, Any]]:
        """Produces next simulated transactions with periodic controlled patterns."""
        now = datetime.now()
        batch = []

        for _ in range(count):
            scenario = self.scenario_cycle[self.cycle_index % len(self.scenario_cycle)]
            self.cycle_index += 1

            if scenario == "NORMAL":
                t = self.generator.generate_normal_transaction(now)
                batch.append(t)
            elif scenario == "HIGH_VALUE":
                batch.extend(self.generator.generate_high_value_spike(now))
            elif scenario == "VELOCITY_BURST":
                burst = self.generator.generate_rapid_velocity_burst(now)
                batch.extend(burst[:2])  # Stream first 2 of the burst
            elif scenario == "STRUCTURING":
                struc = self.generator.generate_structuring_scenario(now)
                batch.extend(struc[:2])
            elif scenario == "MULE_TRANSFER":
                mule = self.generator.generate_mule_account_scenario(now)
                batch.extend(mule[:2])
            elif scenario == "CIRCULAR_STEP":
                circ = self.generator.generate_circular_movement_scenario(now)
                batch.extend(circ[:1])

        return batch

    def process_and_persist(
        self,
        txns: List[Dict[str, Any]],
        fraud_engine: FraudEngine,
        aml_engine: AMLEngine,
        risk_engine: RiskEngine,
        db_path: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Runs fraud + aml + risk engine on incoming simulated transactions
        and records them into SQLite.
        """
        processed = []
        for txn in txns:
            self.cached_history.append(txn)
            if len(self.cached_history) > 200:
                self.cached_history.pop(0)

            # 1. ML Detection
            ml_pred = fraud_engine.predict_transaction(txn, recent_txns=self.cached_history)

            # 2. AML Quick Check against cached recent history
            recent_df = pd.DataFrame(self.cached_history)
            aml_results = aml_engine.run_all_checks(recent_df)
            struct_ids = set(t for c in aml_results["structuring_cases"] for t in c["related_txns"])
            mule_ids = set(t for c in aml_results["mule_cases"] for t in c["related_txns"])
            circ_ids = set(t for c in aml_results["circular_cases"] for t in c["related_txns"])
            rapid_ids = set(t for c in aml_results["rapid_movement_cases"] for t in c["related_txns"])

            txn_id = txn["transaction_id"]
            aml_tags = {
                "is_structuring": txn_id in struct_ids,
                "is_mule": txn_id in mule_ids,
                "is_circular": txn_id in circ_ids,
                "is_rapid_movement": txn_id in rapid_ids
            }

            # 3. Composite Risk Evaluation
            risk_eval = risk_engine.evaluate_transaction(txn, ml_pred, aml_tags)

            # Enrich record
            txn_record = dict(txn)
            txn_record["risk_score"] = risk_eval["risk_score"]
            txn_record["risk_category"] = risk_eval["risk_category"]
            txn_record["detection_reasons"] = risk_eval["detection_reasons"]
            txn_record["recommended_action"] = risk_eval["recommended_action"]
            txn_record["fraud_probability"] = ml_pred["fraud_probability"]
            txn_record["anomaly_score"] = ml_pred["anomaly_score"]

            # Save to Database
            database.insert_transaction(txn_record, db_path=db_path)

            # If High or Critical, generate alert
            if risk_eval["risk_score"] >= 50.0:
                alert = {
                    "transaction_id": txn_id,
                    "risk_score": risk_eval["risk_score"],
                    "risk_category": risk_eval["risk_category"],
                    "primary_reason": "; ".join(risk_eval["detection_reasons"][:2]),
                    "evidence": risk_eval["supporting_evidence"],
                    "recommended_action": risk_eval["recommended_action"],
                    "status": "OPEN",
                    "assigned_to": "Fraud Ops Queue"
                }
                database.insert_fraud_alert(alert, db_path=db_path)

            # Update suspicious account
            sender = txn["sender_account"]
            database.update_suspicious_account({
                "account_id": sender,
                "outgoing_count": 1,
                "total_outgoing_amount": txn["amount"],
                "risk_score": risk_eval["risk_score"],
                "risk_level": risk_eval["risk_category"],
                "suspicious_patterns": risk_eval["detection_reasons"]
            }, db_path=db_path)

            processed.append(txn_record)

        return processed
