"""ACME Inc. REST API (stdlib only). Other ecosystem projects read and write through this.

GET    /api/                 -> table list
GET    /api/{table}          -> rows (?limit=N)
GET    /api/{table}/{id}     -> one row
POST   /api/{table}          -> create, returns {"id": n}
PATCH  /api/{table}/{id}     -> update
DELETE /api/{table}/{id}     -> delete

An unknown table answers 404 with "did_you_mean" when a table name is within 3 edits.
String values in POST/PATCH bodies pass through textsafe.clean before they reach the database;
they are capped at textsafe.LIMIT characters, except the UNCAPPED columns (events.payload, documents.path).
"""

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import db
import textsafe

HOST = os.environ.get("ACME_HOST", "127.0.0.1")
PORT = int(os.environ.get("ACME_PORT", "8700"))

# columns that hold machine data (JSON, file paths): still cleaned, never cut short
UNCAPPED = {"payload", "path"}


def edit_distance(a, b):
    """Plain Levenshtein distance, counted in characters."""
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(cur[j - 1] + 1, prev[j] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def suggest(miss, vocab, limit=3):
    """The closest word in vocab within `limit` edits (ties go alphabetically), or None."""
    m = miss.strip().lower()
    # the distance is at least the length gap, so far-off words are skipped before the O(n*m) pass
    scored = sorted((edit_distance(m, w.lower()), w) for w in vocab if abs(len(m) - len(w)) <= limit)
    return scored[0][1] if m and scored and scored[0][0] <= limit else None


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body):
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _route(self):
        url = urlparse(self.path)
        parts = [p for p in url.path.split("/") if p]
        if not parts or parts[0] != "api" or len(parts) > 3:
            return None, None, url
        table = parts[1] if len(parts) > 1 else None
        if table is not None and table not in db.SCHEMA:
            return False, None, url
        row_id = int(parts[2]) if len(parts) == 3 and parts[2].isdigit() else None
        if len(parts) == 3 and row_id is None:
            return None, None, url
        return table, row_id, url

    def _not_found(self):
        parts = [p for p in urlparse(self.path).path.split("/") if p]
        body = {"error": "not found"}
        if len(parts) > 1 and parts[0] == "api" and parts[1] not in db.SCHEMA:
            hint = suggest(parts[1], db.SCHEMA)
            if hint:
                body["did_you_mean"] = hint
        return self._send(404, body)

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        data = json.loads(self.rfile.read(n) or b"{}")
        return {
            k: textsafe.clean(v, None if k in UNCAPPED else textsafe.LIMIT) if isinstance(v, str) else v
            for k, v in data.items()
        }

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, DELETE")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        table, row_id, url = self._route()
        if table is None and self.path.rstrip("/") == "/api":
            return self._send(200, {"company": "ACME Inc. (fictional)", "tables": {t: db.columns(t) for t in db.SCHEMA}})
        if not table:
            return self._not_found()
        if row_id is None:
            limit = int(parse_qs(url.query).get("limit", ["500"])[0])
            return self._send(200, db.list_rows(table, limit))
        row = db.get_row(table, row_id)
        return self._send(200, row) if row else self._send(404, {"error": "not found"})

    def do_POST(self):
        table, row_id, _ = self._route()
        if not table or row_id is not None:
            return self._not_found()
        try:
            return self._send(201, {"id": db.create_row(table, self._body())})
        except Exception as e:  # bad JSON or constraint failure
            return self._send(400, {"error": str(e)})

    def do_PATCH(self):
        table, row_id, _ = self._route()
        if not table or row_id is None:
            return self._not_found()
        try:
            n = db.update_row(table, row_id, self._body())
        except Exception as e:
            return self._send(400, {"error": str(e)})
        return self._send(200, {"updated": n}) if n else self._send(404, {"error": "not found"})

    def do_DELETE(self):
        table, row_id, _ = self._route()
        if not table or row_id is None:
            return self._not_found()
        n = db.delete_row(table, row_id)
        return self._send(200, {"deleted": n}) if n else self._send(404, {"error": "not found"})


def serve():
    db.init_db()
    print(f"ACME Inc. API on http://{HOST}:{PORT}/api/")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()


if __name__ == "__main__":
    serve()
