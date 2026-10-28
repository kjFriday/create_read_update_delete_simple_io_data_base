# ==== Generic Company Inc. portfolio ====================================
# Project: create_read_update_delete_simple_io_data_base | File: test_db.py
# About: Tests for the db CRUD layer, each on a fresh temporary database.
# Copyright (c) 2026 kjFriday | SPDX-License-Identifier: AGPL-3.0-only
# You may change this file under the AGPL-3.0. The stamp at the end marks
# the version kjFriday wrote. Verify with the portfolio's stamp.py --check.
# Reused code, if any, is mapped in PROVENANCE.md.
# ========================================================================

# ==== Generic Company Inc. portfolio ===============================================
# Project: create_read_update_delete_simple_io_data_base | File: test_db.py
# About: Tests for the db CRUD layer, each on a fresh temporary database.
# Copyright (c) 2026 kjFriday | SPDX-License-Identifier: AGPL-3.0-only
# You may change this file under the AGPL-3.0. The stamp at the end marks
# the version kjFriday wrote. Verify with the portfolio's stamp.py --check.
# Reused code, if any, is mapped in PROVENANCE.md.
# ========================================================================

"""Tests for the db CRUD layer, each on a fresh temporary database."""

import os
import sqlite3
import tempfile
import unittest

import db
import textsafe


class DbTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.old_path = db.DB_PATH
        db.DB_PATH = os.path.join(self.tmp.name, "test.db")
        db.init_db()

    def tearDown(self):
        db.DB_PATH = self.old_path
        self.tmp.cleanup()

    def test_create_read_update_delete(self):
        rid = db.create_row("customers", {"name": "Ada Reyes", "city": "Leeds"})
        self.assertEqual(db.get_row("customers", rid)["name"], "Ada Reyes")
        self.assertEqual(db.update_row("customers", rid, {"city": "York"}), 1)
        self.assertEqual(db.get_row("customers", rid)["city"], "York")
        self.assertEqual([r["id"] for r in db.list_rows("customers")], [rid])
        self.assertEqual(db.delete_row("customers", rid), 1)
        self.assertIsNone(db.get_row("customers", rid))

    def test_missing_row_counts_zero(self):
        self.assertEqual(db.update_row("customers", 99, {"city": "York"}), 0)
        self.assertEqual(db.delete_row("customers", 99), 0)

    def test_list_is_newest_first_and_limited(self):
        ids = [db.create_row("products", {"name": f"Kit {i}"}) for i in range(5)]
        self.assertEqual([r["id"] for r in db.list_rows("products", 2)], ids[:-3:-1])

    def test_offset_and_count(self):
        ids = [db.create_row("products", {"name": f"Kit {i}"}) for i in range(5)]
        self.assertEqual([r["id"] for r in db.list_rows("products", 2, 2)], [ids[2], ids[1]])
        self.assertEqual(db.count_rows("products"), 5)

    def test_create_rows_is_all_or_none(self):
        ids = db.create_rows("customers", [{"name": "Maria Garcia"}, {"name": "Kenji Sato"}])
        self.assertEqual([db.get_row("customers", i)["name"] for i in ids], ["Maria Garcia", "Kenji Sato"])
        with self.assertRaises(sqlite3.IntegrityError):
            db.create_rows("customers", [{"name": "Ana Silva"}, {"city": "no name"}])
        self.assertEqual(db.count_rows("customers"), 2)

    def test_unknown_table_raises_key_error(self):
        for call in (lambda: db.list_rows("nope"), lambda: db.create_row("nope", {"name": "x"})):
            with self.assertRaises(KeyError):
                call()

    def test_no_known_columns_raises_value_error(self):
        with self.assertRaises(ValueError):
            db.create_row("customers", {"shoe_size": 9})
        rid = db.create_row("customers", {"name": "Ben Park"})
        with self.assertRaises(ValueError):
            db.update_row("customers", rid, {"id": 5})

    def test_strings_are_cleaned_and_capped(self):
        rid = db.create_row("customers", {"name": "Cora\x1b[2J Okafor", "city": "z" * 500})
        row = db.get_row("customers", rid)
        self.assertEqual(row["name"], "Cora[2J Okafor")
        self.assertEqual(len(row["city"]), textsafe.LIMIT)

    def test_uncapped_columns_keep_their_length(self):
        payload = '{"note": "' + "x" * 1000 + '"}'
        rid = db.create_row("events", {"kind": "test", "payload": payload})
        self.assertEqual(db.get_row("events", rid)["payload"], payload)

    def test_not_null_refuses_none(self):
        rid = db.create_row("customers", {"name": "Dev Lind"})
        with self.assertRaises(sqlite3.IntegrityError):
            db.update_row("customers", rid, {"name": None})

    def test_referenced_row_cannot_be_deleted(self):
        cid = db.create_row("customers", {"name": "Eli Sato"})
        db.create_row("orders", {"customer_id": cid, "quantity": 1})
        with self.assertRaises(sqlite3.IntegrityError):
            db.delete_row("customers", cid)
        self.assertIsNotNone(db.get_row("customers", cid))


if __name__ == "__main__":
    unittest.main()

# ==== stamp v1 | author=kjFriday | hmac-sha256=926dddaceb00f117a5c5dd7b9187ff900d3935d1bba318d35237cbb2226c9e8e ====
