import os
import psycopg2
import psycopg2.extras
import psycopg2.errors

DATABASE_URL = os.getenv("DATABASE_URL", "")


def get_connection() -> psycopg2.extensions.connection:
    """Return a psycopg2 connection."""
    return psycopg2.connect(DATABASE_URL)


def init_db():
    """Create all required tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id          SERIAL PRIMARY KEY,
            name        TEXT NOT NULL UNIQUE,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
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

    # Seed default categories if table is empty
    cursor.execute("SELECT COUNT(*) FROM categories")
    existing = cursor.fetchone()[0]
    if existing == 0:
        default_cats = ["Food", "Transport", "Bills", "Shopping", "Entertainment", "Health"]
        for cat in default_cats:
            cursor.execute(
                "INSERT INTO categories (name) VALUES (%s) ON CONFLICT DO NOTHING", (cat,)
            )

    conn.commit()
    cursor.close()
    conn.close()


# ── Pending transaction helpers ──────────────────────────────────────

def add_pending(user_id: str, amount: float, description: str, image_url: str,
                raw_ocr: str = "") -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO pending_transactions (user_id, amount, description, image_url, state, raw_ocr)
           VALUES (%s, %s, %s, %s, 'awaiting_category', %s) RETURNING id""",
        (user_id, amount, description, image_url, raw_ocr),
    )
    pending_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()
    return pending_id


def get_pending(user_id: str):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute(
        "SELECT * FROM pending_transactions WHERE user_id = %s ORDER BY created_at DESC LIMIT 1",
        (user_id,),
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return dict(row) if row else None


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
        "UPDATE pending_transactions SET state = %s WHERE id = %s",
        (state, row[0]),
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


# ── Category helpers ─────────────────────────────────────────────────

def get_categories() -> list[str]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM categories ORDER BY name")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [row[0] for row in rows]


def add_category(name: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO categories (name) VALUES (%s)", (name.strip(),))
        conn.commit()
        return True
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


# ── Transaction helpers ──────────────────────────────────────────────

def add_transaction(user_id: str, amount: float, category: str,
                    description: str = "", image_url: str = "",
                    source: str = "slip") -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO transactions (user_id, amount, category, description, image_url, source)
           VALUES (%s, %s, %s, %s, %s, %s) RETURNING id""",
        (user_id, amount, category, description, image_url, source),
    )
    trans_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()
    return trans_id


def get_monthly_total(user_id: str) -> float:
    """Sum of current month's transactions for the user."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT COALESCE(SUM(amount), 0) FROM transactions
           WHERE user_id = %s
             AND TO_CHAR(created_at AT TIME ZONE 'Asia/Bangkok', 'YYYY-MM')
               = TO_CHAR(NOW() AT TIME ZONE 'Asia/Bangkok', 'YYYY-MM')""",
        (user_id,),
    )
    total = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return float(total)


def get_all_transactions(user_id: str) -> list[dict]:
    """Return all transactions for the user, newest first."""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute(
        "SELECT * FROM transactions WHERE user_id = %s ORDER BY created_at DESC",
        (user_id,),
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [dict(r) for r in rows]


def get_monthly_summary(user_id: str) -> list[dict]:
    """Return per-category totals for the current month."""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
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
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [dict(r) for r in rows]
