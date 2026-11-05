"""Step 4 - SQLite storage."""
import hashlib
import sqlite3
import pandas as pd
from config import DB_PATH, ADMIN_EMAIL, ADMIN_PASSWORD

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, role TEXT DEFAULT 'admin');
CREATE TABLE IF NOT EXISTS readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT NOT NULL, hour INTEGER NOT NULL, room TEXT NOT NULL,
    temperature REAL, occupancy INTEGER, devices_on INTEGER, energy_kwh REAL, prev_energy REAL);
CREATE INDEX IF NOT EXISTS idx_readings ON readings(date, room, hour);
CREATE TABLE IF NOT EXISTS actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT, room TEXT, date TEXT, hour INTEGER,
    before_kwh REAL, after_kwh REAL, saved_kwh REAL, co2_kg REAL, note TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
"""


def conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def hash_password(password: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), b"pccoe-energy-salt", 100_000).hex()


def init_db():
    with conn() as c:
        c.executescript(SCHEMA)
        if not c.execute("SELECT 1 FROM users LIMIT 1").fetchone():
            c.execute("INSERT INTO users(email, password_hash) VALUES (?,?)", (ADMIN_EMAIL, hash_password(ADMIN_PASSWORD)))


def read_df(sql: str, params=()) -> pd.DataFrame:
    with conn() as c:
        return pd.read_sql_query(sql, c, params=params)


def execute(sql: str, params=()):
    with conn() as c:
        cur = c.execute(sql, params)
        return cur.lastrowid


def load_readings(df: pd.DataFrame, replace=True):
    with conn() as c:
        if replace:
            c.execute("DELETE FROM readings")
        df.to_sql("readings", c, if_exists="append", index=False)
