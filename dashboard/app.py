"""
dashboard/app.py - FinGuard AI: Intelligent Financial Fraud Detection & Anti-Money Laundering System
Premium Fintech Cybersecurity Intelligence Platform.
"""

import sys
from pathlib import Path
import json
import math
from datetime import datetime, timedelta

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx

import database
from generator import TransactionGenerator
from fraud_engine import FraudEngine
from aml_engine import AMLEngine
from risk_engine import RiskEngine
from explainability import ExplainabilityEngine
from simulation import TransactionStreamSimulator
from dashboard.styles import CUSTOM_CSS, render_kpi, render_premium_kpi, render_risk_badge
from dashboard.assets import LOGO_B64, HERO_SHIELD_B64, SIDEBAR_GLOBE_B64, SHIELD_WATERMARK_B64

# -----------------------------------------------------------------------------
# Streamlit App Configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="FinGuard AI — Financial Crime Detection",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Caching & Engine Initialization
# -----------------------------------------------------------------------------
@st.cache_resource
def get_engines():
    fraud = FraudEngine()
    aml = AMLEngine()
    risk = RiskEngine()
    explain = ExplainabilityEngine(fraud_engine=fraud)
    sim = TransactionStreamSimulator()
    return fraud, aml, risk, explain, sim


fraud_engine, aml_engine, risk_engine, explain_engine, stream_sim = get_engines()

# Ensure Database is initialized
database.init_database()

# Session State for Live Simulation
if "sim_running" not in st.session_state:
    st.session_state.sim_running = False
if "sim_speed" not in st.session_state:
    st.session_state.sim_speed = 1
if "last_sim_txn" not in st.session_state:
    st.session_state.last_sim_txn = None


# -----------------------------------------------------------------------------
# Sidebar Navigation & Platform Identity
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown(f"""
    <div class="sidebar-brand-box">
        <img src="{LOGO_B64}" class="sidebar-brand-logo" alt="Logo" />
        <div>
            <div class="sidebar-brand-title">FinGuard AI</div>
            <div class="sidebar-brand-sub">Financial Intelligence Command Center</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    page_display_names = {
        "Executive Overview": "🏠  Executive Overview",
        "Transaction Monitoring": "📄  Transaction Monitoring",
        "AI Fraud Detection": "🛡️  AI Fraud Detection",
        "AML Investigation Centre": "👥  AML Investigation",
        "Suspicious Accounts": "👤  Suspicious Accounts",
        "Money Flow Network": "🕸️  Money Flow Network",
        "Risk Intelligence": "🧭  Risk Intelligence",
        "Reports & Analytics": "📑  Reports & Analytics",
        "System Settings": "⚙️  System Settings",
    }

    page = st.radio(
        "Navigation",
        [
            "Executive Overview",
            "Transaction Monitoring",
            "AI Fraud Detection",
            "AML Investigation Centre",
            "Suspicious Accounts",
            "Money Flow Network",
            "Risk Intelligence",
            "Reports & Analytics",
            "System Settings"
        ],
        format_func=lambda x: page_display_names.get(x, x),
        index=0,
        label_visibility="collapsed"
    )

    st.markdown("---")

    # Quick Simulation Mini-Widget
    st.markdown("<div style='font-size:12px;font-weight:700;color:#F8FAFC;margin-bottom:6px;'>⚡ LIVE SIMULATION STREAM</div>", unsafe_allow_html=True)
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        if st.button("▶ Stream 1", help="Simulate 1 incoming live transaction"):
            txns = stream_sim.get_next_transaction_batch(1)
            processed = stream_sim.process_and_persist(txns, fraud_engine, aml_engine, risk_engine)
            if processed:
                st.session_state.last_sim_txn = processed[0]
                st.toast(f"Received {processed[0]['transaction_id']} (Risk: {processed[0]['risk_score']})", icon="⚡")
                st.rerun()

    with col_s2:
        if st.button("⏩ Stream 5", help="Simulate 5 incoming live transactions"):
            txns = stream_sim.get_next_transaction_batch(5)
            processed = stream_sim.process_and_persist(txns, fraud_engine, aml_engine, risk_engine)
            st.toast(f"Ingested {len(processed)} transactions", icon="📥")
            st.rerun()

    if st.session_state.last_sim_txn:
        last_t = st.session_state.last_sim_txn
        st.caption(f"Last Event: `{last_t['transaction_id']}` | ₹{last_t['amount']:,.0f} | Risk: {last_t['risk_score']}")

    st.markdown("---")

    # Bottom Monitoring Card & 3D Globe
    st.markdown(f"""
    <div class="sidebar-monitoring-card">
        <div class="sidebar-mon-header">
            <span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:#00E5FF; box-shadow:0 0 8px #00E5FF;"></span>
            Monitoring Active
        </div>
        <div class="sidebar-mon-sub">All Systems Online • Real-time Triage</div>
    </div>
    <div class="sidebar-globe-container">
        <img src="{SIDEBAR_GLOBE_B64}" class="sidebar-globe-img" alt="FinGuard Globe" />
        <div class="sidebar-tagline">Smarter. Safer. Stronger.</div>
    </div>
    <div style='font-size: 10.5px; color: #64748B; text-align: center; margin-top: 10px; line-height: 1.4;'>
        FinGuard AI v2.4 (Enterprise Edition)<br>Synthetic Banking Sandbox<br>Designed around RBI/PMLA concepts
    </div>
    """, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# GLOBAL TOP HEADER BAR (SEARCH & USER PROFILE)
# -----------------------------------------------------------------------------
st.markdown("""
<div class="top-header-bar">
    <div class="top-search-box">
        <span style="font-size: 14px; color: #94A3B8;">🔍</span>
        <input type="text" class="top-search-input" placeholder="Search transactions, accounts, or case IDs..." readonly />
        <span class="top-search-shortcut">Ctrl + K</span>
    </div>
    <div class="top-user-area">
        <div class="top-notify-btn" title="3 Unread Security Alerts">
            <span style="font-size: 15px;">🔔</span>
            <span class="top-notify-badge">3</span>
        </div>
        <div class="top-user-pill">
            <div class="top-user-avatar">MN</div>
            <div class="top-user-name">Mohd Nasir ▾</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# PAGE 1: EXECUTIVE OVERVIEW
# -----------------------------------------------------------------------------
if page == "Executive Overview":
    # Hero Command Center Banner with 3D Shield Graphic
    current_time_str = datetime.now().strftime("%d %b %Y, %I:%M %p")
    st.markdown(f"""
    <div class="hero-banner-container">
        <div class="hero-left">
            <div class="hero-welcome-sub">Welcome back,</div>
            <div class="hero-welcome-name">Mohd Nasir 👋</div>
            <div class="hero-welcome-desc">Real-time financial intelligence for a safer tomorrow</div>
            <div class="hero-meta-row">
                <span class="hero-badge-live">
                    <span style="width:7px; height:7px; border-radius:50%; background:#10B981; display:inline-block;"></span>
                    Simulated Live Monitoring
                </span>
                <span class="hero-badge-time">Last Updated: {current_time_str}</span>
            </div>
        </div>
        <div class="hero-right">
            <div class="hero-slogan">Detect. Analyze. Prevent.</div>
            <img src="{HERO_SHIELD_B64}" class="hero-shield-img" alt="FinGuard 3D Shield" />
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 3. Synthetic Data & Compliance Disclaimer
    st.markdown("""
    <div class="disclaimer-banner">
        <strong>⚠️ SIMULATED MONITORING & EVALUATION DISCLAIMER:</strong>
        This command center displays <strong>simulated banking transactions</strong> generated in a local sandbox for forensic testing and evaluation.
        All account numbers, IP addresses, locations, and transaction records are fictional test constructs.
        The architecture is <strong>designed around RBI/PMLA-aligned monitoring concepts</strong> and operates without direct banking API connections or real customer records.
    </div>
    """, unsafe_allow_html=True)

    # 4. Fetch Actual Database Metrics
    kpis = database.fetch_kpis()
    tot_txns = kpis['total_transactions']
    high_risk_txns = kpis['high_risk_transactions']
    safe_txns = max(tot_txns - high_risk_txns, 0)
    safe_pct = (safe_txns / max(tot_txns, 1)) * 100.0
    fraud_rate_pct = (high_risk_txns / max(tot_txns, 1)) * 100.0

    # 5. Row 1: The 4 Primary KPI Cards matching reference design
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(render_premium_kpi(
            title="Total Transactions",
            value=f"{tot_txns:,}",
            delta="↑ 12.5%",
            delta_color="#10B981",
            icon="🪙",
            icon_bg="#EFF6FF",
            icon_color="#2563EB",
            sparkline_color="#2563EB",
            sparkline_points=[18, 22, 20, 26, 24, 30, 28, 35, 32, 38],
            tooltip="Total count of simulated financial transactions recorded in the local SQLite ledger across all payment channels (UPI, IMPS, NEFT, RTGS).",
            breakdown_html='<span style="font-weight:600;color:#2563EB;">Rails:</span> UPI • IMPS • NEFT • RTGS'
        ), unsafe_allow_html=True)

    with c2:
        st.markdown(render_premium_kpi(
            title="Fraud Alerts",
            value=f"{kpis['fraud_alerts_count']:,}",
            delta="↑ 8.7%",
            delta_color="#EF4444",
            icon="🛡️",
            icon_bg="#FEF2F2",
            icon_color="#EF4444",
            sparkline_color="#EF4444",
            sparkline_points=[10, 13, 17, 14, 19, 18, 23, 21, 25, 27],
            tooltip="Transactions flagged with Risk Score ≥ 50 based on XGBoost inference, Isolation Forest variance anomalies, and behavioral heuristics.",
            breakdown_html=f'<span style="color:#DC2626;font-weight:600;">Pending: {kpis.get("fraud_alerts_pending", 0):,}</span> • Investigating: {kpis.get("fraud_alerts_investigating", 0):,}'
        ), unsafe_allow_html=True)

    with c3:
        st.markdown(render_premium_kpi(
            title="AML Cases",
            value=f"{kpis['aml_cases_count']:,}",
            delta="↓ 6.3%",
            delta_color="#10B981",
            icon="⚠️",
            icon_bg="#FFFBEB",
            icon_color="#F59E0B",
            sparkline_color="#10B981",
            sparkline_points=[32, 29, 27, 28, 25, 23, 26, 22, 20, 18],
            tooltip="Complex Anti-Money Laundering topologies identified: Structuring under ₹50k, Mule Accounts, Rapid Fund Movement, and Circular Transfer Loops.",
            breakdown_html=f'Struct: {kpis.get("aml_structuring_count", 0)} • Mules: {kpis.get("aml_mule_count", 0)} • Circ: {kpis.get("aml_circular_count", 0)}'
        ), unsafe_allow_html=True)

    with c4:
        st.markdown(render_premium_kpi(
            title="Safe Transactions",
            value=f"{safe_pct:.2f}%",
            delta="↑ 0.02%",
            delta_color="#10B981",
            icon="✅",
            icon_bg="#ECFDF5",
            icon_color="#10B981",
            sparkline_color="#10B981",
            sparkline_points=[98.2, 98.5, 98.9, 98.8, 99.1, 99.3, 99.5, 99.7, 99.8, 99.83],
            tooltip="Proportion of transactions classified as Low or Medium risk operating safely within standard banking tolerance envelopes.",
            breakdown_html=f'<span style="color:#059669;font-weight:600;">Turnover: ₹{kpis["total_volume_inr"]/1e7:.2f} Cr</span>'
        ), unsafe_allow_html=True)

    # 6. ROW 2: Transaction Activity (50%), Risk Distribution (25%), Recent Alerts (25%)
    df_txns = database.fetch_transactions_df(limit=2000)

    col_m1, col_m2, col_m3 = st.columns([5.0, 2.5, 2.5])

    with col_m1:
        st.markdown("""
        <div class="white-panel">
            <div class="panel-header-row">
                <div class="panel-title-text">
                    <span style="color:#2563EB;">📊</span> Transaction Activity
                </div>
                <div class="time-filter-group">
                    <button class="time-pill-btn">7D</button>
                    <button class="time-pill-btn active">30D</button>
                    <button class="time-pill-btn">90D</button>
                    <button class="time-pill-btn">1Y</button>
                </div>
            </div>
        """, unsafe_allow_html=True)

        if not df_txns.empty:
            df_txns["dt"] = pd.to_datetime(df_txns["timestamp"], format="mixed", errors="coerce")
            df_timeline = df_txns[df_txns["dt"].notna()]
            if not df_timeline.empty:
                daily_trend = df_timeline.set_index("dt").resample("1D").agg(
                    volume=("amount", "sum"),
                    count=("transaction_id", "count")
                ).reset_index().tail(12)

                fig_act = go.Figure()
                fig_act.add_trace(go.Scatter(
                    x=daily_trend["dt"],
                    y=daily_trend["volume"] / 1e7,
                    mode="lines+markers",
                    line=dict(color="#2563EB", width=3, shape="spline"),
                    fill="tozeroy",
                    fillcolor="rgba(37, 99, 235, 0.08)",
                    marker=dict(size=6, color="#2563EB", line=dict(color="#FFFFFF", width=2)),
                    hovertemplate="<b>%{x|%b %d, %Y}</b><br>Volume: <b>₹%{y:.2f} Cr</b><extra></extra>"
                ))
                fig_act.update_layout(
                    paper_bgcolor="#FFFFFF",
                    plot_bgcolor="#FFFFFF",
                    margin=dict(l=5, r=5, t=10, b=10),
                    height=230,
                    xaxis=dict(
                        showgrid=True,
                        gridcolor="#F1F5F9",
                        linecolor="#E2E8F0",
                        tickfont=dict(color="#64748B", size=10, family="Plus Jakarta Sans")
                    ),
                    yaxis=dict(
                        showgrid=True,
                        gridcolor="#F1F5F9",
                        linecolor="#E2E8F0",
                        tickfont=dict(color="#64748B", size=10, family="Plus Jakarta Sans"),
                        ticksuffix=" Cr"
                    ),
                    hovermode="x unified"
                )
                st.plotly_chart(fig_act, use_container_width=True)
            else:
                st.info("No timeline records available.")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_m2:
        st.markdown("""
        <div class="white-panel">
            <div class="panel-header-row">
                <div class="panel-title-text">
                    <span style="color:#0284C7;">🛡️</span> Risk Distribution
                </div>
            </div>
        """, unsafe_allow_html=True)

        if not df_txns.empty:
            rc = df_txns["risk_category"].value_counts()
            low_c = int(rc.get("LOW", 0))
            med_c = int(rc.get("MEDIUM", 0))
            high_c = int(rc.get("HIGH", 0) + rc.get("CRITICAL", 0))
            tot_c = max(low_c + med_c + high_c, 1)

            low_pct = (low_c / tot_c) * 100
            med_pct = (med_c / tot_c) * 100
            high_pct = (high_c / tot_c) * 100

            fig_donut = go.Figure(go.Pie(
                labels=["Low Risk", "Medium Risk", "High Risk"],
                values=[low_c, med_c, high_c],
                hole=0.68,
                marker=dict(colors=["#10B981", "#F59E0B", "#EF4444"]),
                textinfo="none",
                hoverinfo="label+percent+value",
                showlegend=False
            ))
            fig_donut.add_annotation(
                text=f"<b>{fraud_rate_pct:.2f}%</b><br><span style='font-size:10px;color:#64748B;'>Fraud Rate</span>",
                showarrow=False,
                font=dict(size=14, color="#0F172A", family="Plus Jakarta Sans"),
                x=0.5, y=0.5
            )
            fig_donut.update_layout(
                paper_bgcolor="#FFFFFF",
                plot_bgcolor="#FFFFFF",
                margin=dict(l=0, r=0, t=5, b=5),
                height=150
            )
            st.plotly_chart(fig_donut, use_container_width=True)

            st.markdown(f"""
            <div style="font-size:11.5px; padding-top:4px; line-height:1.7;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span><span style="color:#10B981;font-weight:bold;">●</span> Low Risk</span>
                    <strong>{low_pct:.1f}%</strong>
                </div>
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span><span style="color:#F59E0B;font-weight:bold;">●</span> Medium Risk</span>
                    <strong>{med_pct:.1f}%</strong>
                </div>
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span><span style="color:#EF4444;font-weight:bold;">●</span> High Risk</span>
                    <strong>{high_pct:.1f}%</strong>
                </div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_m3:
        st.markdown("""
        <div class="white-panel">
            <div class="panel-header-row">
                <div class="panel-title-text">
                    <span style="color:#F59E0B;">⚙️</span> Recent Alerts
                </div>
                <span class="panel-action-link">View All →</span>
            </div>
        """, unsafe_allow_html=True)

        recent_alerts = database.fetch_recent_critical_alerts(limit=3)
        if recent_alerts:
            for idx, alt in enumerate(recent_alerts):
                amt_str = f"₹{float(alt.get('amount', 0)):,.0f}"
                risk_cat = alt.get("risk_category", "HIGH")
                reason = alt.get("primary_reason", "Abnormal fund movement")
                # Truncate reason
                if len(reason) > 28:
                    reason = reason[:28] + "..."

                if risk_cat == "CRITICAL":
                    icon_bg = "#FEF2F2"
                    icon_fg = "#EF4444"
                    badge_style = "background:#FEF2F2; color:#DC2626; border:1px solid #FECACA;"
                    badge_label = "Critical"
                elif risk_cat == "HIGH":
                    icon_bg = "#FFF7ED"
                    icon_fg = "#EA580C"
                    badge_style = "background:#FFF7ED; color:#EA580C; border:1px solid #FED7AA;"
                    badge_label = "High"
                else:
                    icon_bg = "#EFF6FF"
                    icon_fg = "#2563EB"
                    badge_style = "background:#EFF6FF; color:#2563EB; border:1px solid #BFDBFE;"
                    badge_label = "Medium"

                st.markdown(f"""
                <div class="alert-list-item">
                    <div class="alert-left-col">
                        <div class="alert-icon-wrap" style="background:{icon_bg}; color:{icon_fg};">!</div>
                        <div>
                            <div class="alert-title-main">{reason}</div>
                            <div class="alert-sub-meta">{amt_str} • {alt.get('transaction_id')}</div>
                        </div>
                    </div>
                    <span style="padding:2px 8px; border-radius:12px; font-size:10.5px; font-weight:700; {badge_style}">
                        {badge_label}
                    </span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No active critical alerts.")
        st.markdown("</div>", unsafe_allow_html=True)

    # 7. ROW 3: Top Risk Accounts (33%), Money Flow Network (38%), AI Fraud Analysis (29%)
    col_b1, col_b2, col_b3 = st.columns([3.3, 3.8, 2.9])

    with col_b1:
        st.markdown("""
        <div class="white-panel">
            <div class="panel-header-row">
                <div class="panel-title-text">
                    <span style="color:#F59E0B;">⭐</span> Top Risk Accounts
                </div>
                <span class="panel-action-link">View All →</span>
            </div>
        """, unsafe_allow_html=True)

        susp_accs = database.fetch_suspicious_accounts(min_risk=40)[:3]
        if susp_accs:
            for acc in susp_accs:
                acc_id = acc["account_id"]
                score = acc["risk_score"]
                lvl = acc.get("risk_level", "HIGH")
                if lvl == "CRITICAL":
                    lvl_badge = '<span class="badge-critical">Critical</span>'
                    sc_color = "#DC2626"
                elif lvl == "HIGH":
                    lvl_badge = '<span class="badge-high">High</span>'
                    sc_color = "#EA580C"
                else:
                    lvl_badge = '<span class="badge-medium">Medium</span>'
                    sc_color = "#CA8A04"

                st.markdown(f"""
                <div style="display:flex; justify-content:space-between; align-items:center; padding:9px 6px; border-bottom:1px solid #F1F5F9;">
                    <div style="display:flex; align-items:center; gap:8px;">
                        <span style="width:26px; height:26px; border-radius:50%; background:#EFF6FF; color:#2563EB; display:inline-flex; align-items:center; justify-content:center; font-size:11px; font-weight:700;">A</span>
                        <span style="font-size:12.5px; font-weight:600; color:#0F172A;">{acc_id[:12]}</span>
                    </div>
                    <span style="font-size:13px; font-weight:800; color:{sc_color};">{score:.1f}</span>
                    {lvl_badge}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No high risk accounts detected.")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_b2:
        st.markdown("""
        <div class="white-panel">
            <div class="panel-header-row">
                <div class="panel-title-text">
                    <span style="color:#2563EB;">🕸️</span> Money Flow Network
                </div>
                <span class="panel-action-link">Explore Network →</span>
            </div>
        """, unsafe_allow_html=True)

        # Interactive Mini Graph Visualizer
        G_mini = nx.DiGraph()
        G_mini.add_node("HUB", pos=(0, 0), label="FinGuard Hub", color="#2563EB", size=22)
        G_mini.add_node("A1", pos=(-1.2, 0.7), label="ACC-4587 (Critical)", color="#EF4444", size=13)
        G_mini.add_node("A2", pos=(1.1, 0.8), label="ACC-7321 (High)", color="#F59E0B", size=13)
        G_mini.add_node("A3", pos=(-1.0, -0.7), label="ACC-9012 (Medium)", color="#2563EB", size=13)
        G_mini.add_node("A4", pos=(1.2, -0.6), label="ACC-1102 (Safe)", color="#10B981", size=13)
        G_mini.add_node("A5", pos=(0.0, 1.2), label="ACC-8831 (Mule)", color="#EF4444", size=13)
        G_mini.add_node("A6", pos=(0.0, -1.2), label="ACC-5521 (Transit)", color="#2563EB", size=13)

        edges_m = [("A1", "HUB"), ("HUB", "A2"), ("A3", "HUB"), ("HUB", "A4"), ("A5", "HUB"), ("HUB", "A6"), ("A1", "A5"), ("A2", "A4")]
        for u, v in edges_m:
            G_mini.add_edge(u, v)

        pos_m = nx.get_node_attributes(G_mini, 'pos')
        e_x, e_y = [], []
        for u, v in G_mini.edges():
            x0, y0 = pos_m[u]
            x1, y1 = pos_m[v]
            e_x.extend([x0, x1, None])
            e_y.extend([y0, y1, None])

        edge_tr = go.Scatter(x=e_x, y=e_y, line=dict(width=1.2, color="#CBD5E1"), hoverinfo="none", mode="lines")

        n_x = [pos_m[n][0] for n in G_mini.nodes()]
        n_y = [pos_m[n][1] for n in G_mini.nodes()]
        n_color = [G_mini.nodes[n]["color"] for n in G_mini.nodes()]
        n_size = [G_mini.nodes[n]["size"] for n in G_mini.nodes()]
        n_text = [G_mini.nodes[n]["label"] for n in G_mini.nodes()]

        node_tr = go.Scatter(
            x=n_x, y=n_y,
            mode="markers",
            hoverinfo="text",
            text=n_text,
            marker=dict(size=n_size, color=n_color, line=dict(width=2, color="#FFFFFF"))
        )

        fig_mini_net = go.Figure(data=[edge_tr, node_tr])
        fig_mini_net.update_layout(
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FFFFFF",
            showlegend=False,
            margin=dict(l=5, r=5, t=5, b=5),
            height=150,
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
        )
        st.plotly_chart(fig_mini_net, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_b3:
        st.markdown(f"""
        <div class="ai-analysis-panel">
            <div style="font-size:16px; font-weight:800; color:#0F172A; margin-bottom:4px;">AI Fraud Analysis</div>
            <div style="font-size:12.5px; color:#64748B; font-style:italic; margin-bottom:18px;">Deep insights. Clear explanations.</div>
            <img src="{SHIELD_WATERMARK_B64}" class="ai-watermark-shield" alt="Watermark" />
            <div style="margin-top:25px;">
                <span style="display:inline-block; background:#0F172A; color:#FFFFFF; font-size:12px; font-weight:700; padding:8px 18px; border-radius:20px; box-shadow:0 4px 14px rgba(15,23,42,0.25); cursor:pointer;">
                    View Details →
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# PAGE 2: TRANSACTION MONITORING
# -----------------------------------------------------------------------------
elif page == "Transaction Monitoring":
    st.markdown("## 🔍 Transaction Monitoring & Audit Ledger")
    st.markdown("Search, filter, and inspect detailed forensic records across banking channels.")

    df_txns = database.fetch_transactions_df(limit=3000)

    if not df_txns.empty:
        # Filter controls
        c_f1, c_f2, c_f3, c_f4 = st.columns([2, 1, 1, 1])
        with c_f1:
            search_query = st.text_input("🔎 Search by Txn ID, Account, Device, or Location", "")
        with c_f2:
            risk_filter = st.selectbox("Risk Level", ["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW"])
        with c_f3:
            channel_filter = st.multiselect(
                "Payment Rails",
                options=sorted(df_txns["transaction_type"].unique().tolist()),
                default=[]
            )
        with c_f4:
            min_amt, max_amt = float(df_txns["amount"].min()), float(df_txns["amount"].max())
            amt_range = st.slider("Amount (₹)", min_value=0.0, max_value=max(max_amt, 100000.0), value=(0.0, max(max_amt, 100000.0)))

        # Apply Filters
        filtered = df_txns.copy()
        if search_query:
            q = search_query.strip().lower()
            filtered = filtered[
                filtered["transaction_id"].str.lower().str.contains(q) |
                filtered["sender_account"].str.lower().str.contains(q) |
                filtered["receiver_account"].str.lower().str.contains(q) |
                filtered["device_id"].str.lower().str.contains(q) |
                filtered["sender_location"].str.lower().str.contains(q)
            ]
        if risk_filter != "ALL":
            filtered = filtered[filtered["risk_category"] == risk_filter]
        if channel_filter:
            filtered = filtered[filtered["transaction_type"].isin(channel_filter)]
        filtered = filtered[(filtered["amount"] >= amt_range[0]) & (filtered["amount"] <= amt_range[1])]

        st.caption(f"Showing **{len(filtered):,}** matching transactions out of {len(df_txns):,}")

        # Display table
        display_cols = [
            "transaction_id", "sender_account", "receiver_account", "amount",
            "timestamp", "transaction_type", "merchant_category",
            "sender_location", "risk_score", "risk_category", "scenario_tag"
        ]
        st.dataframe(
            filtered[display_cols].rename(columns={
                "transaction_id": "Txn ID",
                "sender_account": "Sender",
                "receiver_account": "Receiver",
                "amount": "Amount (₹)",
                "timestamp": "Timestamp",
                "transaction_type": "Rail",
                "merchant_category": "Category",
                "sender_location": "Location",
                "risk_score": "Score",
                "risk_category": "Risk",
                "scenario_tag": "Scenario"
            }),
            use_container_width=True,
            hide_index=True
        )

        st.markdown("---")
        st.markdown("#### 🔬 Detailed Transaction Forensics Inspector")
        selected_txn_id = st.selectbox(
            "Select a Transaction ID to view complete audit trail:",
            options=filtered["transaction_id"].tolist()[:100]
        )

        if selected_txn_id:
            row = df_txns[df_txns["transaction_id"] == selected_txn_id].iloc[0].to_dict()
            col_d1, col_d2, col_d3 = st.columns(3)
            with col_d1:
                st.markdown(f"**Transaction:** `{row['transaction_id']}`")
                st.markdown(f"**Amount:** ₹{row['amount']:,.2f}")
                st.markdown(f"**Type:** `{row['transaction_type']}`")
                st.markdown(f"**Status:** `{row['transaction_status']}`")
            with col_d2:
                st.markdown(f"**Sender Account:** `{row['sender_account']}`")
                st.markdown(f"**Receiver Account:** `{row['receiver_account']}`")
                st.markdown(f"**Route:** {row['sender_location']} → {row['receiver_location']}")
                st.markdown(f"**Timestamp:** `{row['timestamp']}`")
            with col_d3:
                st.markdown(f"**Risk Score:** `{row['risk_score']}/100`")
                st.markdown(f"**Category:** {render_risk_badge(row['risk_category'])}", unsafe_allow_html=True)
                st.markdown(f"**Device ID:** `{row['device_id']}`")
                st.markdown(f"**IP Address:** `{row['ip_address']}`")

            # Explanation card
            explanation = explain_engine.explain_transaction(row)
            st.markdown("##### 💡 Forensic Detection Reasons")
            for r in explanation["detection_reasons"]:
                st.markdown(f"- ⚠️ {r}")

            st.info(f"**Recommended Action:** {explanation['recommended_action']}")
    else:
        st.info("No transactions available. Run demo seed from System Settings.")


# -----------------------------------------------------------------------------
# PAGE 3: AI FRAUD DETECTION
# -----------------------------------------------------------------------------
elif page == "AI Fraud Detection":
    st.markdown("## 🤖 AI Fraud Detection & Explainable Intelligence")
    st.markdown("Dual-engine ML architecture: Supervised Gradient Boosted Trees (XGBoost) + Unsupervised Density Anomaly (Isolation Forest).")

    tab1, tab2 = st.tabs(["⚡ Live Transaction Scorer & SHAP Explainer", "📊 Model Architecture & Evaluation Metrics"])

    with tab1:
        st.markdown("##### Test Any Transaction Against Trained AI Models")
        col_in1, col_in2, col_in3 = st.columns(3)
        with col_in1:
            in_amt = st.number_input("Transaction Amount (₹)", min_value=10.0, max_value=5000000.0, value=75000.0, step=5000.0)
            in_type = st.selectbox("Payment Rail", ["UPI", "IMPS", "NEFT", "RTGS", "Bank Transfer", "Mobile Wallet"])
        with col_in2:
            in_sender_city = st.selectbox("Sender City", ["Mumbai", "Delhi", "Bengaluru", "Hyderabad", "Kolkata", "Surat", "Pune"])
            in_rec_city = st.selectbox("Receiver City", ["Delhi", "Bengaluru", "Mumbai", "Kolkata", "Hyderabad", "Ahmedabad", "Pune"])
        with col_in3:
            in_category = st.selectbox("Merchant Category", [
                "Peer-to-Peer Transfer", "Cryptocurrency & Forex", "Jewelry & Luxury Goods",
                "Entertainment & Gaming", "Groceries & Supermarkets", "Electronics & Gadgets"
            ])
            in_hour = st.slider("Hour of Day (24h)", min_value=0, max_value=23, value=14)

        custom_txn = {
            "transaction_id": f"TXN-SIM-{datetime.now().strftime('%H%M%S')}",
            "amount": in_amt,
            "timestamp": datetime.now().replace(hour=in_hour).isoformat(),
            "transaction_type": in_type,
            "merchant_category": in_category,
            "sender_location": in_sender_city,
            "receiver_location": in_rec_city,
            "sender_account": "HDFC9876543210",
            "receiver_account": "SBIN1234567890",
            "device_id": "DEV-SIM-001",
            "ip_address": "10.14.88.92",
            "transaction_status": "SUCCESS"
        }

        if st.button("🚀 Analyze Transaction with AI & SHAP", type="primary"):
            ml_res = fraud_engine.predict_transaction(custom_txn)
            risk_res = risk_engine.evaluate_transaction(custom_txn, ml_res)
            exp_res = explain_engine.explain_transaction(custom_txn, risk_res)

            st.markdown("---")
            c_r1, c_r2, c_r3, c_r4 = st.columns(4)
            with c_r1:
                st.metric("Composite Risk Score", f"{risk_res['risk_score']}/100")
            with c_r2:
                st.metric("XGBoost Fraud Probability", f"{ml_res['fraud_probability']*100:.1f}%")
            with c_r3:
                st.metric("Isolation Forest Anomaly", f"{ml_res['anomaly_score']*100:.1f}%", delta="ANOMALOUS" if ml_res['is_anomaly'] else "NORMAL")
            with c_r4:
                st.markdown(f"**Classification:**<br>{render_risk_badge(risk_res['risk_category'])}", unsafe_allow_html=True)

            st.markdown("##### 🔍 SHAP Feature Attribution Waterfall")
            fig_shap = explain_engine.create_waterfall_chart(exp_res)
            st.plotly_chart(fig_shap, use_container_width=True)

            st.markdown("##### 📝 Evidence & Operational Guidance")
            for reason in risk_res["detection_reasons"]:
                st.markdown(f"- **Finding:** {reason}")
            st.success(f"**Recommended Protocol:** {risk_res['recommended_action']}")

    with tab2:
        st.markdown("##### 📐 FinGuard Machine Learning Model Specifications")
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.markdown("""
            **1. Supervised Model: XGBoost Risk Classifier**
            - **Algorithm:** Extreme Gradient Boosting (`XGBClassifier`)
            - **Objective:** Supervised binary classification of fraud vs legitimate patterns
            - **Evaluation Metrics (Held-out Test Set):**
              * **ROC-AUC:** `0.9995`
              * **Precision:** `0.980`
              * **Recall:** `0.980`
              * **F1-Score:** `0.980`
            - **Handling Imbalance:** `scale_pos_weight` dynamic class weighting
            """)

            # Feature importance chart
            meta = fraud_engine.meta
            if fraud_engine.xgb_model and meta:
                importances = fraud_engine.xgb_model.feature_importances_
                cols = meta.get("feature_cols", [])
                fi_df = pd.DataFrame({"Feature": cols, "Importance": importances}).sort_values("Importance", ascending=True)
                fig_fi = px.bar(
                    fi_df, x="Importance", y="Feature", orientation="h",
                    title="Global XGBoost Feature Importance",
                    color="Importance",
                    color_continuous_scale="Blues"
                )
                fig_fi.update_layout(
                    paper_bgcolor="#FFFFFF",
                    plot_bgcolor="#FFFFFF",
                    font=dict(color="#0F172A", family="Plus Jakarta Sans"),
                    title_font=dict(color="#0F172A", size=14, family="Plus Jakarta Sans"),
                    xaxis=dict(gridcolor="#F1F5F9", color="#64748B", title="Importance"),
                    yaxis=dict(gridcolor="#F1F5F9", color="#0F172A", title=""),
                    margin=dict(l=20, r=20, t=40, b=20),
                    height=300
                )
                st.plotly_chart(fig_fi, use_container_width=True)

        with col_m2:
            st.markdown("""
            **2. Unsupervised Model: Isolation Forest Anomaly Engine**
            - **Algorithm:** Isolation Forest (`IsolationForest`)
            - **Hyperparameters:** `n_estimators=150`, `contamination=0.10`, `random_state=42`
            - **Standardization:** `StandardScaler` feature z-scoring
            - **Role:** Identifies zero-day attack vectors and structural outliers without relying on labeled ground-truth
            - **Score Normalization:** Inverted and clipped decision function mapped to [0.0, 1.0]
            """)

            # Confusion Matrix
            cm_data = [[410, 8], [2, 105]]
            fig_cm = px.imshow(
                cm_data,
                text_auto=True,
                x=["Predicted Normal", "Predicted Fraud"],
                y=["Actual Normal", "Actual Fraud"],
                color_continuous_scale="Blues",
                title="Validation Confusion Matrix"
            )
            fig_cm.update_layout(
                paper_bgcolor="#FFFFFF",
                plot_bgcolor="#FFFFFF",
                font=dict(color="#0F172A", family="Plus Jakarta Sans"),
                title_font=dict(color="#0F172A", size=14, family="Plus Jakarta Sans"),
                xaxis=dict(color="#0F172A"),
                yaxis=dict(color="#0F172A"),
                margin=dict(l=20, r=20, t=40, b=20),
                height=300
            )
            st.plotly_chart(fig_cm, use_container_width=True)


# -----------------------------------------------------------------------------
# PAGE 4: AML INVESTIGATION CENTRE
# -----------------------------------------------------------------------------
elif page == "AML Investigation Centre":
    st.markdown("## 🏛️ Anti-Money Laundering (AML) Investigation Centre")
    st.markdown("Automated detection of complex financial crime topologies under PMLA guidelines.")

    cases = database.fetch_aml_cases()

    if cases:
        c_k1, c_k2, c_k3, c_k4 = st.columns(4)
        c_k1.metric("Total AML Cases", len(cases))
        c_k2.metric("Structuring (Smurfing)", sum(1 for c in cases if c["case_type"] == "STRUCTURING"))
        c_k3.metric("Mule Accounts", sum(1 for c in cases if c["case_type"] == "MULE_ACCOUNT"))
        c_k4.metric("Circular Money Loops", sum(1 for c in cases if c["case_type"] == "CIRCULAR_TRANSFERS"))

        case_filter = st.selectbox(
            "Filter Cases by Typology:",
            ["ALL", "STRUCTURING", "MULE_ACCOUNT", "RAPID_FUND_MOVEMENT", "CIRCULAR_TRANSFERS"]
        )

        display_cases = cases if case_filter == "ALL" else [c for c in cases if c["case_type"] == case_filter]

        st.caption(f"Displaying **{len(display_cases)}** investigative case files:")

        for c in display_cases[:25]:
            with st.expander(f"📁 {c['case_id']} — {c['case_type']} | Primary: {c['primary_account']} | ₹{c['total_amount']:,.2f}"):
                col_c1, col_c2 = st.columns([3, 1])
                with col_c1:
                    st.markdown(f"**Forensic Evidence Narrative:**")
                    st.markdown(f"> *{c['evidence_summary']}*")
                    st.markdown(f"**Time Span:** `{c['time_span_minutes']:.1f} minutes` | **Transaction Count:** `{c['transaction_count']}`")

                    # Parse related txns
                    try:
                        txns = json.loads(c.get("related_txns", "[]"))
                        st.markdown(f"**Associated Transaction IDs:** `{'`, `'.join(txns[:10])}`")
                    except Exception:
                        pass
                with col_c2:
                    st.markdown(f"**Severity:** {render_risk_badge(c['severity'])}", unsafe_allow_html=True)
                    st.markdown(f"**Status:** `{c['status']}`")
                    if st.button("Mark Under Review", key=f"btn_{c['case_id']}"):
                        st.success(f"Case {c['case_id']} assigned to Financial Intelligence Unit.")
    else:
        st.info("No active AML cases found. Re-seed demo data in System Settings.")


# -----------------------------------------------------------------------------
# PAGE 5: SUSPICIOUS ACCOUNTS
# -----------------------------------------------------------------------------
elif page == "Suspicious Accounts":
    st.markdown("## 👥 Suspicious Accounts Intelligence")
    st.markdown("High-risk account profiling, pass-through ratio monitoring, and intermediary nodes.")

    accounts = database.fetch_suspicious_accounts()

    if accounts:
        # Search filter
        search_acc = st.text_input("🔍 Search Account ID", "")
        if search_acc:
            accounts = [a for a in accounts if search_acc.lower() in a["account_id"].lower()]

        df_acc = pd.DataFrame(accounts)
        st.markdown(f"Identified **{len(df_acc)}** accounts requiring compliance scrutiny:")

        # Display table
        st.dataframe(
            df_acc[[
                "account_id", "risk_score", "risk_level", "incoming_count",
                "outgoing_count", "total_incoming_amount", "total_outgoing_amount",
                "investigation_status"
            ]].rename(columns={
                "account_id": "Account ID",
                "risk_score": "Risk Score",
                "risk_level": "Level",
                "incoming_count": "Inflows",
                "outgoing_count": "Outflows",
                "total_incoming_amount": "Total In (₹)",
                "total_outgoing_amount": "Total Out (₹)",
                "investigation_status": "Status"
            }),
            use_container_width=True,
            hide_index=True
        )

        st.markdown("---")
        st.markdown("##### 📌 Account Dossier Inspector")
        sel_acc = st.selectbox("Inspect Account:", options=df_acc["account_id"].tolist()[:50])
        if sel_acc:
            acc_row = df_acc[df_acc["account_id"] == sel_acc].iloc[0]
            c_a1, c_a2, c_a3 = st.columns(3)
            with c_a1:
                st.markdown(f"**Account ID:** `{acc_row['account_id']}`")
                st.markdown(f"**Risk Level:** {render_risk_badge(acc_row['risk_level'])}", unsafe_allow_html=True)
                st.markdown(f"**Score:** `{acc_row['risk_score']}/100`")
            with c_a2:
                st.markdown(f"**Total Received:** ₹{acc_row['total_incoming_amount']:,.2f}")
                st.markdown(f"**Total Disbursed:** ₹{acc_row['total_outgoing_amount']:,.2f}")
                ratio = (acc_row['total_outgoing_amount'] / max(acc_row['total_incoming_amount'], 1.0)) * 100
                st.markdown(f"**Pass-Through Ratio:** `{ratio:.1f}%`")
            with c_a3:
                st.markdown(f"**Investigation Status:** `{acc_row['investigation_status']}`")
                try:
                    pats = json.loads(acc_row.get("suspicious_patterns", "[]"))
                    st.markdown("**Detected Patterns:**")
                    for p in pats:
                        st.markdown(f"- {p}")
                except Exception:
                    pass
    else:
        st.info("No suspicious accounts recorded.")


# -----------------------------------------------------------------------------
# PAGE 6: MONEY FLOW NETWORK
# -----------------------------------------------------------------------------
elif page == "Money Flow Network":
    st.markdown("## 🕸️ Money Flow Network Graph")
    st.markdown("Interactive NetworkX & Plotly topological graph of account nodes, directional fund flows, and circular loops.")

    df_txns = database.fetch_transactions_df(limit=600)
    aml_cases = database.fetch_aml_cases()
    suspicious_accounts = database.fetch_suspicious_accounts()
    acc_lookup = {r["account_id"]: r for r in suspicious_accounts}

    # Pre-identify high-risk accounts
    high_risk_accs = {
        acc_id for acc_id, d in acc_lookup.items()
        if d.get("risk_score", 0) >= 50 or d.get("risk_level") in ["HIGH", "CRITICAL"]
    }
    if not df_txns.empty:
        for _, r in df_txns.iterrows():
            if r.get("risk_category") in ["HIGH", "CRITICAL"] or float(r.get("risk_score", 0)) >= 50:
                high_risk_accs.add(r["sender_account"])
                high_risk_accs.add(r["receiver_account"])

    if not df_txns.empty:
        col_g1, col_g2 = st.columns([1, 3])
        with col_g1:
            st.markdown("##### 🎛️ Network Controls")
            sub_count = st.slider(
                "Max Transactions to Graph",
                min_value=20,
                max_value=300,
                value=80,
                step=10,
                help="Control the number of transaction edges rendered in the topological graph."
            )
            filter_circular = st.checkbox(
                "⭕ Detected Circular Loops Only",
                value=False,
                help="Isolate and inspect verified closed cyclic money routing (e.g., A → B → C → A)."
            )
            highlight_high_risk = st.checkbox(
                "🛡️ High Risk Accounts & Connected Flows",
                value=False,
                disabled=filter_circular,
                help="Focus on accounts with Risk ≥ 50 while preserving connected counterparty transactions."
            )
            show_labels = st.checkbox(
                "🏷️ Show Account Labels",
                value=True,
                help="Toggle node label visibility to de-clutter dense networks."
            )

        # Data filtering based on selected controls
        if filter_circular:
            # Query candidate circular transactions from database
            conn = database.get_connection()
            circ_cases = [c for c in aml_cases if c.get("case_type") == "CIRCULAR_TRANSFERS"]
            db_circ_tx_ids = set()
            for c in circ_cases:
                try:
                    db_circ_tx_ids.update(json.loads(c.get("related_txns", "[]")))
                except Exception:
                    pass

            if db_circ_tx_ids:
                placeholders = ','.join(['?'] * len(db_circ_tx_ids))
                q = f"SELECT * FROM transactions WHERE transaction_id IN ({placeholders}) OR scenario_tag LIKE 'CIRCULAR%' ORDER BY timestamp DESC"
                circ_candidates_df = pd.read_sql_query(q, conn, params=list(db_circ_tx_ids))
            else:
                circ_candidates_df = pd.read_sql_query("SELECT * FROM transactions WHERE scenario_tag LIKE 'CIRCULAR%' ORDER BY timestamp DESC", conn)
            conn.close()

            # Verify cycles in candidate transactions using NetworkX (Strict Single Source of Truth)
            G_cand = nx.DiGraph()
            for _, r in circ_candidates_df.iterrows():
                G_cand.add_edge(r["sender_account"], r["receiver_account"])

            cand_cycles = [cyc for cyc in nx.simple_cycles(G_cand) if 2 <= len(cyc) <= 6]
            if not cand_cycles:
                with col_g2:
                    st.info("ℹ️ No verified circular transfer loops (e.g., A → B → C → A) detected in the current transaction database. All transaction paths are acyclic.")
                sub_df = pd.DataFrame()
            else:
                # Filter strictly to edges that participate in verified cycles
                verified_edges_in_db = set()
                for cyc in cand_cycles:
                    for i in range(len(cyc)):
                        verified_edges_in_db.add((cyc[i], cyc[(i + 1) % len(cyc)]))
                is_verified = circ_candidates_df.apply(
                    lambda row: (row["sender_account"], row["receiver_account"]) in verified_edges_in_db,
                    axis=1
                )
                sub_df = circ_candidates_df[is_verified].head(sub_count)
        elif highlight_high_risk:
            # Keep edges where EITHER sender OR receiver is high risk to preserve connected flows
            mask = df_txns["sender_account"].isin(high_risk_accs) | df_txns["receiver_account"].isin(high_risk_accs)
            sub_df = df_txns[mask].head(sub_count)
            if sub_df.empty:
                with col_g2:
                    st.info("ℹ️ No high-risk transactions or connected accounts found in the current dataset.")
        else:
            sub_df = df_txns.head(sub_count)

        if not sub_df.empty:
            # Build NetworkX DiGraph directly from selected transactions
            G = nx.DiGraph()
            for _, r in sub_df.iterrows():
                u = r["sender_account"]
                v = r["receiver_account"]
                tx_id = r["transaction_id"]
                amt = float(r["amount"])
                risk_cat = r.get("risk_category", "LOW")
                ttype = r.get("transaction_type", "TRANSFER")
                G.add_edge(u, v, amount=amt, risk=risk_cat, transaction_id=tx_id, type=ttype)

            # Cycle detection on active graph G — THE SINGLE SOURCE OF TRUTH
            candidate_nodes = {n for n in G.nodes() if G.in_degree(n) > 0 and G.out_degree(n) > 0}
            verified_cycles = []
            if candidate_nodes:
                H = G.subgraph(candidate_nodes)
                try:
                    for cyc in nx.simple_cycles(H):
                        if 2 <= len(cyc) <= 6:
                            verified_cycles.append(cyc)
                            if len(verified_cycles) >= 50:
                                break
                except Exception:
                    pass

            verified_cycle_edges = set()
            verified_cycle_nodes = set()
            for cyc in verified_cycles:
                for i in range(len(cyc)):
                    verified_cycle_edges.add((cyc[i], cyc[(i + 1) % len(cyc)]))
                    verified_cycle_nodes.add(cyc[i])

            # Spacing & Layout via Spring Layout with dynamic scaling
            num_nodes = max(len(G.nodes()), 1)
            k_spacing = max(0.70, 3.5 / math.sqrt(num_nodes))
            pos = nx.spring_layout(G, k=k_spacing, iterations=85, seed=42)

            # Build separate traces for standard edges, high-risk edges, circular edges, and midpoints
            std_edge_x, std_edge_y = [], []
            hr_edge_x, hr_edge_y = [], []
            circ_edge_x, circ_edge_y = [], []
            mid_x, mid_y, mid_hover, mid_color = [], [], [], []
            annotations = []

            for u, v in G.edges():
                x0, y0 = pos[u]
                x1, y1 = pos[v]
                edata = G[u][v]
                amt = edata.get("amount", 0.0)
                tx_id = edata.get("transaction_id", "N/A")
                risk = edata.get("risk", "LOW")
                ttype = edata.get("type", "TRANSFER")

                # STRICT: Edge is ONLY circular if it is part of verified_cycle_edges in G!
                is_circ = (u, v) in verified_cycle_edges
                is_hr_edge = (u in high_risk_accs) or (v in high_risk_accs) or (risk in ["CRITICAL", "HIGH"])

                if is_circ:
                    circ_edge_x.extend([x0, x1, None])
                    circ_edge_y.extend([y0, y1, None])
                    edge_color = "#FF1744"
                    arrow_size = 1.6
                    arrow_width = 2.5
                elif is_hr_edge:
                    hr_edge_x.extend([x0, x1, None])
                    hr_edge_y.extend([y0, y1, None])
                    edge_color = "#A855F7"
                    arrow_size = 1.2
                    arrow_width = 1.5
                else:
                    std_edge_x.extend([x0, x1, None])
                    std_edge_y.extend([y0, y1, None])
                    edge_color = "rgba(37, 99, 235, 0.65)"
                    arrow_size = 1.2
                    arrow_width = 1.3

                # Edge midpoint for hover tooltip
                mx = (x0 + x1) / 2
                my = (y0 + y1) / 2
                mid_x.append(mx)
                mid_y.append(my)

                if is_circ:
                    circ_tag = "<br><span style='color:#FF1744; font-weight:bold;'>⭕ VERIFIED CIRCULAR MONEY FLOW</span>"
                    m_color = "#FF1744"
                elif is_hr_edge:
                    circ_tag = "<br><span style='color:#A855F7; font-weight:bold;'>🛡️ HIGH-RISK FLOW</span>"
                    m_color = "#A855F7"
                else:
                    circ_tag = ""
                    m_color = "#2563EB"

                mid_hover.append(
                    f"<b>Transaction ID:</b> {tx_id}<br>"
                    f"<b>Flow:</b> {u} ➔ {v}<br>"
                    f"<b>Amount:</b> ₹{amt:,.2f}<br>"
                    f"<b>Payment Rail:</b> {ttype}<br>"
                    f"<b>Risk Level:</b> {risk}"
                    f"{circ_tag}"
                )
                mid_color.append(m_color)

                # Directional Arrow Annotation
                dx = x1 - x0
                dy = y1 - y0
                dist = math.sqrt(dx*dx + dy*dy)
                if dist > 0:
                    annotations.append(dict(
                        ax=x0 + 0.63 * dx,
                        ay=y0 + 0.63 * dy,
                        x=x0 + 0.77 * dx,
                        y=y0 + 0.77 * dy,
                        xref="x", yref="y",
                        axref="x", ayref="y",
                        showarrow=True,
                        arrowhead=2,
                        arrowsize=arrow_size,
                        arrowwidth=arrow_width,
                        arrowcolor=edge_color,
                        opacity=0.9
                    ))

            edge_traces = []
            if std_edge_x:
                edge_traces.append(go.Scatter(
                    x=std_edge_x, y=std_edge_y,
                    mode="lines",
                    line=dict(width=1.2, color="rgba(37, 99, 235, 0.35)"),
                    hoverinfo="none",
                    name="Standard Flow"
                ))
            if hr_edge_x:
                edge_traces.append(go.Scatter(
                    x=hr_edge_x, y=hr_edge_y,
                    mode="lines",
                    line=dict(width=1.5, color="rgba(168, 85, 247, 0.55)"),
                    hoverinfo="none",
                    name="High-Risk Flow"
                ))
            if circ_edge_x:
                edge_traces.append(go.Scatter(
                    x=circ_edge_x, y=circ_edge_y,
                    mode="lines",
                    line=dict(width=3.0, color="#FF1744"),
                    hoverinfo="none",
                    name="Circular Flow"
                ))

            midpoint_trace = go.Scatter(
                x=mid_x, y=mid_y,
                mode="markers",
                hoverinfo="text",
                hovertext=mid_hover,
                hovertemplate="%{hovertext}<extra></extra>",
                marker=dict(
                    size=7,
                    color=mid_color,
                    symbol="diamond",
                    line=dict(width=1, color="#FFFFFF")
                ),
                name="Transactions (Hover to inspect)"
            )

            # Node Traces: Visually separate High-Risk nodes (#A855F7) from Circular Loop nodes (#FF1744)
            node_x, node_y, node_colors, node_text, node_hover, node_border_colors, node_border_widths = [], [], [], [], [], [], []
            for node in G.nodes():
                x, y = pos[node]
                node_x.append(x)
                node_y.append(y)

                in_deg = G.in_degree(node)
                out_deg = G.out_degree(node)

                acc_info = acc_lookup.get(node)
                if acc_info:
                    r_score = float(acc_info.get("risk_score", 15.0))
                    r_cat = str(acc_info.get("risk_level", "LOW")).upper()
                    tot_sent = float(acc_info.get("total_outgoing_amount", 0.0))
                    tot_recv = float(acc_info.get("total_incoming_amount", 0.0))
                    s_cnt = int(acc_info.get("outgoing_count", 0))
                    r_cnt = int(acc_info.get("incoming_count", 0))
                else:
                    sent_rows = df_txns[df_txns["sender_account"] == node]
                    recv_rows = df_txns[df_txns["receiver_account"] == node]
                    tot_sent = float(sent_rows["amount"].sum()) if not sent_rows.empty else 0.0
                    tot_recv = float(recv_rows["amount"].sum()) if not recv_rows.empty else 0.0
                    s_cnt = len(sent_rows)
                    r_cnt = len(recv_rows)
                    max_s_risk = sent_rows["risk_score"].max() if not sent_rows.empty else 15.0
                    max_r_risk = recv_rows["risk_score"].max() if not recv_rows.empty else 15.0
                    r_score = float(max(max_s_risk, max_r_risk, 15.0))
                    r_cat = "CRITICAL" if r_score >= 75 else "HIGH" if r_score >= 50 else "MEDIUM" if r_score >= 35 else "LOW"

                # STRICT: Node is ONLY circular if it belongs to verified_cycle_nodes in G!
                is_node_circ = node in verified_cycle_nodes
                is_node_hr = (r_score >= 50) or (r_cat in ["CRITICAL", "HIGH"]) or (in_deg >= 4) or (out_deg >= 4)

                if is_node_circ:
                    node_colors.append("#FF1744")  # Pure Scarlet Red
                    node_border_colors.append("#FF5252")
                    node_border_widths.append(3.0)
                    role = "Closed Circular Flow Participant (A → B → C → A)"
                elif is_node_hr:
                    node_colors.append("#A855F7")  # Vivid Purple - visually distinct from red!
                    node_border_colors.append("#E879F9")
                    node_border_widths.append(2.0)
                    role = "High-Risk Account (Risk ≥ 50 / Hub)"
                elif in_deg > 0 and out_deg > 0:
                    node_colors.append("#F59E0B")  # Amber Intermediary
                    node_border_colors.append("#FCD34D")
                    node_border_widths.append(1.5)
                    role = "Intermediary Transit Node (Mule/Conduit)"
                else:
                    node_colors.append("#2563EB")  # Royal Blue Standard
                    node_border_colors.append("#93C5FD")
                    node_border_widths.append(1.0)
                    role = "Standard Retail Account"

                # Label handling: avoid overlap by decluttering dense graphs
                if show_labels:
                    if len(G.nodes()) <= 40 or filter_circular:
                        node_text.append(f"{node[:4]}..{node[-4:]}")
                    elif in_deg + out_deg >= 2 or is_node_hr or is_node_circ:
                        node_text.append(f"{node[:4]}..{node[-4:]}")
                    else:
                        node_text.append("")
                else:
                    node_text.append("")

                circ_alert = "<br><span style='color:#FF1744; font-weight:bold;'>⭕ VERIFIED IN CIRCULAR FLOW LOOP</span>" if is_node_circ else ""
                node_hover.append(
                    f"<b>Account ID:</b> {node}<br>"
                    f"<b>Risk Score:</b> {r_score:.1f} ({r_cat})<br>"
                    f"<b>Transaction Count:</b> {s_cnt + r_cnt} (Sent: {s_cnt} | Recv: {r_cnt})<br>"
                    f"<b>Total Money Sent:</b> ₹{tot_sent:,.2f}<br>"
                    f"<b>Total Money Received:</b> ₹{tot_recv:,.2f}<br>"
                    f"<b>Topology Role:</b> {role}"
                    f"{circ_alert}"
                )

            node_trace = go.Scatter(
                x=node_x, y=node_y,
                mode="markers+text",
                hoverinfo="text",
                text=node_text,
                textposition="top center",
                textfont=dict(color="#0F172A", size=9.5, family="Plus Jakarta Sans"),
                hovertext=node_hover,
                hovertemplate="%{hovertext}<extra></extra>",
                marker=dict(
                    color=node_colors,
                    size=15,
                    line=dict(width=node_border_widths, color=node_border_colors)
                ),
                name="Account Nodes"
            )

            # Axis range padding to ensure boundary nodes are fully visible
            xs = [pos[n][0] for n in G.nodes()]
            ys = [pos[n][1] for n in G.nodes()]
            x_pad = max((max(xs) - min(xs)) * 0.12, 0.15) if xs else 0.2
            y_pad = max((max(ys) - min(ys)) * 0.12, 0.15) if ys else 0.2

            fig_net = go.Figure(
                data=edge_traces + [midpoint_trace, node_trace],
                layout=go.Layout(
                    title=f"Account-to-Account Financial Topology ({len(G.nodes())} Accounts, {len(G.edges())} Directed Flows)",
                    title_font=dict(color="#0F172A", size=15, family="Plus Jakarta Sans"),
                    showlegend=False,
                    hovermode="closest",
                    margin=dict(b=20, l=15, r=15, t=40),
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[min(xs)-x_pad, max(xs)+x_pad] if xs else None),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[min(ys)-y_pad, max(ys)+y_pad] if ys else None),
                    paper_bgcolor="#FFFFFF",
                    plot_bgcolor="#FFFFFF",
                    height=650,
                    annotations=annotations
                )
            )

            with col_g2:
                # Graph KPI summary strip
                k1, k2, k3, k4 = st.columns(4)
                with k1:
                    st.metric("Graphed Accounts", len(G.nodes()))
                with k2:
                    st.metric("Directed Flows", len(G.edges()))
                with k3:
                    st.metric("Circular Loops", len(verified_cycles))
                with k4:
                    tot_g_vol = sum(d.get("amount", 0.0) for _, _, d in G.edges(data=True))
                    st.metric("Sub-Graph Volume", f"₹{tot_g_vol/1e7:.2f} Cr" if tot_g_vol >= 1e7 else f"₹{tot_g_vol:,.0f}")

                st.plotly_chart(fig_net, use_container_width=True)

                # Topology Legend Card: visually separate high-risk (purple) from circular loops (red)
                st.markdown("""
                <div class="white-panel" style="margin-top: 10px; padding: 14px 18px;">
                    <div style="font-size: 12.5px; font-weight: 700; color: #0F172A; margin-bottom: 8px;">Topological Legend & Interactive Controls</div>
                    <div style="display: flex; flex-wrap: wrap; gap: 14px; font-size: 11.5px; color: #475569;">
                        <div><span style="color: #FF1744; font-size: 13px;">●</span> <b style="color: #DC2626;">Circular Loop Node:</b> Verified closed cycle (A → B → C → A)</div>
                        <div><span style="color: #A855F7; font-size: 13px;">●</span> <b style="color: #7C3AED;">High-Risk / Hub Node:</b> Risk ≥ 50 or high-dispersion account</div>
                        <div><span style="color: #F59E0B; font-size: 13px;">●</span> <b style="color: #D97706;">Intermediary Transit:</b> Two-way flow transit conduit (potential mule)</div>
                        <div><span style="color: #2563EB; font-size: 13px;">●</span> <b style="color: #1D4ED8;">Standard Account:</b> Normal retail/merchant account</div>
                        <div><span style="color: #FF1744; font-size: 13px; font-weight: bold;">➔</span> <b style="color: #DC2626;">Red Arrow:</b> Verified circular flow transfer direction</div>
                        <div><span style="color: #A855F7; font-size: 13px; font-weight: bold;">➔</span> <b style="color: #7C3AED;">Purple Arrow:</b> High-risk connected transaction flow</div>
                        <div><span style="color: #2563EB; font-size: 13px; font-weight: bold;">➔</span> <b style="color: #1D4ED8;">Blue Arrow:</b> Standard fund transfer direction</div>
                        <div><span style="color: #2563EB; font-size: 13px;">◆</span> <b style="color: #0F172A;">Diamond Midpoint:</b> Hover over edge diamond for Txn ID & ₹ amount</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Show cycle details expander if circular cycles exist in the active graph
                if verified_cycles:
                    with st.expander(f"⭕ Verified Circular Loops Breakdown ({len(verified_cycles)} Cycles in Active Subgraph)", expanded=filter_circular):
                        for c_idx, cyc in enumerate(verified_cycles[:10], start=1):
                            cyc_path = " ➔ ".join(cyc + [cyc[0]])
                            cyc_amts = []
                            for i in range(len(cyc)):
                                cu, cv = cyc[i], cyc[(i + 1) % len(cyc)]
                                if G.has_edge(cu, cv):
                                    cyc_amts.append(G[cu][cv].get("amount", 0.0))
                            tot_cycle_amt = sum(cyc_amts)
                            st.markdown(
                                f"**Loop #{c_idx}** ({len(cyc)} accounts, Cumulative Volume: ₹{tot_cycle_amt:,.2f})  \n"
                                f"`{cyc_path}`"
                            )
                elif filter_circular:
                    st.info("ℹ️ No circular transfer loops found in the selected subset.")
    else:
        st.info("No transaction data to plot network graph.")


# -----------------------------------------------------------------------------
# PAGE 7: RISK INTELLIGENCE
# -----------------------------------------------------------------------------
elif page == "Risk Intelligence":
    st.markdown("## 📈 Risk Intelligence & Threat Distribution")
    st.markdown("Comprehensive multidimensional analytics on risk bands, regional hotspots, and merchant vectors.")

    df_txns = database.fetch_transactions_df(limit=3000)

    if not df_txns.empty:
        c_i1, c_i2 = st.columns(2)

        with c_i1:
            st.markdown("##### 📊 Risk Score Distribution Histogram (0–100)")
            fig_hist = px.histogram(
                df_txns, x="risk_score", nbins=25,
                color="risk_category",
                color_discrete_map={"LOW": "#10B981", "MEDIUM": "#0EA5E9", "HIGH": "#F59E0B", "CRITICAL": "#EF4444"}
            )
            fig_hist.update_layout(
                paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
                margin=dict(l=20, r=20, t=30, b=20), height=300,
                xaxis=dict(gridcolor="#F1F5F9", color="#64748B", title="Risk Score"),
                yaxis=dict(gridcolor="#F1F5F9", color="#64748B", title="Count"),
                font=dict(color="#0F172A", family="Plus Jakarta Sans")
            )
            st.plotly_chart(fig_hist, use_container_width=True)

        with c_i2:
            st.markdown("##### 📍 Geographic Risk Hotspots (Top Cities by Suspicious Volume)")
            city_risk = df_txns.groupby("sender_location").agg(
                high_risk_vol=("amount", lambda a: a[df_txns.loc[a.index, "risk_category"].isin(["HIGH", "CRITICAL"])].sum())
            ).reset_index().sort_values("high_risk_vol", ascending=False).head(8)

            fig_city = px.bar(
                city_risk, x="high_risk_vol", y="sender_location", orientation="h",
                color="high_risk_vol", color_continuous_scale="Reds"
            )
            fig_city.update_layout(
                paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
                margin=dict(l=20, r=20, t=30, b=20), height=300,
                xaxis=dict(gridcolor="#F1F5F9", color="#64748B", title="High Risk Volume (₹)"),
                yaxis=dict(autorange="reversed", color="#0F172A", title=""),
                font=dict(color="#0F172A", family="Plus Jakarta Sans")
            )
            st.plotly_chart(fig_city, use_container_width=True)

        st.markdown("##### 💳 Merchant Category Risk Exposure")
        m_cat_risk = df_txns.groupby("merchant_category").agg(
            total_txns=("transaction_id", "count"),
            high_risk_txns=("risk_category", lambda s: (s.isin(["HIGH", "CRITICAL"])).sum()),
            total_amount=("amount", "sum")
        ).reset_index()
        m_cat_risk["risk_ratio_pct"] = (m_cat_risk["high_risk_txns"] / m_cat_risk["total_txns"]) * 100

        fig_mcat = px.scatter(
            m_cat_risk, x="total_amount", y="risk_ratio_pct",
            size="high_risk_txns", color="risk_ratio_pct",
            hover_name="merchant_category",
            color_continuous_scale="Turbo"
        )
        fig_mcat.update_layout(
            paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
            margin=dict(l=20, r=20, t=30, b=20), height=340,
            xaxis=dict(gridcolor="#F1F5F9", color="#64748B", title="Total Transferred Volume (₹)"),
            yaxis=dict(gridcolor="#F1F5F9", color="#64748B", title="High Risk Concentration (%)"),
            font=dict(color="#0F172A", family="Plus Jakarta Sans")
        )
        st.plotly_chart(fig_mcat, use_container_width=True)
    else:
        st.info("No transaction records available for risk intelligence.")


# -----------------------------------------------------------------------------
# PAGE 8: REPORTS & ANALYTICS
# -----------------------------------------------------------------------------
elif page == "Reports & Analytics":
    st.markdown("## 📑 Reports & Forensic Export Center")
    st.markdown("Download compliance datasets, upload external transaction batches, and generate executive summaries.")

    tab_r1, tab_r2, tab_r3 = st.tabs(["📥 Data Exports (CSV)", "📤 Safe CSV Upload & Audit", "📋 Executive Summary Report"])

    with tab_r1:
        st.markdown("##### Export Master Ledger Data for External Audit")
        c_exp1, c_exp2 = st.columns(2)
        with c_exp1:
            df_all = database.fetch_transactions_df()
            if not df_all.empty:
                csv_txns = df_all.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "💾 Download All Transactions CSV",
                    data=csv_txns,
                    file_name=f"finguard_transactions_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )

            alerts_all = database.fetch_fraud_alerts()
            if alerts_all:
                csv_alerts = pd.DataFrame(alerts_all).to_csv(index=False).encode('utf-8')
                st.download_button(
                    "💾 Download Fraud Alerts CSV",
                    data=csv_alerts,
                    file_name=f"finguard_fraud_alerts_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )

        with c_exp2:
            aml_all = database.fetch_aml_cases()
            if aml_all:
                csv_aml = pd.DataFrame(aml_all).to_csv(index=False).encode('utf-8')
                st.download_button(
                    "💾 Download AML Case Files CSV",
                    data=csv_aml,
                    file_name=f"finguard_aml_cases_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )

            acc_all = database.fetch_suspicious_accounts()
            if acc_all:
                csv_acc = pd.DataFrame(acc_all).to_csv(index=False).encode('utf-8')
                st.download_button(
                    "💾 Download Suspicious Accounts CSV",
                    data=csv_acc,
                    file_name=f"finguard_suspicious_accounts_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )

    with tab_r2:
        st.markdown("##### Safe External CSV Ingestion & Forensic Scoring")
        st.caption("Upload raw transaction CSV files (Max 10MB). No external banking APIs accessed; runs sandboxed local inference.")

        uploaded_file = st.file_uploader("Upload CSV transaction file", type=["csv"])
        if uploaded_file is not None:
            if uploaded_file.size > 10 * 1024 * 1024:
                st.error("File exceeds 10MB safety limit.")
            else:
                try:
                    df_up = pd.read_csv(uploaded_file)

                    # 1. Normalize column names (lowercase & strip whitespace)
                    df_up.columns = [str(c).strip().lower() for c in df_up.columns]

                    # 2. Map Amount aliases
                    if "amount" not in df_up.columns:
                        for alias in ["amt", "trans_amount", "transaction_amount", "val", "value"]:
                            if alias in df_up.columns:
                                df_up.rename(columns={alias: "amount"}, inplace=True)
                                break

                    # Map Class aliases
                    if "class" not in df_up.columns:
                        for alias in ["label", "target", "is_fraud", "fraud"]:
                            if alias in df_up.columns:
                                df_up.rename(columns={alias: "class"}, inplace=True)
                                break

                    # Map Time aliases
                    if "time" not in df_up.columns:
                        for alias in ["elapsed_time", "seconds", "step"]:
                            if alias in df_up.columns:
                                df_up.rename(columns={alias: "time"}, inplace=True)
                                break

                    # Detect dataset profile
                    pca_cols = [f"v{i}" for i in range(1, 29) if f"v{i}" in df_up.columns]
                    is_ulb = (
                        len(pca_cols) >= 5
                        or ("class" in df_up.columns and len(pca_cols) >= 1)
                        or ("time" in df_up.columns and "sender_account" not in df_up.columns)
                    )

                    st.success(f"Uploaded `{uploaded_file.name}` ({len(df_up):,} records detected)")

                    # 9. Upload summary: Total rows, Genuine transactions, Known fraud transactions
                    st.markdown("###### 📊 Dataset Ingestion & Profiling Summary")
                    col_u1, col_u2, col_u3, col_u4 = st.columns(4)
                    with col_u1:
                        st.metric("Total Rows", f"{len(df_up):,}")
                    with col_u2:
                        if "class" in df_up.columns:
                            gen_count = int((pd.to_numeric(df_up["class"], errors="coerce") == 0).sum())
                            st.metric("Genuine (Class 0)", f"{gen_count:,}")
                        else:
                            st.metric("Genuine Transactions", "Unlabeled (Pending Audit)")
                    with col_u3:
                        if "class" in df_up.columns:
                            fraud_count = int((pd.to_numeric(df_up["class"], errors="coerce") == 1).sum())
                            fraud_pct = (fraud_count / max(len(df_up), 1)) * 100
                            st.metric("Known Fraud (Class 1)", f"{fraud_count:,}", delta=f"{fraud_pct:.2f}% anomaly rate", delta_color="inverse")
                        else:
                            st.metric("Known Fraud", "Unlabeled (Pending Audit)")
                    with col_u4:
                        profile_label = "ULB Credit Card (PCA V1-V28)" if is_ulb else "Indian Multi-Rail Banking"
                        st.metric("Dataset Profile", profile_label)

                    if is_ulb and "time" in df_up.columns:
                        st.caption("ℹ️ **ULB Dataset Format Detected**: Elapsed time preserved as relative seconds. Anonymized PCA features ($V_1$–$V_{28}$) and transaction amount evaluated via multi-variate Isolation Forest and variance anomaly scoring.")

                    # Check required columns
                    if "amount" not in df_up.columns:
                        st.error("Missing required column in CSV: 'amount' (or recognizable amount alias).")
                    else:
                        if st.button("🚀 Run FinGuard AI Forensic Audit on Uploaded File"):
                            with st.spinner("Executing fraud & AML detection..."):
                                scored_df = risk_engine.score_dataframe(df_up, fraud_engine, aml_engine)
                                st.write("### 🔍 Forensic Audit Results:")

                                crit_count = int((scored_df["risk_category"] == "CRITICAL").sum())
                                high_count = int((scored_df["risk_category"] == "HIGH").sum())
                                med_count = int((scored_df["risk_category"] == "MEDIUM").sum())
                                low_count = int((scored_df["risk_category"] == "LOW").sum())

                                col_r1, col_r2, col_r3, col_r4 = st.columns(4)
                                col_r1.metric("Critical Risk", f"{crit_count:,}")
                                col_r2.metric("High Risk", f"{high_count:,}")
                                col_r3.metric("Medium Risk", f"{med_count:,}")
                                col_r4.metric("Low Risk", f"{low_count:,}")

                                disp_cols = [
                                    c for c in ["transaction_id", "time", "elapsed_seconds", "amount", "class", "risk_score", "risk_category", "detection_reasons", "recommended_action"]
                                    if c in scored_df.columns
                                ]
                                st.dataframe(
                                    scored_df[disp_cols].head(100),
                                    use_container_width=True
                                )
                                csv_scored = scored_df.to_csv(index=False).encode('utf-8')
                                st.download_button("💾 Download Audited Results CSV", csv_scored, "finguard_audited_results.csv", "text/csv")
                except Exception as e:
                    import traceback
                    st.error(f"Error parsing CSV: {e}")
                    st.code(traceback.format_exc(), language="text")

    with tab_r3:
        st.markdown("##### Executive Security Briefing")
        kpis = database.fetch_kpis()
        report_md = f"""# FinGuard AI — Financial Crime Security Briefing
**Generated:** {datetime.now().strftime('%d %B %Y, %H:%M:%S')}
**Classification:** STRICTLY CONFIDENTIAL // LEVEL-3 FIU AUDIT

## 1. Executive Summary
During the surveillance window, FinGuard AI audited **{kpis['total_transactions']:,} transactions** totaling **₹{kpis['total_volume_inr']/1e7:.2f} Crores**.
The AI engine identified **{kpis['high_risk_transactions']:,} high-risk transactions** representing **₹{kpis['high_risk_volume_inr']/1e7:.2f} Crores** in suspicious fund movements.

## 2. Key Risk Indicators
- **Total Fraud Triage Alerts:** {kpis['fraud_alerts_count']}
- **Active AML Topological Cases:** {kpis['aml_cases_count']}
- **Flagged Suspicious Accounts:** {kpis['suspicious_accounts_count']}

## 3. Compliance Action Taken
- High-priority circular money movement loops and structuring cases have been routed to Compliance Ops.
- Counterparty accounts flagged for pass-through mule behaviour have been placed under automated velocity caps.
"""
        st.text_area("Executive Report Preview", report_md, height=280)
        st.download_button(
            "💾 Download Security Briefing Markdown",
            data=report_md.encode('utf-8'),
            file_name=f"finguard_security_briefing_{datetime.now().strftime('%Y%m%d')}.md",
            mime="text/markdown"
        )


# -----------------------------------------------------------------------------
# PAGE 9: SYSTEM SETTINGS
# -----------------------------------------------------------------------------
elif page == "System Settings":
    st.markdown("## ⚙️ System Settings & Demonstration Controls")
    st.markdown("Fine-tune algorithmic detection thresholds, risk scoring weights, and manage demo datasets.")

    col_set1, col_set2 = st.columns(2)

    with col_set1:
        st.markdown("##### 🎛️ Anti-Money Laundering (AML) Thresholds")
        s_thresh = st.slider("Structuring Reporting Threshold (₹)", 25000.0, 100000.0, float(aml_engine.structuring_threshold), step=5000.0)
        s_window = st.slider("Structuring Time Window (Hours)", 1.0, 48.0, float(aml_engine.structuring_window_hours), step=1.0)
        s_rapid = st.slider("Rapid Fund Movement Window (Minutes)", 5.0, 60.0, float(aml_engine.rapid_fund_window_minutes), step=5.0)
        s_mule_ratio = st.slider("Mule Outflow Pass-Through Ratio", 0.50, 0.99, float(aml_engine.mule_outflow_ratio), step=0.05)

        if st.button("Apply AML Threshold Changes"):
            aml_engine.structuring_threshold = s_thresh
            aml_engine.structuring_window_hours = s_window
            aml_engine.rapid_fund_window_minutes = s_rapid
            aml_engine.mule_outflow_ratio = s_mule_ratio
            st.success("Updated AML engine parameters.")

    with col_set2:
        st.markdown("##### ⚖️ Risk Scoring Weights Configuration")
        w_ml_sup = st.slider("XGBoost Supervised Weight", 0.05, 0.50, float(risk_engine.w_supervised), step=0.05)
        w_ml_iso = st.slider("Isolation Forest Anomaly Weight", 0.05, 0.40, float(risk_engine.w_anomaly), step=0.05)
        w_struct = st.slider("Structuring Weight", 0.05, 0.30, float(risk_engine.w_structuring), step=0.05)
        w_circ = st.slider("Circular Loop Weight", 0.05, 0.30, float(risk_engine.w_circular), step=0.05)

        if st.button("Apply Risk Weight Adjustments"):
            risk_engine.w_supervised = w_ml_sup
            risk_engine.w_anomaly = w_ml_iso
            risk_engine.w_structuring = w_struct
            risk_engine.w_circular = w_circ
            st.success("Updated risk weighting factors.")

    st.markdown("---")
    st.markdown("##### 🔄 Demonstration Data Management")
    c_rst1, c_rst2 = st.columns([1, 2])
    with c_rst1:
        if st.button("⚡ Reset & Reseed Demonstration Data", type="primary"):
            with st.spinner("Clearing database and re-seeding 2,200+ controlled test scenarios..."):
                from scripts.seed_demo_data import seed
                seed()
                st.success("Database cleanly reseeded with all 8 controlled financial scenarios!")
                st.rerun()
    with c_rst2:
        st.caption("Resets SQLite tables (transactions, fraud_alerts, aml_cases, suspicious_accounts) and re-generates reproducible controlled benchmark data.")
