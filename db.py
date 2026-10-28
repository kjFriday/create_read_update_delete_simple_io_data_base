# ==== Generic Company Inc. portfolio ====================================
# Project: create_read_update_delete_simple_io_data_base | File: db.py
# About: Generic Company Inc. data layer — the shared SQLite file every Generic Company program...
# Copyright (c) 2026 kjFriday | SPDX-License-Identifier: AGPL-3.0-only
# You may change this file under the AGPL-3.0. The stamp at the end marks
# the version kjFriday wrote. Verify with the portfolio's stamp.py --check.
# Reused code, if any, is mapped in PROVENANCE.md.
# ========================================================================

# ==== Generic Company Inc. portfolio ===============================================
# Project: create_read_update_delete_simple_io_data_base | File: db.py
# About: Generic Company Inc. data layer — the shared SQLite file every Generic Company program opens by path (see...
# Copyright (c) 2026 kjFriday | SPDX-License-Identifier: AGPL-3.0-only
# You may change this file under the AGPL-3.0. The stamp at the end marks
# the version kjFriday wrote. Verify with the portfolio's stamp.py --check.
# Reused code, if any, is mapped in PROVENANCE.md.
# ========================================================================

"""Generic Company Inc. data layer — the shared SQLite file every Generic Company program opens by path (see paths.py)."""

import os
import sqlite3
from contextlib import contextmanager

import paths
import textsafe

# a module attribute, so main() (--db) and the tests can point it elsewhere
DB_PATH = paths.resolve_db()

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
        ("body", "TEXT"),
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


def ddl():
    """The CREATE TABLE statements for SCHEMA, in order; export_mock.py ships them as mock/schema.sql."""
    out = []
    for table, cols in SCHEMA.items():
        body = ", ".join(f"{c} {t}" for c, t in cols)
        out.append(f"CREATE TABLE IF NOT EXISTS {table} (id INTEGER PRIMARY KEY AUTOINCREMENT, {body})")
    return out


def connect():
    folder = os.path.dirname(os.path.abspath(DB_PATH))
    os.makedirs(folder, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=5)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=5000")
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
        for statement in ddl():
            conn.execute(statement)


def list_rows(table, limit=500, offset=0):
    _check(table)
    with _session() as conn:
        sql = f"SELECT * FROM {table} ORDER BY id DESC LIMIT ? OFFSET ?"
        return [dict(r) for r in conn.execute(sql, (limit, offset))]


def count_rows(table):
    _check(table)
    with _session() as conn:
        return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


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


def create_rows(table, rows):
    """Insert many rows in one transaction (all or none); -> their ids, in order."""
    _check(table)
    ids = []
    with _session() as conn:
        for data in rows:
            cols, values = _known(table, data)
            cur = conn.execute(
                f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})",
                values,
            )
            ids.append(cur.lastrowid)
    return ids


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

# ==== stamp v1 | author=kjFriday | hmac-sha256=0691f91116a9869a09463ff4909b347ca1feb5e4d2d3de466908857191a0d1b7 ====
