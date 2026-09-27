"""
auth.py — Multi-user authentication for AI Energy Enterprise
Real password hashing (bcrypt) + persistent user storage (SQLite).
This is a first step; the same users table can later be moved to
PostgreSQL/Firebase without changing the app.py calling code.
"""

import sqlite3
import re
from contextlib import contextmanager

import bcrypt

DB_FILE = "users.db"


# ================= DB CONNECTION =================
@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_FILE)
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """Create the users table if it doesn't exist yet. Safe to call every run."""
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                name TEXT,
                company TEXT,
                country TEXT,
                city TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()


# ================= HELPERS =================
def is_valid_email(email: str) -> bool:
    return re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email or "") is not None


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except Exception:
        return False


# ================= PUBLIC API =================
def register_user(email: str, password: str, name: str, company: str, country: str, city: str):
    """
    Returns (success: bool, message: str)
    """
    email = (email or "").strip().lower()

    if not is_valid_email(email):
        return False, "⚠️ البريد الإلكتروني غير صحيح."
    if not password or len(password) < 6:
        return False, "⚠️ خاص الباسوورد يكون 6 خانات أو كثر."
    if not name or not company:
        return False, "⚠️ عافاك عمر اسم المدير و اسم الشركة."

    init_db()
    with get_connection() as conn:
        existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            return False, "⚠️ هاد البريد الإلكتروني مسجل من قبل. جرب تدخل (Login)."

        conn.execute(
            """INSERT INTO users (email, password_hash, name, company, country, city)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (email, hash_password(password), name.strip(), company.strip(), country, city),
        )
        conn.commit()

    return True, "✅ تم إنشاء الحساب بنجاح! دابا تقدر تدخل من Login."


def authenticate(email: str, password: str):
    """
    Returns the user dict on success, or None on failure.
    """
    email = (email or "").strip().lower()
    if not email or not password:
        return None

    init_db()
    with get_connection() as conn:
        row = conn.execute(
            """SELECT id, email, password_hash, name, company, country, city
               FROM users WHERE email = ?""",
            (email,),
        ).fetchone()

    if not row:
        return None

    user_id, db_email, password_hash, name, company, country, city = row
    if not verify_password(password, password_hash):
        return None

    return {
        "id": user_id,
        "email": db_email,
        "name": name,
        "company": company,
        "country": country,
        "city": city,
    }


def change_password(email: str, old_password: str, new_password: str):
    """
    Returns (success: bool, message: str)
    """
    user = authenticate(email, old_password)
    if not user:
        return False, "⚠️ الباسوورد القديم غير صحيح."
    if not new_password or len(new_password) < 6:
        return False, "⚠️ خاص الباسوورد الجديد يكون 6 خانات أو كثر."

    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET password_hash = ? WHERE email = ?",
            (hash_password(new_password), email.strip().lower()),
        )
        conn.commit()
    return True, "✅ تبدل الباسوورد بنجاح.""""
auth.py — Multi-user authentication for AI Energy Enterprise
Real password hashing (bcrypt) + persistent user storage (SQLite).
This is a first step; the same users table can later be moved to
PostgreSQL/Firebase without changing the app.py calling code.
"""

import sqlite3
import re
from contextlib import contextmanager

import bcrypt

DB_FILE = "users.db"


# ================= DB CONNECTION =================
@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_FILE)
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """Create the users table if it doesn't exist yet. Safe to call every run."""
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                name TEXT,
                company TEXT,
                country TEXT,
                city TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()


# ================= HELPERS =================
def is_valid_email(email: str) -> bool:
    return re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email or "") is not None


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except Exception:
        return False


# ================= PUBLIC API =================
def register_user(email: str, password: str, name: str, company: str, country: str, city: str):
    """
    Returns (success: bool, message: str)
    """
    email = (email or "").strip().lower()

    if not is_valid_email(email):
        return False, "⚠️ البريد الإلكتروني غير صحيح."
    if not password or len(password) < 6:
        return False, "⚠️ خاص الباسوورد يكون 6 خانات أو كثر."
    if not name or not company:
        return False, "⚠️ عافاك عمر اسم المدير و اسم الشركة."

    init_db()
    with get_connection() as conn:
        existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            return False, "⚠️ هاد البريد الإلكتروني مسجل من قبل. جرب تدخل (Login)."

        conn.execute(
            """INSERT INTO users (email, password_hash, name, company, country, city)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (email, hash_password(password), name.strip(), company.strip(), country, city),
        )
        conn.commit()

    return True, "✅ تم إنشاء الحساب بنجاح! دابا تقدر تدخل من Login."


def authenticate(email: str, password: str):
    """
    Returns the user dict on success, or None on failure.
    """
    email = (email or "").strip().lower()
    if not email or not password:
        return None

    init_db()
    with get_connection() as conn:
        row = conn.execute(
            """SELECT id, email, password_hash, name, company, country, city
               FROM users WHERE email = ?""",
            (email,),
        ).fetchone()

    if not row:
        return None

    user_id, db_email, password_hash, name, company, country, city = row
    if not verify_password(password, password_hash):
        return None

    return {
        "id": user_id,
        "email": db_email,
        "name": name,
        "company": company,
        "country": country,
        "city": city,
    }


def change_password(email: str, old_password: str, new_password: str):
    """
    Returns (success: bool, message: str)
    """
    user = authenticate(email, old_password)
    if not user:
        return False, "⚠️ الباسوورد القديم غير صحيح."
    if not new_password or len(new_password) < 6:
        return False, "⚠️ خاص الباسوورد الجديد يكون 6 خانات أو كثر."

    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET password_hash = ? WHERE email = ?",
            (hash_password(new_password), email.strip().lower()),
        )
        conn.commit()
    return True, "✅ تبدل الباسوورد بنجاح."
