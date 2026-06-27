import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "expenses.db")


def get_connection() -> sqlite3.Connection:
    """Return a connection to the SQLite database with row factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def init_db():
    """Create all required tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS categories (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL UNIQUE,
            created_at  TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS transactions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     TEXT NOT NULL,
            amount      REAL NOT NULL,
            category    TEXT NOT NULL,
            description TEXT DEFAULT '',
            image_url   TEXT DEFAULT '',
            source      TEXT DEFAULT 'slip',
            created_at  TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS pending_transactions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     TEXT NOT NULL,
            amount      REAL NOT NULL,
            description TEXT DEFAULT '',
            image_url   TEXT DEFAULT '',
            state       TEXT NOT NULL DEFAULT 'awaiting_category',
            raw_ocr     TEXT DEFAULT '',
            created_at  TEXT NOT NULL DEFAULT (datetime('now'))
        );
    """)

    # Seed default categories if table is empty
    existing = cursor.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
    if existing == 0:
        default_cats = ["Food", "Transport", "Bills", "Shopping", "Entertainment", "Health"]
        for cat in default_cats:
            cursor.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (cat,))

    conn.commit()
    conn.close()


# ── Pending transaction helpers ──────────────────────────────────────

def add_pending(user_id: str, amount: float, description: str, image_url: str,
                raw_ocr: str = "") -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO pending_transactions (user_id, amount, description, image_url, state, raw_ocr)
           VALUES (?, ?, ?, ?, 'awaiting_category', ?)""",
        (user_id, amount, description, image_url, raw_ocr),
    )
    conn.commit()
    pending_id = cursor.lastrowid
    conn.close()
    return pending_id


def get_pending(user_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM pending_transactions WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
        (user_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def update_pending_state(user_id: str, state: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    # Get the latest pending ID first (SQLite does not support ORDER BY in UPDATE)
    cursor.execute(
        "SELECT id FROM pending_transactions WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
        (user_id,),
    )
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False
    cursor.execute(
        "UPDATE pending_transactions SET state = ? WHERE id = ?",
        (state, row["id"]),
    )
    conn.commit()
    updated = cursor.rowcount > 0
    conn.close()
    return updated


def delete_pending(user_id: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    # Get the latest pending ID first (SQLite does not support ORDER BY in DELETE on all versions)
    cursor.execute(
        "SELECT id FROM pending_transactions WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
        (user_id,),
    )
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False
    cursor.execute("DELETE FROM pending_transactions WHERE id = ?", (row["id"],))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted


# ── Category helpers ─────────────────────────────────────────────────

def get_categories() -> list[str]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM categories ORDER BY name")
    rows = cursor.fetchall()
    conn.close()
    return [row["name"] for row in rows]


def add_category(name: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO categories (name) VALUES (?)", (name.strip(),))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


# ── Transaction helpers ──────────────────────────────────────────────

def add_transaction(user_id: str, amount: float, category: str,
                    description: str = "", image_url: str = "",
                    source: str = "slip") -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO transactions (user_id, amount, category, description, image_url, source)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (user_id, amount, category, description, image_url, source),
    )
    conn.commit()
    trans_id = cursor.lastrowid
    conn.close()
    return trans_id


def get_monthly_total(user_id: str) -> float:
    """Sum of current month's transactions for the user."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT COALESCE(SUM(amount), 0) FROM transactions
           WHERE user_id = ? AND strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')""",
        (user_id,),
    )
    total = cursor.fetchone()[0]
    conn.close()
    return total


def get_all_transactions(user_id: str) -> list[dict]:
    """Return all transactions for the user, newest first."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM transactions WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]
