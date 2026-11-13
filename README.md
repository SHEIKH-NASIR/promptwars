# 🛡️ FinGuard AI
### Intelligent Financial Fraud Detection & Anti-Money Laundering System
*Enterprise-Grade Financial Crime Detection & Risk Intelligence for Modern Banking Rails*

---

## 📌 Executive Overview

**FinGuard AI** is a next-generation AI-powered financial fraud detection and Anti-Money Laundering (AML) surveillance system tailored for high-velocity payment networks (UPI, IMPS, NEFT, RTGS, Bank Transfers, and Mobile Wallets). Designed around RBI/PMLA-aligned monitoring concepts, FinGuard AI bridges the gap between black-box machine learning and operational compliance investigations.

The platform combines **supervised gradient-boosted classification (XGBoost)**, **unsupervised density-based anomaly detection (Isolation Forest)**, **topological graph cycle detection (NetworkX)**, and **explainable AI (SHAP)** with a real-time cybersecurity command center interface.

---

## 🎯 Problem Statement & Objectives

Modern digital payment rails in India process billions of transactions daily. Traditional fraud detection rules suffer from:
1. **High False Positive Rates (FPR):** Over-flagging legitimate high-value transactions.
2. **Detection Blindspots for Coordinated AML Typologies:** Inability to spot structuring (smurfing), synthetic mule networks, and circular money laundering loops.
3. **Lack of Explainability:** Black-box ML predictions without clear, evidence-backed regulatory audit trails.

### Core Objectives:
- **Zero-Day Anomaly Detection:** Detect novel fraud spikes and unusual account behavioral deviations without requiring labeled historical anomalies.
- **Topological AML Graph Surveillance:** Uncover circular flow rings ($A \to B \to C \to A$), rapid pass-through transit mules, and fan-in/fan-out smurfing patterns.
- **Transparent Risk Scoring:** Calculate calibrated, bounded composite risk scores from $0$ to $100$ with explicit component weighting.
- **Explainable Audit Trails:** Provide SHAP feature attribution waterfalls and factual forensic narratives for compliance and Financial Intelligence Unit (FIU) reporting.

---

## 🏛️ System Architecture

FinGuard AI operates as an integrated, multi-tier security intelligence architecture:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        FinGuard AI Dashboard (UI)                      │
│   (Executive Overview | Surveillance | AML Dossiers | Money Graph)     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────┴────────────────────────────────────┐
│                    FinGuard Core Intelligence Engine                   │
├───────────────────────┬────────────────────────┬───────────────────────┤
│    Machine Learning   │     AML Graph Engine   │  Risk Scoring Engine  │
│  - Supervised XGBoost │  - Structuring Filter  │  - Multi-factor score │
│  - Isolation Forest   │  - Mule Aggregation    │  - Bounded (0-100)    │
│  - SHAP TreeExplainer │  - Cycle Loops (Nx)    │  - Regulatory Actions │
└───────────────────────┴────────────────────────┴───────────────────────┘
                                    │
┌───────────────────────────────────┴────────────────────────────────────┐
│                    Persistence & Simulation Engine                     │
│  - SQLite Multi-Table Ledger (Transactions, Alerts, AML Cases)         │
│  - Synthetic Generator (UPI, IMPS, NEFT, RTGS with 8 Scenarios)       │
└────────────────────────────────────────────────────────────────────────┘
```

---

## ⚡ Core Features & Capabilities

### 1. Multi-Rail Transaction Surveillance
- Continuous ingestion and risk scoring across UPI, IMPS, NEFT, RTGS, Bank Transfers, and Mobile Wallets.
- Real-time detection of high-value spikes, rapid velocity bursts, and odd-hour anomalies.

### 2. Specialized AML Typology Detectors
- **A. Structuring (Smurfing):** Identifies repeated transfers just beneath the ₹50,000 regulatory reporting threshold within configurable rolling windows.
- **B. Mule Account Detection:** Pinpoints intermediary accounts receiving funds from multiple senders and rapidly disbursing $\ge 85\%$ of funds to external destinations.
- **C. Rapid Fund Movement:** Alerts on incoming transfers forwarded to a third party within minutes.
- **D. Circular Money Movement:** Uses NetworkX directed graph depth-bounded search to detect closed loops ($A \to B \to C \to A$) designed to artificially inflate turnover or obfuscate origins.
- **E. Suspicious Network Hubs:** Analyzes in-degree/out-degree centrality and intermediary transit nodes.

### 3. Transparent Multi-Factor Risk Scoring
Generates bounded composite scores from $0$ to $100$:
$$\text{Risk Score} = \min\left(100, \, \sum_{i} w_i \cdot C_i\right)$$
- **0 – 24 (LOW):** Standard automated clearance.
- **25 – 49 (MEDIUM):** Soft friction / dynamic velocity ceiling.
- **50 – 74 (HIGH):** Route to Senior Fraud Analyst queue / Step-up 2FA.
- **75 – 100 (CRITICAL):** Immediate hold / Level-3 Suspicious Transaction Report (STR) consideration.

### 4. Explainable AI (XAI) with SHAP
- SHAP TreeExplainer computes exact log-odds feature contributions for each flagged transaction.
- Interactive Plotly waterfall chart visually depicts positive risk drivers (e.g. amount spike, cross-city jump) vs negative risk dampeners.

### 5. Interactive Money Flow Network
- NetworkX & Plotly topological graph with directional flow vectors.
- Node color-coding: Red (Hub / High Dispersion), Orange (Intermediary Transit), Cyan (Normal).
- Hover tooltips with account degrees, volume, and cycle associations.

### 6. Simulated Real-Time Streaming
- Controlled stream simulation injecting realistic consumer spend alongside live fraud scenarios.
- Supports single-step (`Stream 1`) and batch-step (`Stream 5`) processing with immediate database persistence.

### 7. Safe External CSV Ingestion
- Upload external `.csv` transaction batches (<10MB) for instant offline forensic audit.
- Full CSV export capability for Transactions, Fraud Alerts, AML Cases, and Suspicious Accounts.

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Core Framework** | Python 3.10+, Streamlit 1.32+ |
| **Machine Learning** | scikit-learn 1.4+, XGBoost 2.0+, imbalanced-learn 0.12+ |
| **Explainable AI** | SHAP (TreeExplainer) |
| **Graph & Topology** | NetworkX 3.0+ |
| **Data & Vectorization** | Pandas 2.0+, NumPy 1.24+ |
| **Visualization** | Plotly 5.18+, Matplotlib |
| **Synthetic Generation** | Faker (en_IN locale), python-dateutil |
| **Storage & Ledger** | SQLite3 (Parameterized ACID relational storage) |

---

## 🧪 Controlled Synthetic Benchmark Scenarios

The synthetic generator (`generator.py`) generates realistic transactions across 8 controlled behavioral scenarios:

1. **Normal Transactions:** Typical retail spending (₹20 to ₹15,000).
2. **High-Value Spikes:** Unusually large transfers (₹850,000 to ₹3,500,000) over RTGS/NEFT.
3. **Rapid Velocity Bursts:** 4–7 repeated transfers from the same account within 2–5 minutes.
4. **Fan-In Aggregation:** Multiple victim/source accounts sending funds to a single collector account.
5. **Fan-Out Dispersion:** Single distributor account scattering funds across multiple recipients.
6. **Structuring:** Multiple transfers between ₹47,500 and ₹49,850 just below the ₹50,000 reporting ceiling.
7. **Mule Account Pass-Through:** Inflow from multiple sources followed by 95%+ rapid outbound drain to crypto/forex merchants.
8. **Circular Flow Rings:** Directed loops ($A \to B \to C \to A$) transferring funds across accounts in sequence.

---

## 💻 Installation & Execution (Windows)

### 1. Prerequisites
- Python 3.10, 3.11, 3.12, or 3.13
- Windows Command Prompt or PowerShell

### 2. Environment Setup & Dependency Installation
Open terminal inside the extracted repository folder (`d:\promptwars`):

```powershell
# Create virtual environment (optional)
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
python -m pip install -r requirements.txt
```

### 3. Initialize & Seed Database
```powershell
python scripts/seed_demo_data.py
```

### 4. Run the FinGuard AI Dashboard
```powershell
streamlit run app.py
```
*Or alternatively:*
```powershell
streamlit run dashboard/app.py
```

The application will launch on:
👉 **`http://localhost:8501`**

---

## 📊 Automated Verification & Test Results

FinGuard AI includes a 12-point automated test suite (`tests/test_finguard.py`):

```powershell
python -u tests/test_finguard.py
```

### Test Suite Execution Output:
```
test_01_normal_transaction (__main__.TestFinGuardAI.test_01_normal_transaction) ... ok
test_02_abnormally_large_transaction (__main__.TestFinGuardAI.test_02_abnormally_large_transaction) ... ok
test_03_repeated_rapid_transactions (__main__.TestFinGuardAI.test_03_repeated_rapid_transactions) ... ok
test_04_structuring_detection (__main__.TestFinGuardAI.test_04_structuring_detection) ... ok
test_05_mule_account_detection (__main__.TestFinGuardAI.test_05_mule_account_detection) ... ok
test_06_circular_transfers_detection (__main__.TestFinGuardAI.test_06_circular_transfers_detection) ... ok
test_07_normal_account_activity (__main__.TestFinGuardAI.test_07_normal_account_activity) ... ok
test_08_risk_score_bounds_and_categorization (__main__.TestFinGuardAI.test_08_risk_score_bounds_and_categorization) ... ok
test_09_csv_batch_audit (__main__.TestFinGuardAI.test_09_csv_batch_audit) ... ok
test_10_database_crud (__main__.TestFinGuardAI.test_10_database_crud) ... ok
test_11_streaming_simulation (__main__.TestFinGuardAI.test_11_streaming_simulation) ... ok
test_12_explainability (__main__.TestFinGuardAI.test_12_explainability) ... ok

----------------------------------------------------------------------
Ran 12 tests in 2.323s

OK (100% Passed)
```

---

## ⚠️ Known Limitations & Future Improvements

### Limitations:
- **Synthetic Data Baseline:** Uses statistically realistic synthetic data to comply with data privacy laws; production deployment requires integration with a bank's encrypted data lake.
- **Offline Graph Partitioning:** Large-scale graphs (>1,000,000 edges) should be processed via distributed graph backends (e.g., Neo4j, Apache GraphX) rather than in-memory NetworkX.

### Future Roadmap:
- **Graph Neural Networks (GNNs):** Implement Relational Graph Convolutional Networks (R-GCN) for sub-graph pattern classification.
- **Biometric Fraud Signals:** Ingest client-side device accelerometer, typing cadence, and SIM-swap indicators.
- **FIU-IND Automated XML Generation:** Generate direct reporting XML files conforming to Financial Intelligence Unit India schemas.

---
*Developed for FinGuard AI — Intelligent Financial Crime Detection & Risk Intelligence.*
