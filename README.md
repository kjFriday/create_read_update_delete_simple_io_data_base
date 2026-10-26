<img src="icon/app-256.png" width="64" height="64" alt="" style="image-rendering: pixelated">

# ACME CRUD Hub

The desktop program that owns ACME Inc.'s shared database: one tab per table (employees, customers,
products, orders, tickets, documents, events) with Add / Update / Delete. ACME Inc. and all its data
are fictional. Python 3.10+, standard library only (tkinter, sqlite3).

ACME stands for **American Company Management Engine**. The hub is the engine's home: it owns the
contracts every program shares, written down in [ENGINE.md](ENGINE.md).

The other five ACME programs open the same SQLite file **by path**; nothing else connects them. The
hub creates the file and its schema (`db.py` `SCHEMA`), and **File → Seed demo data** fills it with
the deterministic mock data from `seed.py` (after saving a dated backup copy next to it).

## Run

```bash
python main.py
```

The database is, in order: `--db PATH`, the `ACME_DB` environment variable, the path saved with
**File → Database…**, or `%LOCALAPPDATA%\ACME Inc\acme.db`.

## Install

```bash
python main.py --install
```

Installs for the current user (no admin rights): copies the program to
`%LOCALAPPDATA%\Programs\ACME Inc\ACME CRUD Hub\`, adds **ACME Inc → ACME CRUD Hub** to the Start menu
(`--desktop-shortcut` adds one on the desktop too) and lists it in **Apps & features**, where it can be
uninstalled. Or:

```bash
python main.py --uninstall
```

Uninstalling never deletes the database (`--purge` also removes the hub's saved settings). The
shortcut runs `pythonw.exe` from the Python that installed it, so reinstall after upgrading Python.
`--root DIR` does all of this inside DIR instead (the registry entry goes to `DIR\registry.json`).

Other flags: `--version`, `--smoke FILE` (open the window, write a JSON report, close).

`wizard-maker.exe build setup.json` (ACME Wizard Maker) makes the setup, `dist\ACME CRUD Hub-0.2.0-setup.exe`.

## Seed and snapshots

```bash
python seed.py
```

`seed.py --fresh` rebuilds the file from nothing (byte-identical every run); `--db PATH` picks the
file. `python export_mock.py` writes each sibling project's `mock/` snapshot, including
`mock/schema.sql`, so each runs on its own.

## Tests

```bash
python -m unittest discover
```

## Icon

Silk "database" by Mark James, CC BY 2.5, enlarged by nearest-neighbour; see `icon/README.md`.

## License

AGPL-3.0. Reused code is mapped to its sources in `PROVENANCE.md`.
