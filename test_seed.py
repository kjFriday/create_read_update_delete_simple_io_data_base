"""Seed and mock-export checks on one temporary database (seeding takes a few seconds, so it runs once)."""

import json
import os
import random
import tempfile
import unittest

import db
import export_mock
import lorem
import seed


class SeedTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        cls.old_path = db.DB_PATH
        db.DB_PATH = os.path.join(cls.tmp.name, "acme.db")
        seed.seed()

    @classmethod
    def tearDownClass(cls):
        db.DB_PATH = cls.old_path
        cls.tmp.cleanup()

    def test_counts(self):
        for table, n in seed.COUNTS.items():
            self.assertEqual(db.count_rows(table), n, table)
        self.assertEqual(db.count_rows("documents"), seed.COUNTS["orders"])

    def test_people_have_unique_two_part_names(self):
        names = [r["name"] for t in ("employees", "customers") for r in db.list_rows(t, -1)]
        self.assertEqual(len(names), len(set(names)))
        for n in names:
            first, last = n.split(" ")
            self.assertIn(first, seed.FIRST)
            self.assertIn(last, seed.LAST)

    def test_ticket_text_is_lorem_within_limit(self):
        vocab = set(lorem.WORDS)
        for t in db.list_rows("tickets", 50):
            issue, filler = t["title"].split(": ", 1)
            self.assertIn(issue, seed.ISSUES)
            self.assertTrue(set(filler.split()) <= vocab)
            self.assertLessEqual(len(t["body"]), 240)

    def test_recent_events_wait_for_the_dispatcher(self):
        events = db.list_rows("events", -1)
        pending = [e for e in events if e["status"] == "pending" and e["kind"] in ("order.created", "ticket.created")]
        self.assertTrue(pending)
        self.assertTrue(all(e["created_at"] >= "2026-09-26" for e in pending))
        for e in events:
            if e["kind"] in ("order.created", "ticket.created"):
                self.assertIn("customer_id", json.loads(e["payload"]))

    def test_export_slices_keep_references(self):
        out = os.path.join(self.tmp.name, "root")
        for project in export_mock.snapshots():
            os.makedirs(os.path.join(out, project))
        export_mock.export(out)

        def load(project, table):
            with open(os.path.join(out, project, "mock", f"{table}.json"), encoding="utf-8") as f:
                return json.load(f)

        tracker = "simple_ticket_tracker"
        customers = {c["id"] for c in load(tracker, "customers")}
        staff = {e["id"] for e in load(tracker, "employees")}
        for t in load(tracker, "tickets"):
            self.assertIn(t["customer_id"], customers)
            self.assertTrue(t["assignee_id"] is None or t["assignee_id"] in staff)
        orders = {o["id"] for o in load("document_mover_and_changer", "orders")}
        self.assertTrue(all(d["order_id"] in orders for d in load("document_mover_and_changer", "documents")))
        authors = {e["id"] for e in load("content_management_system", "employees")}
        self.assertTrue(all(p["author_id"] in authors for p in load("content_management_system", "posts")))


class LoremTest(unittest.TestCase):
    def test_same_seed_same_text(self):
        self.assertEqual(lorem.paragraph(random.Random(7)), lorem.paragraph(random.Random(7)))

    def test_sentence_shape_and_limit(self):
        r = random.Random(1)
        s = lorem.sentence(r, 3, 3)
        self.assertTrue(s[0].isupper() and s.endswith(".") and len(s.split()) == 3)
        for i in range(50):
            self.assertLessEqual(len(lorem.paragraph(random.Random(i), 5, 9, limit=60)), 61)


if __name__ == "__main__":
    unittest.main()
