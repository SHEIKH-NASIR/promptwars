"""
dashboard/styles.py - FinGuard AI Premium Futuristic UI Design System
Matches the Executive Intelligence Command Center visual reference:
- Light Theme: Warm ivory & alabaster pearl background (#F8F7F4 / #FAF9F6)
- Deep Navy Translucent Glass Sidebar (#070D1D to #0B172E)
- Royal Blue (#1D6AE5 / #2563EB) and Cobalt accents
- Champagne Gold (#D4AF37) subtle accents
- Soft Emerald/Teal (#10B981) positive indicators
- Muted Coral/Red (#EF4444) fraud indicators
- Clean glassmorphic cards with delicate shadows (border-radius: 18px)
- Fully backward-compatible helper functions
"""

import html
from typing import Dict, Any, List, Optional
from dashboard.assets import LOGO_B64, HERO_SHIELD_B64, SIDEBAR_GLOBE_B64, SHIELD_WATERMARK_B64

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Playfair+Display:ital,wght@1,500;1,600;1,700&display=swap');

/* =========================================================================
   1. GLOBAL APP BACKGROUND & TYPOGRAPHY (LIGHT THEME)
   ========================================================================= */
.stApp {
    background-color: #F8F7F4 !important;
    color: #0F172A !important;
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
}

/* Main Container Spacing */
.main .block-container {
    padding-top: 1.0rem !important;
    padding-bottom: 2.5rem !important;
    padding-left: 2.2rem !important;
    padding-right: 2.2rem !important;
    max-width: 98% !important;
}

/* Global Headings */
h1, h2, h3, h4, h5, h6 {
    color: #0F172A !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: -0.3px !important;
}

p, span, label {
    color: #334155;
    font-family: 'Plus Jakarta Sans', sans-serif;
}

/* =========================================================================
   2. SIDEBAR STYLING (DEEP NAVY TRANSLUCENT GLASS)
   ========================================================================= */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #070D1D 0%, #0A1326 50%, #0B172E 100%) !important;
    border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
    box-shadow: 4px 0 24px rgba(0, 0, 0, 0.15) !important;
}

section[data-testid="stSidebar"] .block-container {
    padding-top: 1.2rem !important;
    padding-left: 1.0rem !important;
    padding-right: 1.0rem !important;
}

section[data-testid="stSidebar"] h1, 
section[data-testid="stSidebar"] h2, 
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] h4,
section[data-testid="stSidebar"] h5 {
    color: #F8FAFC !important;
}

section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label {
    color: #94A3B8 !important;
}

/* Sidebar Brand Header */
.sidebar-brand-box {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 8px 18px 8px;
    margin-bottom: 12px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}
.sidebar-brand-logo {
    width: 36px;
    height: 36px;
    border-radius: 10px;
    object-fit: contain;
    box-shadow: 0 0 16px rgba(0, 229, 255, 0.4);
}
.sidebar-brand-title {
    font-size: 19px;
    font-weight: 800;
    color: #FFFFFF !important;
    letter-spacing: -0.2px;
    line-height: 1.1;
    margin: 0;
}
.sidebar-brand-sub {
    font-size: 10.5px;
    color: #8E9CAE !important;
    letter-spacing: 0.2px;
    margin-top: 3px;
    font-weight: 500;
}

/* Custom Navigation Radio Styling matching Reference Image */
section[data-testid="stSidebar"] div[role="radiogroup"] {
    gap: 4px !important;
    padding: 0 !important;
}

section[data-testid="stSidebar"] div[role="radiogroup"] > label {
    background: transparent !important;
    border: 1px solid transparent !important;
    border-radius: 12px !important;
    padding: 9px 14px !important;
    color: #94A3B8 !important;
    font-size: 13.5px !important;
    font-weight: 500 !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    cursor: pointer !important;
    display: flex !important;
    align-items: center !important;
    margin-bottom: 3px !important;
}

section[data-testid="stSidebar"] div[role="radiogroup"] > label:hover {
    background: rgba(255, 255, 255, 0.06) !important;
    color: #FFFFFF !important;
    transform: translateX(3px);
}

/* Active Navigation Item */
section[data-testid="stSidebar"] div[role="radiogroup"] > label[data-checked="true"],
section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) {
    background: linear-gradient(90deg, #1D6AE5 0%, #2575FC 100%) !important;
    color: #FFFFFF !important;
    font-weight: 700 !important;
    border: 1px solid rgba(0, 229, 255, 0.35) !important;
    box-shadow: 0 4px 18px rgba(29, 106, 229, 0.4) !important;
}

/* Hide Radio Dot */
section[data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child {
    display: none !important;
}

/* Sidebar Monitoring Status Card */
.sidebar-monitoring-card {
    background: rgba(14, 25, 48, 0.85);
    border: 1px solid rgba(0, 229, 255, 0.25);
    border-radius: 14px;
    padding: 12px 14px;
    margin-top: 15px;
    margin-bottom: 15px;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);
}
.sidebar-mon-header {
    display: flex;
    align-items: center;
    gap: 7px;
    font-size: 12px;
    font-weight: 700;
    color: #00E5FF;
    letter-spacing: 0.3px;
}
.sidebar-mon-sub {
    font-size: 11px;
    color: #94A3B8;
    margin-top: 2px;
}
.sidebar-globe-container {
    text-align: center;
    padding: 10px 0;
}
.sidebar-globe-img {
    width: 130px;
    height: auto;
    border-radius: 50%;
    filter: drop-shadow(0 0 15px rgba(0, 229, 255, 0.3));
}
.sidebar-tagline {
    font-size: 11px;
    color: #8E9CAE;
    letter-spacing: 0.5px;
    text-align: center;
    margin-top: 6px;
    font-weight: 500;
}

/* =========================================================================
   3. TOP NAVIGATION HEADER (SEARCH & USER PROFILE)
   ========================================================================= */
.top-header-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    padding: 0 2px;
}
.top-search-box {
    display: flex;
    align-items: center;
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 28px;
    padding: 8px 18px;
    box-shadow: 0 2px 8px rgba(15, 23, 42, 0.03);
    width: 420px;
    transition: all 0.2s ease;
}
.top-search-box:focus-within {
    border-color: #2563EB;
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12);
}
.top-search-input {
    border: none;
    outline: none;
    background: transparent;
    font-size: 13px;
    color: #334155;
    width: 100%;
    margin-left: 8px;
    font-family: inherit;
}
.top-search-shortcut {
    font-size: 11px;
    color: #94A3B8;
    background: #F1F5F9;
    padding: 2px 8px;
    border-radius: 12px;
    font-weight: 600;
    white-space: nowrap;
}
.top-user-area {
    display: flex;
    align-items: center;
    gap: 16px;
}
.top-notify-btn {
    position: relative;
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    width: 38px;
    height: 38px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.02);
}
.top-notify-badge {
    position: absolute;
    top: -2px;
    right: -2px;
    background: #EF4444;
    color: #FFFFFF;
    font-size: 10px;
    font-weight: 800;
    width: 16px;
    height: 16px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 2px solid #FFFFFF;
}
.top-user-pill {
    display: flex;
    align-items: center;
    gap: 9px;
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 24px;
    padding: 4px 14px 4px 5px;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.02);
    cursor: pointer;
}
.top-user-avatar {
    width: 30px;
    height: 30px;
    border-radius: 50%;
    background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
    color: #FFFFFF;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    font-weight: 700;
}
.top-user-name {
    font-size: 13px;
    font-weight: 600;
    color: #0F172A;
}

/* =========================================================================
   4. HERO BANNER COMMAND CENTER SECTION
   ========================================================================= */
.hero-banner-container {
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.98) 0%, rgba(254, 252, 248, 0.95) 100%);
    border: 1px solid rgba(226, 232, 240, 0.9);
    border-radius: 20px;
    padding: 24px 28px;
    margin-bottom: 22px;
    box-shadow: 0 10px 30px -5px rgba(15, 23, 42, 0.04), 0 2px 6px -1px rgba(15, 23, 42, 0.02);
    display: flex;
    justify-content: space-between;
    align-items: center;
    position: relative;
    overflow: hidden;
}
.hero-banner-container::before {
    content: '';
    position: absolute;
    top: 0;
    right: 0;
    width: 480px;
    height: 100%;
    background: radial-gradient(circle at 80% 50%, rgba(212, 175, 55, 0.06), transparent 70%);
    pointer-events: none;
}
.hero-left {
    max-width: 58%;
    z-index: 2;
}
.hero-welcome-sub {
    font-size: 14px;
    color: #64748B;
    margin-bottom: 3px;
    font-weight: 500;
}
.hero-welcome-name {
    font-size: 29px;
    font-weight: 800;
    color: #0F172A;
    letter-spacing: -0.5px;
    margin-bottom: 6px;
    line-height: 1.15;
}
.hero-welcome-desc {
    font-size: 14px;
    color: #475569;
    margin-bottom: 14px;
}
.hero-meta-row {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
}
.hero-badge-live {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #ECFDF5;
    border: 1px solid #A7F3D0;
    color: #059669;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 11.5px;
    font-weight: 700;
    letter-spacing: 0.3px;
}
.hero-badge-time {
    font-size: 11.5px;
    color: #64748B;
    font-weight: 500;
}
.hero-right {
    display: flex;
    align-items: center;
    gap: 20px;
    z-index: 2;
}
.hero-slogan {
    font-family: 'Playfair Display', Georgia, serif;
    font-style: italic;
    font-size: 21px;
    font-weight: 600;
    color: #1E3A8A;
    letter-spacing: 0.3px;
    white-space: nowrap;
}
.hero-shield-img {
    height: 130px;
    width: auto;
    object-fit: contain;
    filter: drop-shadow(0 12px 25px rgba(29, 106, 229, 0.25));
    border-radius: 12px;
}

/* =========================================================================
   5. PREMIUM WHITE KPI METRIC CARDS WITH SPARKLINES
   ========================================================================= */
.premium-kpi-card {
    background: #FFFFFF;
    border: 1px solid rgba(226, 232, 240, 0.95);
    border-radius: 18px;
    padding: 18px 20px 14px 20px;
    box-shadow: 0 8px 25px -4px rgba(15, 23, 42, 0.04), 0 2px 6px -1px rgba(15, 23, 42, 0.02);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    margin-bottom: 18px;
    position: relative;
    overflow: hidden;
}
.premium-kpi-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 14px 30px -4px rgba(15, 23, 42, 0.08);
}
.kpi-top-row {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 10px;
}
.kpi-icon-circle {
    width: 38px;
    height: 38px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 17px;
    flex-shrink: 0;
}
.kpi-label-text {
    font-size: 13px;
    font-weight: 600;
    color: #64748B;
    line-height: 1.2;
}
.kpi-val-row {
    display: flex;
    align-items: baseline;
    gap: 10px;
    margin-bottom: 6px;
}
.kpi-main-number {
    font-size: 27px;
    font-weight: 800;
    color: #0F172A;
    letter-spacing: -0.6px;
    line-height: 1.1;
}
.kpi-delta-tag {
    font-size: 12px;
    font-weight: 700;
    display: inline-flex;
    align-items: center;
    gap: 2px;
}
.kpi-sparkline-box {
    margin-top: 4px;
    margin-bottom: 4px;
}
.kpi-breakdown-row {
    margin-top: 8px;
    padding-top: 6px;
    border-top: 1px solid #F1F5F9;
    font-size: 11px;
    color: #64748B;
}

/* =========================================================================
   6. WHITE DASHBOARD PANELS & CARDS
   ========================================================================= */
.white-panel {
    background: #FFFFFF;
    border: 1px solid rgba(226, 232, 240, 0.95);
    border-radius: 18px;
    padding: 20px 22px;
    box-shadow: 0 8px 25px -4px rgba(15, 23, 42, 0.04), 0 2px 6px -1px rgba(15, 23, 42, 0.02);
    margin-bottom: 20px;
    height: 100%;
}
.panel-header-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
}
.panel-title-text {
    font-size: 15.5px;
    font-weight: 700;
    color: #0F172A;
    display: flex;
    align-items: center;
    gap: 8px;
}
.panel-action-link {
    font-size: 12.5px;
    font-weight: 600;
    color: #2563EB;
    cursor: pointer;
    text-decoration: none;
    transition: color 0.15s;
}
.panel-action-link:hover {
    color: #1D4ED8;
    text-decoration: underline;
}

/* Time Filter Pill Buttons */
.time-filter-group {
    display: inline-flex;
    background: #F1F5F9;
    padding: 3px;
    border-radius: 20px;
    gap: 3px;
}
.time-pill-btn {
    border: none;
    background: transparent;
    padding: 4px 11px;
    border-radius: 16px;
    font-size: 11.5px;
    font-weight: 600;
    color: #64748B;
    cursor: pointer;
    transition: all 0.15s;
}
.time-pill-btn.active {
    background: #2563EB;
    color: #FFFFFF;
    box-shadow: 0 2px 6px rgba(37, 99, 235, 0.3);
}

/* Recent Alerts List Items */
.alert-list-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 12px;
    border-radius: 12px;
    background: #F8FAFC;
    border: 1px solid #F1F5F9;
    margin-bottom: 9px;
    transition: background 0.15s;
}
.alert-list-item:hover {
    background: #F1F5F9;
}
.alert-left-col {
    display: flex;
    align-items: center;
    gap: 11px;
}
.alert-icon-wrap {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    font-weight: 800;
    flex-shrink: 0;
}
.alert-title-main {
    font-size: 13px;
    font-weight: 700;
    color: #0F172A;
    line-height: 1.2;
}
.alert-sub-meta {
    font-size: 11.5px;
    color: #64748B;
    margin-top: 2px;
}

/* AI Analysis Card */
.ai-analysis-panel {
    background: linear-gradient(135deg, #FFFFFF 0%, #F8FAFC 100%);
    border: 1px solid rgba(226, 232, 240, 0.95);
    border-radius: 18px;
    padding: 22px;
    box-shadow: 0 8px 25px -4px rgba(15, 23, 42, 0.04);
    position: relative;
    overflow: hidden;
    height: 100%;
}
.ai-watermark-shield {
    position: absolute;
    right: 14px;
    bottom: 12px;
    width: 90px;
    height: auto;
    opacity: 0.9;
    pointer-events: none;
    filter: drop-shadow(0 8px 20px rgba(37, 99, 235, 0.2));
}

/* =========================================================================
   7. RISK BADGES & STATUS PILLS
   ========================================================================= */
.badge-critical {
    background-color: #FEF2F2 !important;
    color: #DC2626 !important;
    border: 1px solid #FECACA !important;
    padding: 3px 9px !important;
    border-radius: 6px !important;
    font-weight: 700 !important;
    font-size: 11px !important;
    display: inline-block !important;
    letter-spacing: 0.3px !important;
}
.badge-high {
    background-color: #FFF7ED !important;
    color: #EA580C !important;
    border: 1px solid #FED7AA !important;
    padding: 3px 9px !important;
    border-radius: 6px !important;
    font-weight: 700 !important;
    font-size: 11px !important;
    display: inline-block !important;
    letter-spacing: 0.3px !important;
}
.badge-medium {
    background-color: #FEFCE8 !important;
    color: #CA8A04 !important;
    border: 1px solid #FEF08A !important;
    padding: 3px 9px !important;
    border-radius: 6px !important;
    font-weight: 700 !important;
    font-size: 11px !important;
    display: inline-block !important;
    letter-spacing: 0.3px !important;
}
.badge-low {
    background-color: #ECFDF5 !important;
    color: #059669 !important;
    border: 1px solid #A7F3D0 !important;
    padding: 3px 9px !important;
    border-radius: 6px !important;
    font-weight: 700 !important;
    font-size: 11px !important;
    display: inline-block !important;
    letter-spacing: 0.3px !important;
}

/* =========================================================================
   8. STREAMLIT COMPONENT REFINEMENTS (LIGHT THEME)
   ========================================================================= */
.stButton > button {
    background: linear-gradient(90deg, #1D6AE5 0%, #2575FC 100%) !important;
    color: #FFFFFF !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 8px 20px !important;
    box-shadow: 0 4px 14px rgba(29, 106, 229, 0.3) !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(29, 106, 229, 0.45) !important;
}

/* Streamlit Dataframe in Light Theme */
.stDataFrame, div[data-testid="stDataFrame"] {
    background-color: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 12px !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02) !important;
}

/* Streamlit Expanders in Light Theme */
div[data-testid="stExpander"] {
    background-color: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 14px !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02) !important;
    margin-bottom: 10px !important;
}
div[data-testid="stExpander"] summary {
    color: #0F172A !important;
    font-weight: 600 !important;
    font-size: 13.5px !important;
}
div[data-testid="stExpander"] summary:hover {
    color: #2563EB !important;
}

/* Streamlit Tabs in Light Theme */
.stTabs [data-baseweb="tab-list"] {
    background-color: #F1F5F9 !important;
    border-radius: 14px !important;
    padding: 4px !important;
    gap: 4px !important;
    border: 1px solid #E2E8F0 !important;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 10px !important;
    color: #64748B !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    padding: 8px 18px !important;
    border: none !important;
    background: transparent !important;
}
.stTabs [aria-selected="true"] {
    background-color: #FFFFFF !important;
    color: #2563EB !important;
    font-weight: 700 !important;
    box-shadow: 0 2px 8px rgba(37, 99, 235, 0.12) !important;
}

/* Streamlit Metric Containers in Light Theme */
div[data-testid="stMetric"] {
    background-color: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 14px !important;
    padding: 14px 18px !important;
    box-shadow: 0 4px 16px -2px rgba(15, 23, 42, 0.03) !important;
}
div[data-testid="stMetricLabel"] {
    color: #64748B !important;
    font-weight: 600 !important;
    font-size: 12px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
}
div[data-testid="stMetricValue"] {
    color: #0F172A !important;
    font-weight: 800 !important;
    font-size: 24px !important;
    letter-spacing: -0.5px !important;
}

/* Streamlit Inputs & Selectboxes in Light Theme */
.stTextInput input, .stNumberInput input, div[data-baseweb="select"] > div {
    background-color: #FFFFFF !important;
    color: #0F172A !important;
    border: 1px solid #CBD5E1 !important;
    border-radius: 10px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.02) !important;
}
.stTextInput input:focus, .stNumberInput input:focus, div[data-baseweb="select"] > div:focus {
    border-color: #2563EB !important;
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12) !important;
}
div[data-baseweb="popover"], div[data-baseweb="menu"] {
    background-color: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    box-shadow: 0 10px 25px rgba(0,0,0,0.08) !important;
    border-radius: 10px !important;
}
div[data-baseweb="menu"] li {
    color: #0F172A !important;
}

/* Streamlit Slider in Light Theme */
.stSlider {
    color: #2563EB !important;
}

/* Streamlit Text Area in Light Theme */
.stTextArea textarea {
    background-color: #FFFFFF !important;
    color: #0F172A !important;
    border: 1px solid #CBD5E1 !important;
    border-radius: 12px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.02) !important;
    font-family: inherit !important;
}
.stTextArea textarea:focus {
    border-color: #2563EB !important;
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12) !important;
}

/* Streamlit Alerts / Info / Warning / Success Boxes */
div[data-testid="stAlert"] {
    background-color: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 12px !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02) !important;
    color: #0F172A !important;
}
div[data-testid="stAlert"] p, div[data-testid="stAlert"] span {
    color: #0F172A !important;
}

/* Multiselect Tags / Chips */
div[data-baseweb="tag"] {
    background-color: #EFF6FF !important;
    border: 1px solid #BFDBFE !important;
    border-radius: 6px !important;
}
div[data-baseweb="tag"] span {
    color: #1D4ED8 !important;
    font-weight: 600 !important;
}

/* Code and Inline Code Blocks */
code {
    background-color: #F1F5F9 !important;
    color: #0F172A !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 5px !important;
    padding: 2px 6px !important;
    font-size: 88% !important;
    font-weight: 600 !important;
}
pre {
    background-color: #F8FAFC !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 10px !important;
    padding: 12px 16px !important;
    color: #0F172A !important;
}

/* Blockquotes */
blockquote {
    border-left: 4px solid #2563EB !important;
    background: #F8FAFC !important;
    padding: 10px 16px !important;
    border-radius: 0 8px 8px 0 !important;
    color: #334155 !important;
    margin: 8px 0 !important;
}

/* Streamlit Download Buttons */
.stDownloadButton > button {
    background: #FFFFFF !important;
    color: #2563EB !important;
    border: 1px solid #BFDBFE !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    box-shadow: 0 2px 6px rgba(37, 99, 235, 0.08) !important;
    transition: all 0.2s ease !important;
}
.stDownloadButton > button:hover {
    background: #EFF6FF !important;
    border-color: #2563EB !important;
    color: #1D4ED8 !important;
    transform: translateY(-1px) !important;
}

/* Audit and Forensics Cards in Light Theme */
.audit-card {
    background: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 14px !important;
    padding: 18px !important;
    margin-bottom: 14px !important;
    box-shadow: 0 4px 16px rgba(15, 23, 42, 0.03) !important;
}
.audit-header {
    display: flex !important;
    justify-content: space-between !important;
    align-items: center !important;
    border-bottom: 1px solid #F1F5F9 !important;
    padding-bottom: 10px !important;
    margin-bottom: 12px !important;
}

/* Section Dividers */
hr {
    border: none !important;
    border-top: 1px solid #E2E8F0 !important;
    margin: 22px 0 !important;
}

/* Disclaimer Banner */
.disclaimer-banner {
    background: #FFFBEB !important;
    border: 1px solid #FDE68A !important;
    border-left: 4px solid #F59E0B !important;
    border-radius: 10px !important;
    padding: 12px 18px !important;
    margin-bottom: 20px !important;
    font-size: 12.5px !important;
    color: #92400E !important;
    line-height: 1.5 !important;
}

/* Custom Scrollbars */
::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}
::-webkit-scrollbar-track {
    background: #F1F5F9;
}
::-webkit-scrollbar-thumb {
    background: #CBD5E1;
    border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
    background: #94A3B8;
}
</style>
"""


# -----------------------------------------------------------------------------
# HELPER FUNCTIONS & COMPONENT RENDERERS
# -----------------------------------------------------------------------------

def generate_sparkline_svg(color: str = "#2563EB", points: Optional[List[float]] = None) -> str:
    """Generates a clean inline SVG sparkline matching the reference design."""
    if not points or len(points) < 2:
        points = [28, 24, 26, 20, 23, 19, 25, 16, 12, 10]

    w, h = 140, 30
    min_v = min(points)
    max_v = max(points)
    span = max(max_v - min_v, 1.0)

    coords = []
    n = len(points)
    for i, v in enumerate(points):
        x = (i / (n - 1)) * (w - 10) + 5
        y = h - 5 - ((v - min_v) / span) * (h - 10)
        coords.append((x, y))

    path_d = f"M {coords[0][0]:.1f} {coords[0][1]:.1f} "
    for i in range(len(coords) - 1):
        x1, y1 = coords[i]
        x2, y2 = coords[i + 1]
        cx1 = x1 + (x2 - x1) * 0.4
        cy1 = y1
        cx2 = x1 + (x2 - x1) * 0.6
        cy2 = y2
        path_d += f"C {cx1:.1f} {cy1:.1f}, {cx2:.1f} {cy2:.1f}, {x2:.1f} {y2:.1f} "

    area_d = path_d + f"L {coords[-1][0]:.1f} {h} L {coords[0][0]:.1f} {h} Z"
    grad_id = f"grad_{abs(hash(color + str(points[0])))}"

    return f"""<svg width="100%" height="32" viewBox="0 0 {w} {h}" fill="none" xmlns="http://www.w3.org/2000/svg" style="display: block; overflow: visible;">
        <defs>
            <linearGradient id="{grad_id}" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="{color}" stop-opacity="0.22" />
                <stop offset="100%" stop-color="{color}" stop-opacity="0.0" />
            </linearGradient>
        </defs>
        <path d="{area_d}" fill="url(#{grad_id})" />
        <path d="{path_d}" stroke="{color}" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" />
        <circle cx="{coords[-1][0]:.1f}" cy="{coords[-1][1]:.1f}" r="3" fill="{color}" />
    </svg>"""


def render_premium_kpi(
    title: str,
    value: str,
    delta: str = "",
    delta_color: str = "#10B981",
    icon: str = "📊",
    icon_bg: str = "#EFF6FF",
    icon_color: str = "#2563EB",
    sparkline_color: str = "#2563EB",
    sparkline_points: Optional[List[float]] = None,
    tooltip: str = "",
    breakdown_html: str = ""
) -> str:
    """HTML string for luxury white KPI metric card matching the reference image."""
    tooltip_clean = tooltip.replace('"', '&quot;')
    tooltip_attr = f'title="{tooltip_clean}"' if tooltip else ""
    info_icon = f'<span style="cursor: help; color: #94A3B8; font-size: 11px; margin-left: 4px;" title="{tooltip_clean}">ⓘ</span>' if tooltip else ""
    svg_sparkline = generate_sparkline_svg(color=sparkline_color, points=sparkline_points)

    delta_span = (
        f'<span class="kpi-delta-tag" style="color: {delta_color};">{delta}</span>'
        if delta else ""
    )
    breakdown_div = f'<div class="kpi-breakdown-row">{breakdown_html}</div>' if breakdown_html else ""

    return f"""
    <div class="premium-kpi-card" {tooltip_attr}>
        <div class="kpi-top-row">
            <div class="kpi-icon-circle" style="background: {icon_bg}; color: {icon_color};">
                {icon}
            </div>
            <div class="kpi-label-text">{title} {info_icon}</div>
        </div>
        <div class="kpi-val-row">
            <div class="kpi-main-number">{value}</div>
            {delta_span}
        </div>
        <div class="kpi-sparkline-box">
            {svg_sparkline}
        </div>
        {breakdown_div}
    </div>
    """


def render_kpi(
    title: str,
    value: str,
    sub: str = "",
    border_color: str = "#1E88E5",
    tooltip: str = "",
    breakdown_html: str = ""
) -> str:
    """Backward-compatible KPI renderer upgraded to match the new luxury light theme."""
    # Map border colors to theme palettes
    color_map = {
        "#1E88E5": ("#EFF6FF", "#2563EB", "#2563EB"),
        "#00E5FF": ("#ECFEFF", "#0284C7", "#0284C7"),
        "#EF4444": ("#FEF2F2", "#DC2626", "#DC2626"),
        "#F59E0B": ("#FFFBEB", "#D97706", "#D97706"),
        "#A855F7": ("#FAF5FF", "#7C3AED", "#7C3AED"),
        "#EC4899": ("#FDF2F8", "#DB2777", "#DB2777"),
        "#10B981": ("#ECFDF5", "#059669", "#059669"),
    }
    bg, fg, spark = color_map.get(border_color, ("#F8FAFC", "#475569", "#2563EB"))

    return render_premium_kpi(
        title=title,
        value=value,
        delta=sub if sub.startswith("↑") or sub.startswith("↓") else "",
        delta_color="#10B981" if "↓" not in sub else "#EF4444",
        icon="📊" if "Transactions" in title or "Volume" in title else ("🛡️" if "Alert" in title else "⚠️"),
        icon_bg=bg,
        icon_color=fg,
        sparkline_color=spark,
        tooltip=tooltip,
        breakdown_html=breakdown_html or (f'<span style="font-size:11px;color:#64748B;">{sub}</span>' if sub and not (sub.startswith("↑") or sub.startswith("↓")) else "")
    )


def render_risk_badge(category: str) -> str:
    """Returns styled HTML risk badge for the light theme."""
    cat = str(category).upper()
    if cat == "CRITICAL":
        return '<span class="badge-critical">CRITICAL</span>'
    elif cat == "HIGH":
        return '<span class="badge-high">HIGH</span>'
    elif cat == "MEDIUM":
        return '<span class="badge-medium">MEDIUM</span>'
    else:
        return '<span class="badge-low">LOW</span>'
