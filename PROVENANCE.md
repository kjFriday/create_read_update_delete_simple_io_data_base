# Provenance

Each adapted file and the staged source it came from. Sources are identified by their sha256 row in the staging `MANIFEST.tsv`, plus the path under their source tree. All code was ported to Python stdlib, cut by symbol name and then adapted. No source headers or comments were copied.

## Code

| File | Source (sha256) | Symbols | Adaptation |
|---|---|---|---|
| `seed.py` (`_mix`, `SALTS`, `_rng`) | `src/corridor/paper/Report.java` (`6816275F309B558F3F8C8D2FC3A0FCC99F0833436CEDA4B887D8222745E8AA48`) | `mix()` | Java to Python. The value is masked to 64 bits after each multiply and XOR, so it stays unsigned. Each record gets `random.Random(_mix(base_seed ^ salt, n))`, with a fixed integer salt per table. The signature is now `seed(base_seed=42)`. Checked against the splitmix64 reference outputs for state 0. |
| `textsafe.py`, `test_textsafe.py` | `src/mycelium/Safe.java` (`B65658B96FEF02ECC968BA98B2C8A2DEB23586BD26BAB0A2064F4A4E1A053272`) | `refused()`, `check()` | Works per character and removes refused characters instead of replacing them. Adds U+2028/2029 and the bidi controls U+202A-202E and U+2066-2069. Keeps tab and newline. Adds a length cap (`LIMIT = 240`). The tests use a neutral fixture string. |
| `sigil.py`, `test_sigil.py` | `src/ui/Sigil.java` (`F90BEC86A4F87669A670CE07713C4AAAE38E36A64B3862213328A6072F14ED81`) | `grid()`, `tint()`, plus the 6x6x6 cube from `rgb256` inlined | `tint()` returns an `(r, g, b)` tuple. The FILL comment is corrected to about 51.6% of cells lit. The port reproduces all three of the source's own test vectors exactly. The tests here use neutral names, with vectors regenerated from the port. |
| `api.py` (`edit_distance`, `suggest`, `_not_found`, `_body`) | `suggest.go` (`CA5E1F3D5330539C4DCE51140153B59C335E7FCDDE6240FFA92853D64FBD83F7`) | `editDistance()`, `suggest()` | Go to Python. The vocabulary is passed in (the table names). Both sides are lowercased. `suggest` returns the single closest name within 3 edits. `_body` now runs `textsafe.clean` on string values. |

`api.py` (the REST API) was retired in 0.2.0, when the programs started sharing the database by path; its rows below are kept as history, and the file stays in git history.

## Follow-up fixes (no staged source)

| File | Change |
|---|---|
| `api.py` | `_body` keeps the 240-character cap for ordinary text but cleans `events.payload` and `documents.path` without a cap (`UNCAPPED`), so JSON payloads and long paths are stored whole. `suggest` skips names whose length differs by more than the limit, so a very long path segment costs no Levenshtein pass. |
| `textsafe.py`, `test_textsafe.py` | A negative `limit` is treated as 0 instead of slicing from the end. Test added. |
| `db.py` | Each call now closes its connection (`_session()`), so the database file is not held open between calls. The schema and `connect()` are unchanged. |
| `seed.py` | `seed()` also removes stale `-wal` and `-shm` files before rebuilding, and can now be called repeatedly in one process. |
| `db.py` | String cleaning (`textsafe.clean`, `UNCAPPED`) moved here from `api._body`, so the GUI's writes are cleaned too. `create_row`/`update_row` raise `ValueError` when no known column is given. |
| `api.py` | `_body` only parses the JSON and refuses a body that is not an object; a negative `Content-Length` reads as 0. A bad `?limit` answers 400; constraint failures answer 409 instead of dropping the connection; a PATCH with no known columns answers 400, not 404. Row ids must be ASCII digits. The table list matches `/api/` with a query string. Tests: `test_api.py`, `test_db.py`. |
| `main.py` | Update sends blank fields as NULL, so a NOT NULL column refuses them instead of storing `''`. |

## Data (`data/`, format in `data/README.md`)

| File | Source (sha256) | Rows kept | Scrub |
|---|---|---|---|
| `languages.dat` | `gen/languages.dat` (`1B6B718B8D82133A450F60680C300E9BDDD0EBB2D18CCBC4ED1692E0AD09B820`) | 25 of 211 | The form column is relabelled as `category`, and the weight column as `tier`. The verdict column is dropped. |
| `theatres.tsv` | `theatres.tsv` (`29496700B51081C996BD31A6BEDC1AA39001E7BE79A08C38CBA0B75C4E73D703`) | 20 of 371 | Header comments are stripped and replaced by a plain column-header row. A `city` column was added. The venue data is Wikidata, CC0 1.0. |
| `stages.tsv` | `stages.tsv` (`198EB69EF4687E5BEC304D7D6C2E36967C82F9912923496DF9D54954FDEDCED1`) | 7 class rows, 7 weekday rows | Header comments are dropped. The class rows keep only class, seats and ticket price; all of the building-power columns are dropped. Only the weekday rows of the knob section are kept. |
| `seasons.tsv` | `seasons.tsv` (`F71708D4A9562ED527951A0AFC948C39D08540FBC88C18E9AB7067B2A4EDD4E3`) | 8 instants (2026-2027), 1 window, 1 day | Header comments, the source and line columns, and all scene rows are dropped. The window is renamed `AUTUMN SALE` and the day `LATE OPENING`. |
