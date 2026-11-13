"""
database.py - FinGuard AI SQLite Database Manager
Handles tables: transactions, fraud_alerts, suspicious_accounts, aml_cases, system_activity.
All queries use parameterized statements.
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import pandas as pd

DB_PATH = Path(__file__).resolve().parent / "data" / "finguard.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    target_path = str(db_path or DB_PATH)
    conn = sqlite3.connect(target_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_database(db_path: Optional[Path] = None):
    """Initializes tables with proper indices and constraints."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS transactions (
        transaction_id TEXT PRIMARY KEY,
        sender_account TEXT NOT NULL,
        receiver_account TEXT NOT NULL,
        amount REAL NOT NULL,
        timestamp TEXT NOT NULL,
        transaction_type TEXT NOT NULL,
        merchant_category TEXT NOT NULL,
        sender_location TEXT NOT NULL,
        receiver_location TEXT NOT NULL,
        device_id TEXT NOT NULL,
        ip_address TEXT NOT NULL,
        transaction_status TEXT NOT NULL,
        risk_score REAL DEFAULT 0,
        risk_category TEXT DEFAULT 'LOW',
        fraud_label INTEGER DEFAULT 0,
        scenario_tag TEXT DEFAULT 'NORMAL',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS fraud_alerts (
        alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
        transaction_id TEXT NOT NULL UNIQUE,
        risk_score REAL NOT NULL,
        risk_category TEXT NOT NULL,
        primary_reason TEXT NOT NULL,
        evidence_json TEXT,
        recommended_action TEXT,
        status TEXT DEFAULT 'OPEN',
        assigned_to TEXT DEFAULT 'Unassigned',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (transaction_id) REFERENCES transactions (transaction_id)
    );

    CREATE TABLE IF NOT EXISTS suspicious_accounts (
        account_id TEXT PRIMARY KEY,
        incoming_count INTEGER DEFAULT 0,
        outgoing_count INTEGER DEFAULT 0,
        total_incoming_amount REAL DEFAULT 0,
        total_outgoing_amount REAL DEFAULT 0,
        risk_score REAL DEFAULT 0,
        risk_level TEXT DEFAULT 'LOW',
        suspicious_patterns TEXT,
        investigation_status TEXT DEFAULT 'PENDING',
        last_updated TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS aml_cases (
        case_id TEXT PRIMARY KEY,
        case_type TEXT NOT NULL,
        primary_account TEXT NOT NULL,
        involved_accounts TEXT,
        total_amount REAL NOT NULL,
        transaction_count INTEGER NOT NULL,
        time_span_minutes REAL,
        evidence_summary TEXT,
        related_txns TEXT,
        severity TEXT DEFAULT 'HIGH',
        status TEXT DEFAULT 'ACTIVE',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS system_activity (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type TEXT NOT NULL,
        description TEXT NOT NULL,
        metadata_json TEXT,
        timestamp TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE INDEX IF NOT EXISTS idx_txn_sender ON transactions(sender_account);
    CREATE INDEX IF NOT EXISTS idx_txn_receiver ON transactions(receiver_account);
    CREATE INDEX IF NOT EXISTS idx_txn_timestamp ON transactions(timestamp);
    CREATE INDEX IF NOT EXISTS idx_txn_risk_category ON transactions(risk_category);
    CREATE INDEX IF NOT EXISTS idx_alerts_status ON fraud_alerts(status);
    CREATE INDEX IF NOT EXISTS idx_aml_case_type ON aml_cases(case_type);
    """)

    conn.commit()
    conn.close()


def insert_transaction(txn: Dict[str, Any], db_path: Optional[Path] = None) -> bool:
    """Inserts a single transaction record using parameterized queries."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO transactions (
                transaction_id, sender_account, receiver_account, amount,
                timestamp, transaction_type, merchant_category, sender_location,
                receiver_location, device_id, ip_address, transaction_status,
                risk_score, risk_category, fraud_label, scenario_tag
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            txn["transaction_id"], txn["sender_account"], txn["receiver_account"],
            float(txn["amount"]), str(txn["timestamp"]), txn["transaction_type"],
            txn["merchant_category"], txn["sender_location"], txn["receiver_location"],
            txn["device_id"], txn["ip_address"], txn["transaction_status"],
            float(txn.get("risk_score", 0)), txn.get("risk_category", "LOW"),
            int(txn.get("fraud_label", 0)), txn.get("scenario_tag", "NORMAL")
        ))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        return False
    finally:
        conn.close()


def insert_transactions_batch(txns: List[Dict[str, Any]], db_path: Optional[Path] = None) -> int:
    """Inserts a batch of transactions efficiently."""
    if not txns:
        return 0
    conn = get_connection(db_path)
    cursor = conn.cursor()
    inserted = 0
    try:
        tuples = [
            (
                t["transaction_id"], t["sender_account"], t["receiver_account"],
                float(t["amount"]), str(t["timestamp"]), t["transaction_type"],
                t["merchant_category"], t["sender_location"], t["receiver_location"],
                t["device_id"], t["ip_address"], t["transaction_status"],
                float(t.get("risk_score", 0)), t.get("risk_category", "LOW"),
                int(t.get("fraud_label", 0)), t.get("scenario_tag", "NORMAL")
            )
            for t in txns
        ]
        cursor.executemany("""
            INSERT OR REPLACE INTO transactions (
                transaction_id, sender_account, receiver_account, amount,
                timestamp, transaction_type, merchant_category, sender_location,
                receiver_location, device_id, ip_address, transaction_status,
                risk_score, risk_category, fraud_label, scenario_tag
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, tuples)
        conn.commit()
        inserted = cursor.rowcount
    except Exception as e:
        conn.rollback()
    finally:
        conn.close()
    return inserted


def insert_fraud_alert(alert: Dict[str, Any], db_path: Optional[Path] = None) -> bool:
    conn = get_connection(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO fraud_alerts (
                transaction_id, risk_score, risk_category, primary_reason,
                evidence_json, recommended_action, status, assigned_to
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            alert["transaction_id"], float(alert["risk_score"]), alert["risk_category"],
            alert["primary_reason"], json.dumps(alert.get("evidence", {})),
            alert.get("recommended_action", "Manual Review Required"),
            alert.get("status", "OPEN"), alert.get("assigned_to", "Unassigned")
        ))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        return False
    finally:
        conn.close()


def insert_fraud_alerts_batch(alerts: List[Dict[str, Any]], db_path: Optional[Path] = None) -> int:
    if not alerts:
        return 0
    conn = get_connection(db_path)
    cursor = conn.cursor()
    count = 0
    try:
        tuples = [
            (
                a["transaction_id"], float(a["risk_score"]), a["risk_category"],
                a["primary_reason"], json.dumps(a.get("evidence", {})),
                a.get("recommended_action", "Manual Review Required"),
                a.get("status", "OPEN"), a.get("assigned_to", "Unassigned")
            )
            for a in alerts
        ]
        cursor.executemany("""
            INSERT OR REPLACE INTO fraud_alerts (
                transaction_id, risk_score, risk_category, primary_reason,
                evidence_json, recommended_action, status, assigned_to
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, tuples)
        conn.commit()
        count = cursor.rowcount
    except Exception as e:
        conn.rollback()
    finally:
        conn.close()
    return count


def insert_aml_case(case: Dict[str, Any], db_path: Optional[Path] = None) -> bool:
    conn = get_connection(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO aml_cases (
                case_id, case_type, primary_account, involved_accounts,
                total_amount, transaction_count, time_span_minutes,
                evidence_summary, related_txns, severity, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            case["case_id"], case["case_type"], case["primary_account"],
            json.dumps(case.get("involved_accounts", [])),
            float(case["total_amount"]), int(case["transaction_count"]),
            float(case.get("time_span_minutes", 0)),
            case.get("evidence_summary", ""),
            json.dumps(case.get("related_txns", [])),
            case.get("severity", "HIGH"),
            case.get("status", "ACTIVE")
        ))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        return False
    finally:
        conn.close()


def update_suspicious_account(acc: Dict[str, Any], db_path: Optional[Path] = None) -> bool:
    conn = get_connection(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO suspicious_accounts (
                account_id, incoming_count, outgoing_count,
                total_incoming_amount, total_outgoing_amount,
                risk_score, risk_level, suspicious_patterns,
                investigation_status, last_updated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(account_id) DO UPDATE SET
                incoming_count = excluded.incoming_count,
                outgoing_count = excluded.outgoing_count,
                total_incoming_amount = excluded.total_incoming_amount,
                total_outgoing_amount = excluded.total_outgoing_amount,
                risk_score = excluded.risk_score,
                risk_level = excluded.risk_level,
                suspicious_patterns = excluded.suspicious_patterns,
                last_updated = CURRENT_TIMESTAMP
        """, (
            acc["account_id"], int(acc.get("incoming_count", 0)),
            int(acc.get("outgoing_count", 0)), float(acc.get("total_incoming_amount", 0)),
            float(acc.get("total_outgoing_amount", 0)), float(acc.get("risk_score", 0)),
            acc.get("risk_level", "LOW"), json.dumps(acc.get("suspicious_patterns", [])),
            acc.get("investigation_status", "PENDING")
        ))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        return False
    finally:
        conn.close()


def log_activity(event_type: str, description: str, metadata: Optional[Dict] = None, db_path: Optional[Path] = None):
    conn = get_connection(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO system_activity (event_type, description, metadata_json)
            VALUES (?, ?, ?)
        """, (event_type, description, json.dumps(metadata or {})))
        conn.commit()
    except Exception:
        pass
    finally:
        conn.close()


def fetch_transactions_df(limit: Optional[int] = None, db_path: Optional[Path] = None) -> pd.DataFrame:
    conn = get_connection(db_path)
    query = "SELECT * FROM transactions ORDER BY timestamp DESC"
    if limit:
        query += f" LIMIT {int(limit)}"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def fetch_fraud_alerts(status: Optional[str] = None, db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    conn = get_connection(db_path)
    cursor = conn.cursor()
    if status:
        cursor.execute("SELECT * FROM fraud_alerts WHERE status = ? ORDER BY risk_score DESC", (status,))
    else:
        cursor.execute("SELECT * FROM fraud_alerts ORDER BY risk_score DESC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def fetch_recent_critical_alerts(limit: int = 10, db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Fetches high and critical risk alerts joined with transaction telemetry."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            a.alert_id,
            a.transaction_id,
            COALESCE(t.amount, 0.0) as amount,
            a.risk_score,
            a.risk_category,
            a.primary_reason,
            a.status,
            COALESCE(t.transaction_type, 'UPI') as transaction_type,
            COALESCE(t.timestamp, a.created_at) as timestamp,
            a.recommended_action
        FROM fraud_alerts a
        LEFT JOIN transactions t ON a.transaction_id = t.transaction_id
        WHERE a.risk_category IN ('HIGH', 'CRITICAL') OR a.risk_score >= 50.0
        ORDER BY a.risk_score DESC, a.created_at DESC
        LIMIT ?
    """, (int(limit),))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def fetch_aml_cases(db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM aml_cases ORDER BY created_at DESC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def fetch_suspicious_accounts(min_risk: float = 0, db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM suspicious_accounts WHERE risk_score >= ? ORDER BY risk_score DESC", (min_risk,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def fetch_kpis(db_path: Optional[Path] = None) -> Dict[str, Any]:
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # 1. Transactions volume
    cursor.execute("SELECT COUNT(*), COALESCE(SUM(amount), 0) FROM transactions")
    total_txns, total_vol = cursor.fetchone()

    # 2. Fraud alerts total and status breakdowns
    cursor.execute("SELECT COUNT(*) FROM fraud_alerts WHERE status != 'DISMISSED'")
    fraud_alerts_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM fraud_alerts WHERE status = 'OPEN'")
    alerts_pending = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM fraud_alerts WHERE status IN ('IN_REVIEW', 'UNDER_REVIEW', 'ASSIGNED')")
    alerts_investigating = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM fraud_alerts WHERE status IN ('RESOLVED', 'DISMISSED', 'CLOSED')")
    alerts_resolved = cursor.fetchone()[0]

    # 3. AML cases total and typology breakdowns
    cursor.execute("SELECT COUNT(*) FROM aml_cases WHERE status = 'ACTIVE'")
    aml_cases_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM aml_cases WHERE case_type = 'STRUCTURING'")
    aml_structuring_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM aml_cases WHERE case_type = 'MULE_ACCOUNT'")
    aml_mule_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM aml_cases WHERE case_type = 'RAPID_FUND_MOVEMENT'")
    aml_rapid_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM aml_cases WHERE case_type = 'CIRCULAR_TRANSFERS'")
    aml_circular_count = cursor.fetchone()[0]

    # 4. Suspicious accounts
    cursor.execute("SELECT COUNT(*) FROM suspicious_accounts WHERE risk_score >= 50 OR risk_level IN ('HIGH', 'CRITICAL')")
    suspicious_acc_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM suspicious_accounts WHERE risk_score >= 75 OR risk_level = 'CRITICAL'")
    critical_acc_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM suspicious_accounts WHERE (risk_score >= 50 AND risk_score < 75) OR risk_level = 'HIGH'")
    high_acc_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM suspicious_accounts")
    total_acc_count = cursor.fetchone()[0]

    # 5. High-risk transaction exposure
    cursor.execute("SELECT COUNT(*), COALESCE(SUM(amount), 0) FROM transactions WHERE risk_category IN ('HIGH', 'CRITICAL') OR risk_score >= 50.0")
    high_risk_txns, high_risk_vol = cursor.fetchone()

    conn.close()
    return {
        # Core preserved keys (existing callers rely on these)
        "total_transactions": total_txns or 0,
        "total_volume_inr": total_vol or 0.0,
        "fraud_alerts_count": fraud_alerts_count or 0,
        "aml_cases_count": aml_cases_count or 0,
        "suspicious_accounts_count": suspicious_acc_count or 0,
        "high_risk_transactions": high_risk_txns or 0,
        "high_risk_volume_inr": high_risk_vol or 0.0,

        # Enhanced breakdowns requested
        "fraud_alerts_pending": alerts_pending or 0,
        "fraud_alerts_investigating": alerts_investigating or 0,
        "fraud_alerts_resolved": alerts_resolved or 0,
        "aml_structuring_count": aml_structuring_count or 0,
        "aml_mule_count": aml_mule_count or 0,
        "aml_rapid_count": aml_rapid_count or 0,
        "aml_circular_count": aml_circular_count or 0,
        "high_risk_accounts_count": suspicious_acc_count or 0,
        "critical_accounts_count": critical_acc_count or 0,
        "moderate_high_accounts_count": high_acc_count or 0,
        "total_accounts_count": total_acc_count or 0,
        "high_risk_exposure_formula": "Cumulative INR volume of all transactions classified as HIGH (50–74) or CRITICAL (75–100) risk",
    }


def reset_database(db_path: Optional[Path] = None):
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.executescript("""
        DELETE FROM fraud_alerts;
        DELETE FROM aml_cases;
        DELETE FROM suspicious_accounts;
        DELETE FROM system_activity;
        DELETE FROM transactions;
    """)
    conn.commit()
    conn.close()
    log_activity("RESET", "Database records cleared for demonstration reset.", db_path=db_path)
