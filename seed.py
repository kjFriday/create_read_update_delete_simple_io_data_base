"""Fill acme.db with deterministic mock data. ACME Inc. and everyone in it is fictional.

Each record gets its own generator, seeded by _mix(base_seed ^ table salt, record number), so a
change to one table's row count or draws never shifts the values in another table.
Products, cities and calendar events come from the files in data/ (see data/README.md).
"""

import csv
import json
import os
import random
from datetime import datetime, timedelta

import db

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
MASK = (1 << 64) - 1

# fixed per-table salts; never hash(), which is randomised per process for strings
SALTS = {"employees": 0x101, "customers": 0x202, "products": 0x303, "orders": 0x404, "tickets": 0x505, "events": 0x606}

FIRST = ["Ada", "Ben", "Cora", "Dev", "Eli", "Fay", "Gus", "Hana", "Ivo", "Juno", "Kai", "Lena", "Milo", "Nia", "Otto"]
LAST = ["Reyes", "Park", "Okafor", "Lind", "Moreau", "Sato", "Quinn", "Vale", "Hart", "Novak"]
ROLES = ["Support", "Support", "Sales", "Engineer", "Manager"]
TIER_PRICE = {"basic": (15, 40), "lite": (40, 90), "standard": (90, 180), "pro": (180, 400)}
ISSUES = ["Order arrived damaged", "Invoice question", "Can't log in", "Request refund", "Shipping delay", "Upgrade plan"]
WEEKDAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


def _mix(seed, number):
    """splitmix64 finaliser: one well-spread unsigned 64-bit value per (seed, number)."""
    z = (seed ^ ((number * 0x9E3779B97F4A7C15) & MASK)) & MASK
    z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & MASK
    z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & MASK
    return z ^ (z >> 31)


def _rng(base_seed, table, n):
    return random.Random(_mix(base_seed ^ SALTS[table], n))


def _rows(filename):
    with open(os.path.join(DATA, filename), encoding="utf-8") as f:
        return [line.rstrip("\n").split("\t") for line in f if line.strip()]


def load_products():
    """languages.dat: fixed width, name 0-36, year 36-42, category 42-54, tier 54-."""
    with open(os.path.join(DATA, "languages.dat"), encoding="utf-8") as f:
        return [{"name": line[:36].strip(), "year": line[36:42].strip(),
                 "category": line[42:54].strip(), "tier": line[54:].strip()} for line in f if line.strip()]


def load_venues():
    with open(os.path.join(DATA, "theatres.tsv"), encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def load_stages():
    """-> ({class: (seats, ticket_cents)}, [mon..sun multipliers])"""
    stages, days = {}, {}
    for row in _rows("stages.tsv"):
        if row[0] == "stage":
            stages[row[1]] = (int(row[2]), int(row[3]))
        elif row[0] == "day":
            days[row[1]] = float(row[2])
    return stages, [days[d] for d in WEEKDAYS]


def busy_day(rng, start, span, weekday):
    """A day in [start, start + span]; busier weekdays come up more often."""
    top = max(weekday)
    while True:
        when = start + timedelta(days=rng.randint(0, span))
        if rng.random() * top < weekday[when.weekday()]:
            return when


def name(rng):
    return f"{rng.choice(FIRST)} {rng.choice(LAST)}"


def email(n, domain):
    return n.lower().replace(" ", ".") + "@" + domain


def seed(base_seed=42):
    # start from an empty file; a leftover -wal/-shm must not be replayed into the new database
    for path in (db.DB_PATH, db.DB_PATH + "-wal", db.DB_PATH + "-shm"):
        if os.path.exists(path):
            os.remove(path)
    db.init_db()
    start = datetime(2026, 1, 1)
    now = start + timedelta(days=271)  # the seeded "today": later events are still pending
    venues = load_venues()
    stages, weekday = load_stages()

    employees = []
    for i in range(12):
        r = _rng(base_seed, "employees", i)
        n = name(r)
        employees.append(db.create_row("employees", {"name": n, "role": r.choice(ROLES), "email": email(n, "acme.example")}))

    customers = []
    for i in range(50):
        r = _rng(base_seed, "customers", i)
        n = name(r)
        customers.append(db.create_row("customers", {"name": n, "email": email(n, "mail.example"), "city": r.choice(venues)["city"]}))

    products = []
    for i, item in enumerate(load_products()):
        r = _rng(base_seed, "products", i)
        price = round(r.uniform(*TIER_PRICE[item["tier"]]), 2)
        products.append((db.create_row("products", {
            "name": f"{item['name']} Toolkit", "category": item["category"].title(), "price": price,
        }), price))

    for i in range(300):
        r = _rng(base_seed, "orders", i)
        pid, price = r.choice(products)
        qty = r.randint(1, 5)
        when = busy_day(r, start, 270, weekday) + timedelta(minutes=r.randint(0, 1439))
        oid = db.create_row("orders", {
            "customer_id": r.choice(customers), "product_id": pid, "quantity": qty,
            "total": round(price * qty, 2), "ordered_at": when.isoformat(timespec="minutes"),
        })
        db.create_row("events", {
            "kind": "order.created", "payload": json.dumps({"order_id": oid}),
            "status": "sent", "created_at": when.isoformat(timespec="minutes"),
        })

    for i in range(40):
        r = _rng(base_seed, "tickets", i)
        when = start + timedelta(days=r.randint(0, 270))
        db.create_row("tickets", {
            "customer_id": r.choice(customers), "assignee_id": r.choice(employees),
            "title": r.choice(ISSUES), "status": r.choice(["open", "open", "in_progress", "closed"]),
            "created_at": when.isoformat(timespec="minutes"),
        })

    # calendar rows from seasons.tsv; yearly rows are placed in the seeded year
    for kind, label, first, last in _rows("seasons.tsv"):
        if kind == "instant":
            payload = {"name": label.title(), "date": first}
        elif kind == "window":
            payload = {"name": label.title(), "start": f"{start.year}-{first}", "end": f"{start.year}-{last}"}
        else:
            payload = {"name": label.title(), "date": f"{start.year}-{first}"}
        when = datetime.fromisoformat(payload.get("date") or payload["start"])
        db.create_row("events", {
            "kind": f"calendar.{kind}", "payload": json.dumps(payload),
            "status": "sent" if when < now else "pending", "created_at": when.isoformat(timespec="minutes"),
        })

    # one evening show per venue, priced by its class and the weekday it falls on
    for i, venue in enumerate(venues):
        r = _rng(base_seed, "events", i)
        cls = venue["classes"].split("|")[0]
        seats, cents = stages[cls]
        when = busy_day(r, start, 364, weekday) + timedelta(hours=19, minutes=30)
        payload = {
            "venue": venue["name"], "city": venue["city"], "class": cls,
            "seats": int(venue["capacity"] or seats),
            "ticket": round(cents * weekday[when.weekday()] / 100, 2),
        }
        db.create_row("events", {
            "kind": "venue.show", "payload": json.dumps(payload),
            "status": "sent" if when < now else "pending", "created_at": when.isoformat(timespec="minutes"),
        })


if __name__ == "__main__":
    seed()
    print(f"seeded {db.DB_PATH}")
