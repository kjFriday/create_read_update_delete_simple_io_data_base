# ==== Generic Company Inc. portfolio ====================================
# Project: create_read_update_delete_simple_io_data_base | File: test_schema_export.py
# About: ==== Generic Company Inc. portfolio ===============================================...
# Copyright (c) 2026 kjFriday | SPDX-License-Identifier: AGPL-3.0-only
# You may change this file under the AGPL-3.0. The stamp at the end marks
# the version kjFriday wrote. Verify with the portfolio's stamp.py --check.
# Reused code, if any, is mapped in PROVENANCE.md.
# ========================================================================

# ==== Generic Company Inc. portfolio ===============================================
# Project: create_read_update_delete_simple_io_data_base | File: test_schema_export.py
# About: Tests for schema_export.py.
# Copyright (c) 2026 kjFriday | SPDX-License-Identifier: AGPL-3.0-only
# You may change this file under the AGPL-3.0. The stamp at the end marks
# the version kjFriday wrote. Verify with the portfolio's stamp.py --check.
# Reused code, if any, is mapped in PROVENANCE.md.
# ========================================================================

import os
import sqlite3
import tempfile
import unittest

import db
import export_mock


def tables(conn):
    return conn.execute("SELECT name, sql FROM sqlite_master WHERE type = 'table' ORDER BY name").fetchall()


class SchemaExportTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old_path = db.DB_PATH
        db.DB_PATH = os.path.join(self.tmp.name, "hub.db")

    def tearDown(self):
        db.DB_PATH = self.old_path
        self.tmp.cleanup()

    def test_schema_sql_builds_the_same_tables(self):
        db.init_db()
        hub = sqlite3.connect(db.DB_PATH)
        copy = sqlite3.connect(":memory:")
        copy.executescript(export_mock.schema_sql())
        self.assertEqual(tables(copy), tables(hub))
        self.assertEqual(len([n for n, _ in tables(copy) if n != "sqlite_sequence"]), len(db.SCHEMA))
        hub.close()
        copy.close()

    def test_one_statement_per_table(self):
        sql = export_mock.schema_sql()
        self.assertTrue(sql.startswith("--"))
        self.assertEqual(sql.count("CREATE TABLE"), len(db.SCHEMA))
        self.assertTrue(all(s.endswith(")") for s in db.ddl()))


if __name__ == "__main__":
    unittest.main()

# ==== stamp v1 | author=kjFriday | hmac-sha256=1f094f7a01ab1f528f0af15950d42db64efa10b9d9156b375b9542f479f29afa ====
