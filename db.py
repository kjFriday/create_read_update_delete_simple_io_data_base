"""ACME Inc. data layer — one SQLite file every ecosystem project reads through the API."""

import os
import sqlite3
from contextlib import contextmanager

import textsafe

DB_PATH = os.environ.get("ACME_DB", os.path.join(os.path.dirname(__file__), "acme.db"))

# table -> ordered (column, sql type); every table also gets `id INTEGER PRIMARY KEY`
SCHEMA = {
    "employees": [("name", "TEXT NOT NULL"), ("role", "TEXT"), ("email", "TEXT")],
    "customers": [("name", "TEXT NOT NULL"), ("email", "TEXT"), ("city", "TEXT")],
    "products": [("name", "TEXT NOT NULL"), ("category", "TEXT"), ("price", "REAL")],
    "orders": [
        ("customer_id", "INTEGER REFERENCES customers(id)"),
        ("product_id", "INTEGER REFERENCES products(id)"),
        ("quantity", "INTEGER"),
        ("total", "REAL"),
        ("ordered_at", "TEXT"),
    ],
    "tickets": [
        ("customer_id", "INTEGER REFERENCES customers(id)"),
        ("assignee_id", "INTEGER REFERENCES employees(id)"),
        ("title", "TEXT NOT NULL"),
        ("status", "TEXT DEFAULT 'open'"),
        ("created_at", "TEXT"),
    ],
    "documents": [("order_id", "INTEGER REFERENCES orders(id)"), ("kind", "TEXT"), ("path", "TEXT")],
    "events": [
        ("kind", "TEXT NOT NULL"),
        ("payload", "TEXT"),
        ("status", "TEXT DEFAULT 'pending'"),
        ("created_at", "TEXT"),
    ],
}


# columns that hold machine data (JSON, file paths): still cleaned, never cut short
UNCAPPED = {"payload", "path"}


def columns(table):
    return [name for name, _ in SCHEMA[table]]


def _check(table):
    if table not in SCHEMA:
        raise KeyError(table)


def _known(table, data):
    """The table's columns present in data, cleaned; every write path (API and GUI) goes through here."""
    cols = [c for c in columns(table) if c in data]
    if not cols:
        raise ValueError("no known columns")
    values = [
        textsafe.clean(data[c], None if c in UNCAPPED else textsafe.LIMIT) if isinstance(data[c], str) else data[c]
        for c in cols
    ]
    return cols, values


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def _session():
    """A connection that commits (or rolls back) and is then closed, so the file is not held open."""
    conn = connect()
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def init_db():
    with _session() as conn:
        for table, cols in SCHEMA.items():
            body = ", ".join(f"{c} {t}" for c, t in cols)
            conn.execute(f"CREATE TABLE IF NOT EXISTS {table} (id INTEGER PRIMARY KEY AUTOINCREMENT, {body})")


def list_rows(table, limit=500):
    _check(table)
    with _session() as conn:
        return [dict(r) for r in conn.execute(f"SELECT * FROM {table} ORDER BY id DESC LIMIT ?", (limit,))]


def get_row(table, row_id):
    _check(table)
    with _session() as conn:
        r = conn.execute(f"SELECT * FROM {table} WHERE id = ?", (row_id,)).fetchone()
        return dict(r) if r else None


def create_row(table, data):
    _check(table)
    cols, values = _known(table, data)
    with _session() as conn:
        cur = conn.execute(
            f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})",
            values,
        )
        return cur.lastrowid


def update_row(table, row_id, data):
    _check(table)
    cols, values = _known(table, data)
    with _session() as conn:
        cur = conn.execute(
            f"UPDATE {table} SET {', '.join(c + ' = ?' for c in cols)} WHERE id = ?",
            values + [row_id],
        )
        return cur.rowcount


def delete_row(table, row_id):
    _check(table)
    with _session() as conn:
        return conn.execute(f"DELETE FROM {table} WHERE id = ?", (row_id,)).rowcount
