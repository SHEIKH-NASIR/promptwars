"""
fraud_engine.py - FinGuard AI Hybrid Machine Learning Fraud Detection Engine
Integrates:
1. Supervised XGBoost Fraud Classifier
2. Unsupervised Isolation Forest Anomaly Detection
3. Statistical Amount Anomaly Detection (Z-score / IQR)
4. Transaction Frequency & Velocity Analysis
5. Behavioral Heuristics (Night hours, Cross-city jumps, Unusual categories)
Provides unified interfaces for single-transaction and batch inference.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import joblib
import numpy as np
import pandas as pd

MODELS_DIR = Path(__file__).resolve().parent / "models"


class FraudEngine:
    def __init__(self, models_dir: Optional[Path] = None):
        self.models_dir = models_dir or MODELS_DIR
        self.xgb_model = None
        self.iso_model = None
        self.scaler = None
        self.encoders = {}
        self.meta = {}
        self._load_models()

    def _load_models(self):
        """Loads trained FinGuard models; gracefully handles legacy if needed."""
        try:
            xgb_path = self.models_dir / "finguard_xgboost.pkl"
            iso_path = self.models_dir / "finguard_isolation_forest.pkl"
            scaler_path = self.models_dir / "finguard_scaler.pkl"
            meta_path = self.models_dir / "finguard_meta.pkl"
            enc_path = self.models_dir / "finguard_encoders.pkl"

            if xgb_path.exists():
                self.xgb_model = joblib.load(xgb_path)
            if iso_path.exists():
                self.iso_model = joblib.load(iso_path)
            if scaler_path.exists():
                self.scaler = joblib.load(scaler_path)
            if meta_path.exists():
                self.meta = joblib.load(meta_path)
            if enc_path.exists():
                self.encoders = joblib.load(enc_path)
        except Exception as e:
            print(f"[FraudEngine] Warning loading models: {e}")

    def _extract_single_features(
        self, txn: Dict[str, Any], recent_txns: Optional[List[Dict[str, Any]]] = None
    ) -> pd.DataFrame:
        """Extracts engineered features matching the FinGuard ML schema."""
        ts = txn.get("timestamp")
        if isinstance(ts, str):
            dt = pd.to_datetime(ts, format="mixed", errors="coerce")
            if pd.isna(dt):
                dt = datetime.now()
        elif isinstance(ts, datetime):
            dt = ts
        else:
            dt = datetime.now()

        amount = float(txn.get("amount", 0.0))
        hour = dt.hour
        is_night = 1 if (hour >= 22 or hour <= 5) else 0
        is_weekend = 1 if dt.weekday() >= 5 else 0

        sender_loc = str(txn.get("sender_location", ""))
        rec_loc = str(txn.get("receiver_location", ""))
        is_cross_city = 1 if (sender_loc and rec_loc and sender_loc != rec_loc) else 0
        is_high_value = 1 if amount > 100000.0 else 0

        # Velocity in last 5 minutes
        velocity = 1
        time_since_last = 99999.0
        if recent_txns:
            sender = txn.get("sender_account")
            cutoff = dt - timedelta(minutes=5)
            sender_txns = []
            for t in recent_txns:
                if t.get("sender_account") == sender:
                    t_dt = pd.to_datetime(t.get("timestamp"), format="mixed", errors="coerce")
                    if pd.notna(t_dt) and t_dt <= dt:
                        sender_txns.append(t)
            if sender_txns:
                # Count in 5 min window
                velocity = sum(
                    1 for t in sender_txns
                    if pd.notna(t_dt := pd.to_datetime(t.get("timestamp"), format="mixed", errors="coerce"))
                    and t_dt >= cutoff
                )
                # Time diff to previous
                prev_times = [
                    t_dt for t in sender_txns
                    if pd.notna(t_dt := pd.to_datetime(t.get("timestamp"), format="mixed", errors="coerce"))
                    and t_dt < dt
                ]
                if prev_times:
                    time_since_last = (dt - max(prev_times)).total_seconds()

        amount_ratio = amount / 5000.0  # Normalized to median basket benchmark

        # Categorical encodings
        txn_type = str(txn.get("transaction_type", "UPI"))
        m_cat = str(txn.get("merchant_category", "Peer-to-Peer Transfer"))

        txn_type_enc = 0
        if "transaction_type" in self.encoders:
            le = self.encoders["transaction_type"]
            txn_type_enc = le.transform([txn_type])[0] if txn_type in le.classes_ else 0

        m_cat_enc = 0
        if "merchant_category" in self.encoders:
            le = self.encoders["merchant_category"]
            m_cat_enc = le.transform([m_cat])[0] if m_cat in le.classes_ else 0

        row = {
            "amount": amount,
            "hour_of_day": hour,
            "is_night": is_night,
            "is_weekend": is_weekend,
            "is_cross_city": is_cross_city,
            "is_high_value": is_high_value,
            "velocity_sender_5m": velocity,
            "time_since_last_sender_txn": time_since_last,
            "amount_ratio": amount_ratio,
            "transaction_type_enc": txn_type_enc,
            "merchant_category_enc": m_cat_enc,
        }
        return pd.DataFrame([row])

    def detect_statistical_anomalies(
        self, txn: Dict[str, Any], baseline_amount_mean: float = 8500.0, baseline_amount_std: float = 18000.0
    ) -> Dict[str, Any]:
        """Calculates Z-score and amount ratio anomalies."""
        amt = float(txn.get("amount", 0.0))
        z_score = (amt - baseline_amount_mean) / max(baseline_amount_std, 1.0)
        is_amount_anomaly = amt > 150000.0 or z_score > 3.0

        return {
            "amount": amt,
            "z_score": round(float(z_score), 2),
            "is_anomaly": bool(is_amount_anomaly),
            "severity": "CRITICAL" if amt > 500000.0 else ("HIGH" if is_amount_anomaly else "NORMAL"),
            "reason": f"Amount ₹{amt:,.2f} is {z_score:.1f} standard deviations above baseline" if is_amount_anomaly else "Normal amount range"
        }

    def detect_velocity_anomaly(
        self, txn: Dict[str, Any], recent_txns: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Detects rapid repeated transfers within short windows."""
        sender = txn.get("sender_account")
        ts = txn.get("timestamp", datetime.now())
        dt = pd.to_datetime(ts, format="mixed", errors="coerce")
        if pd.isna(dt):
            dt = datetime.now()

        if not recent_txns or not sender:
            return {"count_5m": 1, "is_spike": False, "reason": "No recent transaction history"}

        cutoff = dt - timedelta(minutes=5)
        recent_sender = []
        for t in recent_txns:
            if t.get("sender_account") == sender:
                t_dt = pd.to_datetime(t.get("timestamp"), format="mixed", errors="coerce")
                if pd.notna(t_dt) and cutoff <= t_dt <= dt:
                    recent_sender.append(t)
        cnt = len(recent_sender)
        is_spike = cnt >= 3
        return {
            "count_5m": cnt,
            "is_spike": is_spike,
            "reason": f"High velocity: {cnt} transactions executed within 5 minutes" if is_spike else "Normal velocity"
        }

    def detect_behavioral_anomaly(self, txn: Dict[str, Any]) -> Dict[str, Any]:
        """Detects unusual hours, suspicious merchant categories, or cross-city transfers."""
        ts = txn.get("timestamp", datetime.now())
        dt = pd.to_datetime(ts, format="mixed", errors="coerce")
        if pd.isna(dt):
            dt = datetime.now()
        hour = dt.hour
        is_night = hour >= 23 or hour <= 4
        m_cat = txn.get("merchant_category", "")
        high_risk_cats = ["Cryptocurrency & Forex", "Jewelry & Luxury Goods", "Entertainment & Gaming"]
        is_high_risk_cat = m_cat in high_risk_cats

        sender_loc = txn.get("sender_location", "")
        rec_loc = txn.get("receiver_location", "")
        is_cross_city = bool(sender_loc and rec_loc and sender_loc != rec_loc)

        flags = []
        if is_night:
            flags.append(f"Odd hour transaction at {hour:02d}:00")
        if is_high_risk_cat:
            flags.append(f"High risk merchant category: {m_cat}")
        if is_cross_city and float(txn.get("amount", 0)) > 50000.0:
            flags.append(f"Cross-jurisdiction transfer ({sender_loc} -> {rec_loc}) for large amount")

        return {
            "is_night": is_night,
            "is_high_risk_cat": is_high_risk_cat,
            "is_cross_city": is_cross_city,
            "risk_flags": flags,
            "has_behavioral_flags": len(flags) > 0
        }

    def predict_transaction(
        self, txn: Dict[str, Any], recent_txns: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Full inference pipeline for a single transaction."""
        feat_df = self._extract_single_features(txn, recent_txns)
        explanations = []

        # 1. Supervised XGBoost Probability
        fraud_proba = 0.05
        if self.xgb_model and hasattr(self.xgb_model, "predict_proba"):
            try:
                cols = self.meta.get("feature_cols", feat_df.columns.tolist())
                X_input = feat_df[cols]
                fraud_proba = float(self.xgb_model.predict_proba(X_input)[0, 1])
            except Exception as e:
                fraud_proba = 0.15

        # 2. Unsupervised Isolation Forest Anomaly Score
        iso_flag = 0
        anomaly_score = 0.10
        if self.iso_model and self.scaler:
            try:
                cols = self.meta.get("feature_cols", feat_df.columns.tolist())
                X_scaled = self.scaler.transform(feat_df[cols])
                raw_decision = self.iso_model.decision_function(X_scaled)[0]
                pred = self.iso_model.predict(X_scaled)[0]  # -1 = anomaly, 1 = normal
                iso_flag = 1 if pred == -1 else 0
                # Map decision function to 0.0-1.0 risk range (lower decision = more anomalous)
                anomaly_score = float(np.clip(0.5 - raw_decision, 0.0, 1.0))
            except Exception as e:
                iso_flag = 0
                anomaly_score = 0.15

        # 3. Statistical & Velocity Rules
        stat = self.detect_statistical_anomalies(txn)
        vel = self.detect_velocity_anomaly(txn, recent_txns)
        behav = self.detect_behavioral_anomaly(txn)

        if fraud_proba >= 0.70:
            explanations.append(f"XGBoost fraud probability is high ({fraud_proba*100:.1f}%)")
        if iso_flag == 1 or anomaly_score > 0.65:
            explanations.append(f"Isolation Forest flagged structural anomaly (score: {anomaly_score*100:.1f}%)")
        if stat["is_anomaly"]:
            explanations.append(stat["reason"])
        if vel["is_spike"]:
            explanations.append(vel["reason"])
        explanations.extend(behav["risk_flags"])

        # Combined ML Risk Score bounded 0-100
        combined_score = (
            (fraud_proba * 50.0) +
            (anomaly_score * 30.0) +
            (15.0 if stat["is_anomaly"] else 0.0) +
            (10.0 if vel["is_spike"] else 0.0)
        )
        combined_score = float(np.clip(combined_score, 0.0, 100.0))

        return {
            "transaction_id": txn.get("transaction_id"),
            "fraud_probability": round(fraud_proba, 4),
            "anomaly_score": round(anomaly_score, 4),
            "is_anomaly": bool(iso_flag == 1),
            "statistical_anomaly": stat,
            "velocity_anomaly": vel,
            "behavioral_anomaly": behav,
            "ml_risk_score": round(combined_score, 2),
            "explanations": explanations if explanations else ["Normal transaction profile; no fraud signals detected"]
        }

    def predict_batch(self, df: pd.DataFrame) -> pd.DataFrame:
        """Batch inference for existing or uploaded dataframes."""
        if df.empty:
            return df

        df = df.copy()
        txns = df.to_dict(orient="records")
        results = [self.predict_transaction(t) for t in txns]

        df["fraud_probability"] = [r["fraud_probability"] for r in results]
        df["anomaly_score"] = [r["anomaly_score"] for r in results]
        df["is_anomaly"] = [r["is_anomaly"] for r in results]
        df["ml_risk_score"] = [r["ml_risk_score"] for r in results]
        df["ml_explanations"] = ["; ".join(r["explanations"]) for r in results]
        return df


if __name__ == "__main__":
    engine = FraudEngine()
    test_txn = {
        "transaction_id": "TXN-TEST-1",
        "sender_account": "HDFC1234567890",
        "receiver_account": "SBIN0987654321",
        "amount": 950000.0,
        "timestamp": datetime.now().isoformat(),
        "transaction_type": "RTGS",
        "merchant_category": "Jewelry & Luxury Goods",
        "sender_location": "Mumbai",
        "receiver_location": "Delhi",
        "device_id": "DEV-111111"
    }
    res = engine.predict_transaction(test_txn)
    print("Test inference result:")
    print(res)
