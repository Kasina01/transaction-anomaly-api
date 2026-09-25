"""
audit_store.py
Persistent SQLite-based compliance audit log for the Product Development Curtailment Layer.
No external database credentials or API keys required.
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any

DB_PATH = Path(__file__).parent / "audit.db"


def init_db():
    """Initializes the SQLite schema if it doesn't already exist."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id TEXT UNIQUE NOT NULL,
                timestamp TEXT NOT NULL,
                customer_id TEXT NOT NULL,
                amount REAL NOT NULL,
                fraud_probability REAL NOT NULL,
                flagged INTEGER NOT NULL,
                decision_action TEXT NOT NULL,
                reason TEXT NOT NULL,
                signals_json TEXT,
                dispatched_actions_json TEXT,
                status TEXT NOT NULL,
                investigator_notes TEXT,
                updated_at TEXT NOT NULL
            )
        """)
        conn.commit()


def log_curtailment_event(
    transaction_id: str,
    customer_id: str,
    amount: float,
    fraud_probability: float,
    flagged: bool,
    decision_action: str,
    reason: str,
    signals: Dict[str, Any],
    dispatched_actions: List[Dict[str, Any]],
    status: str = "EXECUTED",
    investigator_notes: str = ""
) -> int:
    """Inserts or updates a curtailment event into the audit database."""
    init_db()
    now_str = datetime.utcnow().isoformat()
    signals_str = json.dumps(signals)
    dispatched_str = json.dumps(dispatched_actions)

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO audit_events (
                transaction_id, timestamp, customer_id, amount,
                fraud_probability, flagged, decision_action, reason,
                signals_json, dispatched_actions_json, status,
                investigator_notes, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(transaction_id) DO UPDATE SET
                fraud_probability = excluded.fraud_probability,
                flagged = excluded.flagged,
                decision_action = excluded.decision_action,
                reason = excluded.reason,
                signals_json = excluded.signals_json,
                dispatched_actions_json = excluded.dispatched_actions_json,
                status = excluded.status,
                investigator_notes = excluded.investigator_notes,
                updated_at = excluded.updated_at
        """, (
            transaction_id, now_str, customer_id, amount,
            fraud_probability, 1 if flagged else 0, decision_action, reason,
            signals_str, dispatched_str, status,
            investigator_notes, now_str
        ))
        conn.commit()
        return cursor.lastrowid or 0


def get_audit_events(limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieves recent audit log events sorted from newest to oldest."""
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM audit_events ORDER BY id DESC LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        
        events = []
        for r in rows:
            events.append({
                "id": r["id"],
                "transaction_id": r["transaction_id"],
                "timestamp": r["timestamp"],
                "customer_id": r["customer_id"],
                "amount": r["amount"],
                "fraud_probability": r["fraud_probability"],
                "flagged": bool(r["flagged"]),
                "decision_action": r["decision_action"],
                "reason": r["reason"],
                "signals": json.loads(r["signals_json"]) if r["signals_json"] else {},
                "dispatched_actions": json.loads(r["dispatched_actions_json"]) if r["dispatched_actions_json"] else [],
                "status": r["status"],
                "investigator_notes": r["investigator_notes"] or "",
                "updated_at": r["updated_at"]
            })
        return events


def override_event(transaction_id: str, new_action: str, notes: str) -> bool:
    """Allows an investigator or Watson Orchestrate agent to override an action."""
    init_db()
    now_str = datetime.utcnow().isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE audit_events
            SET decision_action = ?,
                status = 'OVERRIDDEN',
                investigator_notes = ?,
                updated_at = ?
            WHERE transaction_id = ?
        """, (new_action, notes, now_str, transaction_id))
        conn.commit()
        return cursor.rowcount > 0


def get_metrics() -> Dict[str, Any]:
    """Calculates operational metrics across all audited transactions."""
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM audit_events")
        total = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM audit_events WHERE decision_action = 'FREEZE_ACCOUNT'")
        frozen = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM audit_events WHERE decision_action = 'BLOCK_TRANSACTION'")
        blocked = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM audit_events WHERE decision_action = 'STEP_UP_MFA'")
        step_up = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM audit_events WHERE decision_action = 'AUTO_APPROVE'")
        approved = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM audit_events WHERE status = 'OVERRIDDEN'")
        overridden = cursor.fetchone()[0]

        return {
            "total_transactions": total,
            "frozen_accounts": frozen,
            "blocked_transactions": blocked,
            "step_up_challenges": step_up,
            "auto_approved": approved,
            "manual_overrides": overridden
        }
