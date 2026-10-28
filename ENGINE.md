# The Generic Company engine

**Generic Company** stands for **American Company Management Engine**. The engine is not one program. It is the
seven Generic Company programs and the contracts they share. Generic Company Inc. and all its data are fictional.

## The one rule

**Every program runs on its own.** None of them starts, calls, imports or waits for another one at
run time. If the shared database is missing, a program runs on its own `mock/` snapshot and says so.
The programs share **data and file formats**, never code or processes. Each one can be written in
Python, Go or Rust.

The hub (this project) owns the contracts below. When a contract changes, change it here first, then
in `db.py` / `export_mock.py`, and then in each program.

## Contracts

### 1. The database

- One SQLite file. The hub creates it, and its schema is `db.py` `SCHEMA`. No other program changes
  the schema.
- Path, in this order: `--db PATH`, the `GENERIC_COMPANY_DB` environment variable, the program's saved setting,
  then `%LOCALAPPDATA%\Generic Company Inc\generic_company.db`.
- Each program writes only the rows it owns:

| Program | Writes |
|---|---|
| CRUD Hub | every table (schema and seed) |
| Doc Pipeline | `documents` rows, `documents.generated` events |
| Notify Hub | `events.status` |
| Ticket Tracker | `tickets` |
| Journal, Data Dash | nothing |

- If the schema does not match what a program expects, the program falls back to its snapshot. It
  never migrates the database itself.

### 2. The mock snapshot (JSON)

- `mock/<table>.json` holds a JSON array of row objects, with the same column names and ids as the
  database. `mock/schema.sql` is the hub's `CREATE TABLE` statements, used for tests.
- Made only by `export_mock.py`. Never edit a snapshot by hand.
- Each program keeps its own copy, so it can run alone.

### 3. Settings (JSON)

- `%LOCALAPPDATA%\Generic Company Inc\<app id>\settings.json` is a JSON object: `{"db": "<path>", "version": 1}`.
- Unknown keys are kept. Writes go to a temp file that is then swapped in.

### 4. Install (JSON)

- `install.json` marker in the install folder: `app_id`, `name`, `version`, `install_dir`, the files
  copied, the shortcuts and the Apps & features entry.
- Generic Company Wizard Maker's `setup.exe` writes the same marker, so either installer can take over an
  install made by the other.
- Flags every program accepts: `--db`, `--install`, `--uninstall`, `--root DIR`, `--version`,
  `--quiet`, `--smoke FILE`.

### 5. Identity

| Program | App id | Language |
|---|---|---|
| CRUD Hub | `GenericCompany.Hub` | Python |
| Doc Pipeline | `GenericCompany.DocPipe` | Python |
| Journal | `GenericCompany.CMS` | Go |
| Notify Hub | `GenericCompany.Notify` | Go |
| Ticket Tracker | `GenericCompany.Tickets` | Rust |
| Data Dash | `GenericCompany.Dash` | Rust |
| Wizard Maker | `GenericCompany.Wizard` | Go |

Title bar: `Generic Company Inc. — <name> <version>`.

## Paring down (small, low-effort steps)

Because the programs are self-contained, some code is repeated on purpose: each language pair carries
its own copy of the installer and the path rules. Work in this order, one step per sitting:

1. **Conformance, not sharing.** Add a test in each program that checks it against these contracts:
   path order, settings shape, snapshot shape, owned rows. When a copy drifts, its test fails, and
   the copies never have to be merged.
2. **Same-language pairs stay in sync.** The Python pair (hub and docpipe), the Go pair (Journal and
   Notify) and the Rust pair (Tracker and Dash) each carry a near-identical installer. Edit one, then
   copy the change to its twin, and let the conformance test show anything you missed.
3. **Move core logic out of the windows.** Keep each program's logic in functions that take data and
   return data. The window only calls them. Refactor only the core.
4. **Start where it is easiest:** Python (hub, docpipe), then Go, and leave Rust and the Wizard Maker
   for last.
