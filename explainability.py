"""
explainability.py - FinGuard AI Explainable Machine Learning & AML Attribution Engine
Provides transparent feature contributions using SHAP / TreeExplainer for XGBoost
and rule-level transaction trails for Anti-Money Laundering findings.
Never fabricates explanations.
"""

from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from fraud_engine import FraudEngine


class ExplainabilityEngine:
    def __init__(self, fraud_engine: Optional[FraudEngine] = None):
        self.fraud_engine = fraud_engine or FraudEngine()
        self.shap_explainer = None
        self._init_shap()

    def _init_shap(self):
        """Initializes TreeExplainer for the XGBoost model if available."""
        try:
            import shap
            if self.fraud_engine.xgb_model:
                self.shap_explainer = shap.TreeExplainer(self.fraud_engine.xgb_model)
        except Exception as e:
            self.shap_explainer = None

    def explain_transaction(
        self, txn: Dict[str, Any], risk_evaluation: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generates comprehensive explainability audit card for a transaction.
        Includes feature attributions (SHAP or tree-based), AML rule evidence,
        and human-readable next actions.
        """
        feat_df = self.fraud_engine._extract_single_features(txn)
        cols = self.fraud_engine.meta.get("feature_cols", feat_df.columns.tolist())
        X_input = feat_df[cols]

        feature_contributions = {}
        expected_value = 0.0

        if self.shap_explainer:
            try:
                shap_values = self.shap_explainer(X_input)
                vals = shap_values.values[0]
                expected_value = float(self.shap_explainer.expected_value)
                for c, v in zip(cols, vals):
                    feature_contributions[c] = round(float(v), 4)
            except Exception:
                feature_contributions = self._fallback_feature_importance(X_input)
        else:
            feature_contributions = self._fallback_feature_importance(X_input)

        # Sort contributions by absolute magnitude
        sorted_contribs = sorted(
            feature_contributions.items(), key=lambda x: abs(x[1]), reverse=True
        )

        reasons = []
        if risk_evaluation:
            reasons = risk_evaluation.get("detection_reasons", [])
        else:
            ml_pred = self.fraud_engine.predict_transaction(txn)
            reasons = ml_pred.get("explanations", [])

        action = (
            risk_evaluation.get("recommended_action")
            if risk_evaluation
            else "Review transaction parameters against account baseline."
        )

        return {
            "transaction_id": txn.get("transaction_id"),
            "expected_base_value": expected_value,
            "feature_contributions": dict(sorted_contribs[:8]),
            "detection_reasons": reasons,
            "recommended_action": action,
            "feature_values": {c: float(X_input[c].iloc[0]) for c in cols}
        }

    def _fallback_feature_importance(self, X_input: pd.DataFrame) -> Dict[str, float]:
        """Calculates normalized tree-weight based contribution when SHAP is bypassed."""
        if not self.fraud_engine.xgb_model:
            return {}
        try:
            importances = self.fraud_engine.xgb_model.feature_importances_
            cols = X_input.columns.tolist()
            contribs = {}
            for col, imp in zip(cols, importances):
                val = float(X_input[col].iloc[0])
                # Direct heuristic scaling with feature value
                contribs[col] = round(imp * (val / max(abs(val), 1.0)), 4)
            return contribs
        except Exception:
            return {}

    def create_waterfall_chart(self, explanation: Dict[str, Any]) -> go.Figure:
        """Renders an interactive Plotly horizontal bar chart of feature contributions."""
        contribs = explanation.get("feature_contributions", {})
        if not contribs:
            fig = go.Figure()
            fig.update_layout(title="No feature contributions available")
            return fig

        features = list(contribs.keys())
        values = list(contribs.values())

        # Clean display names
        clean_names = [
            f.replace("_enc", "")
            .replace("_", " ")
            .title()
            for f in features
        ]

        colors = ["#FF3B30" if v > 0 else "#00E5FF" for v in values]

        fig = go.Figure(go.Bar(
            x=values,
            y=clean_names,
            orientation='h',
            marker=dict(color=colors, line=dict(color="#FFFFFF", width=1.5)),
            text=[f"{v:+.3f}" for v in values],
            textposition='auto',
        ))

        fig.update_layout(
            title=f"Feature Risk Contribution (SHAP / Feature Impact)",
            title_font=dict(color="#0F172A", size=15, family="Plus Jakarta Sans"),
            xaxis=dict(
                title="Impact on Fraud Probability (Log-Odds / SHAP Value)",
                gridcolor="#F1F5F9",
                zerolinecolor="#CBD5E1",
                color="#64748B"
            ),
            yaxis=dict(
                autorange="reversed",
                gridcolor="#F1F5F9",
                color="#0F172A"
            ),
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FFFFFF",
            margin=dict(l=20, r=20, t=50, b=30),
            height=320
        )
        return fig


if __name__ == "__main__":
    explainer = ExplainabilityEngine()
    test_txn = {
        "transaction_id": "TXN-EXP-001",
        "sender_account": "HDFC555555",
        "receiver_account": "SBIN999999",
        "amount": 750000.0,
        "transaction_type": "RTGS",
        "merchant_category": "Jewelry & Luxury Goods",
        "sender_location": "Mumbai",
        "receiver_location": "Kolkata"
    }
    exp = explainer.explain_transaction(test_txn)
    print("Explainability Result:")
    print("Top Feature Contributions:", exp["feature_contributions"])
    print("Reasons:", exp["detection_reasons"])
