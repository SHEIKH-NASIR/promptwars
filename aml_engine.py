"""
aml_engine.py - FinGuard AI Anti-Money Laundering (AML) Intelligence Engine
Implements specialized financial crime topology detection:
1. Structuring Detection (Smurfing below regulatory threshold)
2. Mule Account Detection (Aggregation & rapid pass-through dispersion)
3. Rapid Fund Movement (High-velocity in-to-out fund forwarding)
4. Circular Money Movement (Directed graph cycles using NetworkX)
5. Suspicious Network Analysis (Hubs, high degree centrality, transfer chains)
Objective evidence-based alerts with full transaction trails.
"""

from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
import networkx as nx
import pandas as pd
import numpy as np


class AMLEngine:
    def __init__(
        self,
        structuring_threshold: float = 50000.0,
        structuring_window_hours: float = 24.0,
        structuring_min_txns: int = 3,
        rapid_fund_window_minutes: float = 30.0,
        mule_inflow_min_accounts: int = 3,
        mule_outflow_ratio: float = 0.85
    ):
        self.structuring_threshold = structuring_threshold
        self.structuring_window_hours = structuring_window_hours
        self.structuring_min_txns = structuring_min_txns
        self.rapid_fund_window_minutes = rapid_fund_window_minutes
        self.mule_inflow_min_accounts = mule_inflow_min_accounts
        self.mule_outflow_ratio = mule_outflow_ratio

    def _prepare_df(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        if "timestamp" not in df.columns:
            df["timestamp"] = pd.Timestamp.now()
        else:
            df["timestamp"] = pd.to_datetime(df["timestamp"], format="mixed", errors="coerce").fillna(pd.Timestamp.now())
        return df.sort_values("timestamp").reset_index(drop=True)

    # -------------------------------------------------------------------------
    # A. STRUCTURING DETECTION
    # -------------------------------------------------------------------------
    def detect_structuring(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Identifies repeated smaller transfers from an account within a time window
        where individual amounts sit just below the regulatory threshold (e.g. ₹50,000).
        """
        if df.empty or "sender_account" not in df.columns or "receiver_account" not in df.columns or "amount" not in df.columns:
            return []
        df = self._prepare_df(df)
        cases = []

        # Filter transactions just below threshold (e.g. 50% to 99.8% of threshold)
        lower_bound = self.structuring_threshold * 0.40
        upper_bound = self.structuring_threshold * 0.999

        sub_df = df[(df["amount"] >= lower_bound) & (df["amount"] <= upper_bound)]
        grouped = sub_df.groupby("sender_account")

        window_delta = timedelta(hours=self.structuring_window_hours)

        case_idx = 1
        for sender, group in grouped:
            if len(group) < self.structuring_min_txns:
                continue

            records = group.to_dict(orient="records")
            # Rolling window search
            n = len(records)
            for i in range(n):
                window_txns = [records[i]]
                start_t = records[i]["timestamp"]
                for j in range(i + 1, n):
                    if records[j]["timestamp"] - start_t <= window_delta:
                        window_txns.append(records[j])
                    else:
                        break

                if len(window_txns) >= self.structuring_min_txns:
                    tot_amt = sum(t["amount"] for t in window_txns)
                    time_span_min = (window_txns[-1]["timestamp"] - window_txns[0]["timestamp"]).total_seconds() / 60.0
                    txn_ids = [t["transaction_id"] for t in window_txns]

                    cases.append({
                        "case_id": f"AML-STRUC-{case_idx:04d}",
                        "case_type": "STRUCTURING",
                        "primary_account": sender,
                        "involved_accounts": list(set([t["receiver_account"] for t in window_txns])),
                        "total_amount": round(tot_amt, 2),
                        "transaction_count": len(window_txns),
                        "time_span_minutes": round(time_span_min, 1),
                        "evidence_summary": (
                            f"Account executed {len(window_txns)} transfers between ₹{lower_bound:,.0f} and "
                            f"₹{upper_bound:,.0f} totaling ₹{tot_amt:,.2f} within {time_span_min:.0f} minutes, "
                            f"exhibiting potential smurfing under the ₹{self.structuring_threshold:,.0f} threshold."
                        ),
                        "related_txns": txn_ids,
                        "severity": "CRITICAL" if tot_amt >= 200000.0 else "HIGH",
                        "status": "ACTIVE"
                    })
                    case_idx += 1
                    break  # Record one primary case per sender window

        return cases

    # -------------------------------------------------------------------------
    # B. MULE ACCOUNT DETECTION
    # -------------------------------------------------------------------------
    def detect_mule_accounts(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Identifies accounts that receive funds from multiple distinct sources
        and rapidly transfer the majority of funds out to external accounts.
        """
        if df.empty or "sender_account" not in df.columns or "receiver_account" not in df.columns or "amount" not in df.columns:
            return []
        df = self._prepare_df(df)
        cases = []

        all_accounts = set(df["sender_account"]).union(set(df["receiver_account"]))
        case_idx = 1

        for acc in all_accounts:
            inflows = df[df["receiver_account"] == acc]
            outflows = df[df["sender_account"] == acc]

            unique_senders = inflows["sender_account"].nunique()
            unique_receivers = outflows["receiver_account"].nunique()

            if unique_senders >= self.mule_inflow_min_accounts and len(outflows) >= 1:
                total_in = inflows["amount"].sum()
                total_out = outflows["amount"].sum()

                # High pass-through ratio
                if total_in > 0:
                    flow_ratio = total_out / total_in
                    if flow_ratio >= self.mule_outflow_ratio or (total_out > 50000.0 and unique_senders >= 3):
                        related = inflows["transaction_id"].tolist() + outflows["transaction_id"].tolist()
                        earliest_in = inflows["timestamp"].min()
                        latest_out = outflows["timestamp"].max()
                        time_span = (latest_out - earliest_in).total_seconds() / 60.0 if pd.notna(earliest_in) and pd.notna(latest_out) else 0

                        cases.append({
                            "case_id": f"AML-MULE-{case_idx:04d}",
                            "case_type": "MULE_ACCOUNT",
                            "primary_account": acc,
                            "involved_accounts": list(set(inflows["sender_account"]).union(set(outflows["receiver_account"])))[:10],
                            "total_amount": round(float(total_in), 2),
                            "transaction_count": len(inflows) + len(outflows),
                            "time_span_minutes": round(float(time_span), 1),
                            "evidence_summary": (
                                f"Account received ₹{total_in:,.2f} from {unique_senders} unique sources "
                                f"and disbursed ₹{total_out:,.2f} ({flow_ratio*100:.1f}% pass-through) to "
                                f"{unique_receivers} destinations, acting as an intermediary node."
                            ),
                            "related_txns": related[:15],
                            "severity": "CRITICAL" if total_in > 250000.0 else "HIGH",
                            "status": "ACTIVE"
                        })
                        case_idx += 1

        return cases

    # -------------------------------------------------------------------------
    # C. RAPID FUND MOVEMENT
    # -------------------------------------------------------------------------
    def detect_rapid_fund_movement(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Detects incoming funds followed by rapid outgoing transfers within a short window (<30 mins).
        """
        if df.empty or "sender_account" not in df.columns or "receiver_account" not in df.columns or "amount" not in df.columns:
            return []
        df = self._prepare_df(df)
        cases = []
        window_sec = self.rapid_fund_window_minutes * 60.0
        case_idx = 1

        # Accounts that appear as both receiver and sender
        dual_accounts = set(df["receiver_account"]).intersection(set(df["sender_account"]))

        for acc in dual_accounts:
            in_txns = df[df["receiver_account"] == acc].to_dict(orient="records")
            out_txns = df[df["sender_account"] == acc].to_dict(orient="records")

            for in_t in in_txns:
                in_time = in_t["timestamp"]
                for out_t in out_txns:
                    out_time = out_t["timestamp"]
                    if out_time > in_time:
                        diff_sec = (out_time - in_time).total_seconds()
                        if diff_sec <= window_sec:
                            amt_in = in_t["amount"]
                            amt_out = out_t["amount"]
                            # Matching or significant portion
                            if amt_out >= amt_in * 0.70 and amt_in >= 25000.0:
                                cases.append({
                                    "case_id": f"AML-RFM-{case_idx:04d}",
                                    "case_type": "RAPID_FUND_MOVEMENT",
                                    "primary_account": acc,
                                    "involved_accounts": [in_t["sender_account"], out_t["receiver_account"]],
                                    "total_amount": round(float(amt_in + amt_out), 2),
                                    "transaction_count": 2,
                                    "time_span_minutes": round(diff_sec / 60.0, 1),
                                    "evidence_summary": (
                                        f"Inflow of ₹{amt_in:,.2f} from {in_t['sender_account']} was forwarded "
                                        f"as ₹{amt_out:,.2f} to {out_t['receiver_account']} within {diff_sec/60.0:.1f} minutes."
                                    ),
                                    "related_txns": [in_t["transaction_id"], out_t["transaction_id"]],
                                    "severity": "HIGH",
                                    "status": "ACTIVE"
                                })
                                case_idx += 1
                                break

        return cases[:30]  # Cap to prevent alert fatigue

    # -------------------------------------------------------------------------
    # D. CIRCULAR MONEY MOVEMENT (NETWORK CYCLES)
    # -------------------------------------------------------------------------
    def detect_circular_money_movement(self, df: pd.DataFrame, max_len: int = 4, max_cases: int = 15) -> List[Dict[str, Any]]:
        """
        Uses depth-bounded directed search to detect circular routing (e.g. A -> B -> C -> A)
        in sub-second time without exponential cycle explosion.
        """
        if df.empty or "sender_account" not in df.columns or "receiver_account" not in df.columns:
            return []
        df = self._prepare_df(df)
        G = nx.DiGraph()

        edge_data = {}
        for _, r in df.iterrows():
            u = r["sender_account"]
            v = r["receiver_account"]
            if u != v:
                G.add_edge(u, v)
                if (u, v) not in edge_data:
                    edge_data[(u, v)] = []
                edge_data[(u, v)].append({
                    "txn_id": r["transaction_id"],
                    "amount": r["amount"],
                    "timestamp": r["timestamp"]
                })

        # Only check nodes with both in-degree > 0 and out-degree > 0
        candidate_nodes = [n for n in G.nodes() if G.in_degree(n) > 0 and G.out_degree(n) > 0]
        
        found_cycles = []
        visited_cycle_sets = set()

        for start in candidate_nodes:
            stack = [(start, [start])]
            while stack:
                curr, path = stack.pop()
                if len(path) > max_len:
                    continue
                for neighbor in G.successors(curr):
                    if neighbor == start and len(path) >= 3:
                        cycle_tuple = tuple(path)
                        canon = frozenset(cycle_tuple)
                        if canon not in visited_cycle_sets:
                            visited_cycle_sets.add(canon)
                            found_cycles.append(list(cycle_tuple))
                            if len(found_cycles) >= max_cases:
                                break
                    elif neighbor not in path and len(path) < max_len:
                        stack.append((neighbor, path + [neighbor]))
                if len(found_cycles) >= max_cases:
                    break
            if len(found_cycles) >= max_cases:
                break

        cases = []
        for case_idx, cycle in enumerate(found_cycles, start=1):
            cycle_edges = list(zip(cycle, cycle[1:] + [cycle[0]]))
            cycle_txns = []
            total_flow = 0.0

            for u, v in cycle_edges:
                if (u, v) in edge_data:
                    t = edge_data[(u, v)][0]
                    cycle_txns.append(t["txn_id"])
                    total_flow += t["amount"]

            cycle_path_str = " -> ".join(cycle) + f" -> {cycle[0]}"

            cases.append({
                "case_id": f"AML-CIRC-{case_idx:04d}",
                "case_type": "CIRCULAR_TRANSFERS",
                "primary_account": cycle[0],
                "involved_accounts": cycle,
                "total_amount": round(float(total_flow), 2),
                "transaction_count": len(cycle_txns),
                "time_span_minutes": 60.0,
                "evidence_summary": (
                    f"Detected closed circular fund loop: {cycle_path_str} "
                    f"with cumulative flow of ₹{total_flow:,.2f} across {len(cycle)} intermediary nodes."
                ),
                "related_txns": cycle_txns,
                "severity": "CRITICAL",
                "status": "ACTIVE"
            })

        return cases

    # -------------------------------------------------------------------------
    # E. SUSPICIOUS NETWORK ANALYSIS
    # -------------------------------------------------------------------------
    def analyze_network_topology(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Builds graph representation and extracts network metrics:
        - In-degree & Out-degree centrality
        - High volume hubs
        - Connected components & isolated clusters
        """
        if df.empty or "sender_account" not in df.columns or "receiver_account" not in df.columns or "amount" not in df.columns:
            return {
                "node_count": 0,
                "edge_count": 0,
                "top_receivers": [],
                "top_senders": [],
                "degree_centrality": {},
                "graph": nx.DiGraph()
            }
        df = self._prepare_df(df)
        G = nx.DiGraph()

        for _, r in df.iterrows():
            u = r["sender_account"]
            v = r["receiver_account"]
            amt = float(r["amount"])
            if G.has_edge(u, v):
                G[u][v]["weight"] += amt
                G[u][v]["count"] += 1
            else:
                G.add_edge(u, v, weight=amt, count=1)

        in_degrees = dict(G.in_degree())
        out_degrees = dict(G.out_degree())
        degree_centrality = nx.degree_centrality(G)

        # Top hubs
        top_receivers = sorted(in_degrees.items(), key=lambda x: -x[1])[:10]
        top_senders = sorted(out_degrees.items(), key=lambda x: -x[1])[:10]

        return {
            "node_count": G.number_of_nodes(),
            "edge_count": G.number_of_edges(),
            "top_receivers": top_receivers,
            "top_senders": top_senders,
            "degree_centrality": degree_centrality,
            "graph": G
        }

    # -------------------------------------------------------------------------
    # MASTER RUNNER
    # -------------------------------------------------------------------------
    def run_all_checks(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Runs all detection sub-engines and aggregates alerts."""
        if df.empty or "sender_account" not in df.columns or "receiver_account" not in df.columns or "amount" not in df.columns:
            return {
                "all_cases": [],
                "structuring_cases": [],
                "mule_cases": [],
                "rapid_movement_cases": [],
                "circular_cases": [],
                "topology": {
                    "node_count": 0,
                    "edge_count": 0,
                    "top_receivers": [],
                    "top_senders": [],
                    "degree_centrality": {},
                    "graph": nx.DiGraph()
                },
                "total_case_count": 0,
                "total_suspicious_volume": 0.0
            }

        structuring = self.detect_structuring(df)
        mules = self.detect_mule_accounts(df)
        rapid_movement = self.detect_rapid_fund_movement(df)
        circular = self.detect_circular_money_movement(df)
        topology = self.analyze_network_topology(df)

        all_cases = structuring + mules + rapid_movement + circular

        return {
            "all_cases": all_cases,
            "structuring_cases": structuring,
            "mule_cases": mules,
            "rapid_movement_cases": rapid_movement,
            "circular_cases": circular,
            "topology": topology,
            "total_case_count": len(all_cases),
            "total_suspicious_volume": sum(c["total_amount"] for c in all_cases)
        }


if __name__ == "__main__":
    from generator import TransactionGenerator
    gen = TransactionGenerator(seed=42)
    df = gen.generate_full_dataset(total_normal=500, save_csv=False)
    aml = AMLEngine()
    res = aml.run_all_checks(df)
    print("=== AML Engine Diagnostic Run ===")
    print(f"Total AML Cases Detected: {res['total_case_count']}")
    print(f"Structuring: {len(res['structuring_cases'])}")
    print(f"Mule Accounts: {len(res['mule_cases'])}")
    print(f"Rapid Movement: {len(res['rapid_movement_cases'])}")
    print(f"Circular Transfers: {len(res['circular_cases'])}")
    if res['all_cases']:
        print("\nSample Case:", res['all_cases'][0]['evidence_summary'])
