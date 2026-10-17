"""Tests for the REST API, over real HTTP against a server on a free port and a temporary database."""

import json
import os
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import api
import db


class QuietHandler(api.Handler):
    def log_message(self, *args):
        pass


class ApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        cls.old_path = db.DB_PATH
        db.DB_PATH = os.path.join(cls.tmp.name, "test.db")
        db.init_db()
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), QuietHandler)
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}/api"
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        db.DB_PATH = cls.old_path
        cls.tmp.cleanup()

    def call(self, method, path, body=None, raw=None, headers=None):
        """-> (status, decoded JSON body)"""
        data = raw if raw is not None else (None if body is None else json.dumps(body).encode())
        req = urllib.request.Request(self.base + path, data=data, method=method, headers=headers or {})
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status, json.loads(resp.read())
        except urllib.error.HTTPError as e:
            with e:
                return e.code, json.loads(e.read())

    def test_crud_cycle(self):
        code, out = self.call("POST", "/customers", {"name": "Fay Quinn", "city": "Bath"})
        self.assertEqual(code, 201)
        path = f"/customers/{out['id']}"
        self.assertEqual(self.call("GET", path)[1]["city"], "Bath")
        self.assertEqual(self.call("PATCH", path, {"city": "Wells"}), (200, {"updated": 1}))
        self.assertEqual(self.call("GET", path)[1]["city"], "Wells")
        self.assertEqual(self.call("DELETE", path), (200, {"deleted": 1}))
        self.assertEqual(self.call("GET", path)[0], 404)

    def test_table_list_ignores_query_string(self):
        code, out = self.call("GET", "/?x=1")
        self.assertEqual(code, 200)
        self.assertIn("customers", out["tables"])

    def test_bad_limit_is_400(self):
        for limit in ("abc", "0", "-1", "501", "²"):
            self.assertEqual(self.call("GET", "/customers?limit=" + urllib.request.quote(limit))[0], 400, limit)
        self.assertEqual(self.call("GET", "/customers?limit=3")[0], 200)

    def test_odd_digit_id_is_404(self):
        self.assertEqual(self.call("GET", "/customers/" + urllib.request.quote("²"))[0], 404)

    def test_unknown_table_suggests(self):
        code, out = self.call("GET", "/custmers")
        self.assertEqual((code, out.get("did_you_mean")), (404, "customers"))

    def test_no_known_columns_is_400(self):
        self.assertEqual(self.call("POST", "/customers", {"shoe_size": 9})[0], 400)
        rid = self.call("POST", "/customers", {"name": "Gus Vale"})[1]["id"]
        self.assertEqual(self.call("PATCH", f"/customers/{rid}", {"shoe_size": 9})[0], 400)

    def test_patch_or_delete_missing_row_is_404(self):
        self.assertEqual(self.call("PATCH", "/customers/9999", {"city": "Ely"})[0], 404)
        self.assertEqual(self.call("DELETE", "/customers/9999")[0], 404)

    def test_bad_body_is_400(self):
        self.assertEqual(self.call("POST", "/customers", raw=b"{not json")[0], 400)
        self.assertEqual(self.call("POST", "/customers", [1, 2])[0], 400)

    def test_constraint_failures_are_409(self):
        self.assertEqual(self.call("POST", "/customers", {"city": "no name"})[0], 409)
        cid = self.call("POST", "/customers", {"name": "Hana Hart"})[1]["id"]
        self.call("POST", "/orders", {"customer_id": cid, "quantity": 2})
        self.assertEqual(self.call("DELETE", f"/customers/{cid}")[0], 409)
        self.assertEqual(self.call("GET", f"/customers/{cid}")[0], 200)

    def test_strings_are_cleaned(self):
        rid = self.call("POST", "/customers", {"name": "Ivo\x9b2J Novak"})[1]["id"]
        self.assertEqual(self.call("GET", f"/customers/{rid}")[1]["name"], "Ivo2J Novak")


if __name__ == "__main__":
    unittest.main()
