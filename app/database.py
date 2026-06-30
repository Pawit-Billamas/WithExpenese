import os
import ssl
import pg8000
import pg8000.dbapi
from urllib.parse import urlparse

DATABASE_URL = os.getenv("DATABASE_URL", "")


def _parse_url() -> dict:
    """Parse a postgres:// URL into pg8000 connect kwargs."""
    p = urlparse(DATABASE_URL)
    return {
        "host": p.hostname,
        "port": p.port or 5432,
        "database": p.path.lstrip("/"),
        "user": p.username,
        "password": p.password,
    }


def get_connection():
    """Return a pg8000 connection (SSL required for Neon)."""
    ssl_ctx = ssl.create_default_context()
    return pg8000.connect(**_parse_url(), ssl_context=ssl_ctx)


def _as_dict(cursor, row) -> dict:
    """Convert a single row tuple to a dict using cursor.description."""
    cols = [d[0] for d in cursor.description]
    return dict(zip(cols, row))


def _all_as_dicts(cursor) -> list[dict]:
    cols = [d[0] for d in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]


def init_db():
    """Create all required tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id         SERIAL PRIMARY KEY,
            name       TEXT NOT NULL UNIQUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id          SERIAL PRIMARY KEY,
            user_id     TEXT NOT NULL,
            amount      REAL NOT NULL,
            category    TEXT NOT NULL,
            description TEXT DEFAULT '',
            image_url   TEXT DEFAULT '',
            source      TEXT DEFAULT 'slip',
            created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pending_transactions (
            id          SERIAL PRIMARY KEY,
            user_id     TEXT NOT NULL,
            amount      REAL NOT NULL,
            description TEXT DEFAULT '',
            image_url   TEXT DEFAULT '',
            state       TEXT NOT NULL DEFAULT 'awaiting_category',
            raw_ocr     TEXT DEFAULT '',
            created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS manage_sessions (
            user_id        TEXT PRIMARY KEY,
            transaction_id INTEGER NOT NULL,
            state          TEXT NOT NULL DEFAULT 'menu'
        )
    """)

    # Seed default categories if empty
    cursor.execute("SELECT COUNT(*) FROM categories")
    if cursor.fetchone()[0] == 0:
        for cat in ["Food", "Transport", "Bills", "Shopping", "Entertainment", "Health"]:
            cursor.execute(
                "INSERT INTO categories (name) VALUES (%s) ON CONFLICT DO NOTHING", (cat,)
            )

    conn.commit()
    cursor.close()
    conn.close()


# ── Pending helpers ───────────────────────────────────────────────────

def add_pending(user_id: str, amount: float, description: str,
                image_url: str, raw_ocr: str = "") -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO pending_transactions
               (user_id, amount, description, image_url, state, raw_ocr)
           VALUES (%s, %s, %s, %s, 'awaiting_category', %s)
           RETURNING id""",
        (user_id, amount, description, image_url, raw_ocr),
    )
    pending_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()
    return pending_id


def get_pending(user_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM pending_transactions WHERE user_id = %s ORDER BY created_at DESC LIMIT 1",
        (user_id,),
    )
    row = cursor.fetchone()
    result = _as_dict(cursor, row) if row else None
    cursor.close()
    conn.close()
    return result


def update_pending_state(user_id: str, state: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM pending_transactions WHERE user_id = %s ORDER BY created_at DESC LIMIT 1",
        (user_id,),
    )
    row = cursor.fetchone()
    if not row:
        cursor.close()
        conn.close()
        return False
    cursor.execute(
        "UPDATE pending_transactions SET state = %s WHERE id = %s", (state, row[0])
    )
    conn.commit()
    updated = cursor.rowcount > 0
    cursor.close()
    conn.close()
    return updated


def delete_pending(user_id: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM pending_transactions WHERE user_id = %s ORDER BY created_at DESC LIMIT 1",
        (user_id,),
    )
    row = cursor.fetchone()
    if not row:
        cursor.close()
        conn.close()
        return False
    cursor.execute("DELETE FROM pending_transactions WHERE id = %s", (row[0],))
    conn.commit()
    deleted = cursor.rowcount > 0
    cursor.close()
    conn.close()
    return deleted


# ── Manage-session helpers (edit/delete saved transactions) ───────────

def set_manage_session(user_id: str, transaction_id: int, state: str = "menu") -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO manage_sessions (user_id, transaction_id, state)
           VALUES (%s, %s, %s)
           ON CONFLICT (user_id) DO UPDATE
               SET transaction_id = EXCLUDED.transaction_id, state = EXCLUDED.state""",
        (user_id, transaction_id, state),
    )
    conn.commit()
    cursor.close()
    conn.close()


def get_manage_session(user_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM manage_sessions WHERE user_id = %s", (user_id,))
    row = cursor.fetchone()
    result = _as_dict(cursor, row) if row else None
    cursor.close()
    conn.close()
    return result


def clear_manage_session(user_id: str) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM manage_sessions WHERE user_id = %s", (user_id,))
    conn.commit()
    cursor.close()
    conn.close()


# ── Category helpers ──────────────────────────────────────────────────

def get_categories() -> list[str]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM categories ORDER BY name")
    rows = [r[0] for r in cursor.fetchall()]
    cursor.close()
    conn.close()
    return rows


def add_category(name: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO categories (name) VALUES (%s)", (name.strip(),))
        conn.commit()
        return True
    except pg8000.dbapi.DatabaseError as e:
        conn.rollback()
        # pgcode 23505 = unique_violation
        args = e.args[0] if e.args else {}
        if isinstance(args, dict) and args.get("C") == "23505":
            return False
        raise
    finally:
        cursor.close()
        conn.close()


# ── Transaction helpers ───────────────────────────────────────────────

def add_transaction(user_id: str, amount: float, category: str,
                    description: str = "", image_url: str = "",
                    source: str = "slip") -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO transactions
               (user_id, amount, category, description, image_url, source)
           VALUES (%s, %s, %s, %s, %s, %s)
           RETURNING id""",
        (user_id, amount, category, description, image_url, source),
    )
    trans_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()
    return trans_id


def get_monthly_total(user_id: str) -> float:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT COALESCE(SUM(amount), 0) FROM transactions
           WHERE user_id = %s
             AND TO_CHAR(created_at AT TIME ZONE 'Asia/Bangkok', 'YYYY-MM')
               = TO_CHAR(NOW() AT TIME ZONE 'Asia/Bangkok', 'YYYY-MM')""",
        (user_id,),
    )
    total = float(cursor.fetchone()[0])
    cursor.close()
    conn.close()
    return total


def get_all_transactions(user_id: str) -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM transactions WHERE user_id = %s ORDER BY created_at DESC",
        (user_id,),
    )
    result = _all_as_dicts(cursor)
    cursor.close()
    conn.close()
    return result


def get_recent_transactions(user_id: str, limit: int = 10) -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM transactions WHERE user_id = %s ORDER BY created_at DESC LIMIT %s",
        (user_id, limit),
    )
    result = _all_as_dicts(cursor)
    cursor.close()
    conn.close()
    return result


def get_transaction(user_id: str, transaction_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM transactions WHERE id = %s AND user_id = %s",
        (transaction_id, user_id),
    )
    row = cursor.fetchone()
    result = _as_dict(cursor, row) if row else None
    cursor.close()
    conn.close()
    return result


def update_transaction(user_id: str, transaction_id: int, **fields) -> bool:
    """Update one or more columns (amount, description, category) on a transaction."""
    allowed = {"amount", "description", "category"}
    fields = {k: v for k, v in fields.items() if k in allowed}
    if not fields:
        return False
    set_clause = ", ".join(f"{col} = %s" for col in fields)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"UPDATE transactions SET {set_clause} WHERE id = %s AND user_id = %s",
        (*fields.values(), transaction_id, user_id),
    )
    conn.commit()
    updated = cursor.rowcount > 0
    cursor.close()
    conn.close()
    return updated


def delete_transaction(user_id: str, transaction_id: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM transactions WHERE id = %s AND user_id = %s",
        (transaction_id, user_id),
    )
    conn.commit()
    deleted = cursor.rowcount > 0
    cursor.close()
    conn.close()
    return deleted


def get_monthly_summary(user_id: str) -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT category, SUM(amount) AS total, COUNT(*) AS count
           FROM transactions
           WHERE user_id = %s
             AND TO_CHAR(created_at AT TIME ZONE 'Asia/Bangkok', 'YYYY-MM')
               = TO_CHAR(NOW() AT TIME ZONE 'Asia/Bangkok', 'YYYY-MM')
           GROUP BY category
           ORDER BY total DESC""",
        (user_id,),
    )
    result = _all_as_dicts(cursor)
    cursor.close()
    conn.close()
    return result
