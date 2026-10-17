# data/

Small, plain-text inputs for `seed.py`. UTF-8, LF line endings. The data files hold no comments. Their formats are documented here.

## languages.dat: product catalog (fixed width)

Each row becomes one product, named `<name> Toolkit`.

| Columns | Field | Values |
|---|---|---|
| 1-36 | name | language name |
| 37-42 | year | first release year; may read `c.YYYY` or `unkn` |
| 43-54 | category | `compiled`, `managed`, `interpreted`, `transpiled`, `embedded` |
| 55- | tier | `basic`, `lite`, `standard`, `pro`; sets the price band in `seed.py` |

## theatres.tsv: venues and customer cities (tab-separated, header row)

`qid  name  city  lat  lon  capacity  classes`

- `qid`, `name`, `lat`, `lon`, `capacity` and `classes` come from Wikidata (CC0 1.0).
- `capacity` is blank where Wikidata has none. `seed.py` then uses the seat count from `stages.tsv`.
- `classes` is `|`-separated. The first entry is the venue's class.
- `city` was added for this demo. Customers take their `city` from a venue.

## stages.tsv: venue classes and weekday demand (tab-separated, two row kinds)

- `stage  class  seats  ticket_cents`: the default seat count and ticket price for a venue class.
- `day  mon..sun  multiplier`: how busy each weekday is compared with an average day. Order dates favour busy days, and show ticket prices are scaled by the day's multiplier.

The numbers are invented starting values.

## first_names.txt, last_names.txt: people (one name per line)

Self-authored lists of common given names and surnames from many languages. `seed.py` pairs one of each
at random for every employee and customer, redrawing until the pair is unused, so names are realistic but
belong to no one. Emails are built from the name on the reserved `.example` domains.

Free text (ticket titles after the issue type, ticket bodies, order notes) is lorem ipsum from `lorem.py`.

## seasons.tsv: calendar events (tab-separated, three row kinds)

- `instant  NAME  yyyy-mm-dd  -`: a solstice or equinox (factual dates).
- `window  NAME  mm-dd  mm-dd`: a yearly promotion window. Both days are inside the window.
- `day  NAME  mm-dd  -`: a one-day yearly promotion.

`seed.py` turns each row into an `events` row of kind `calendar.instant`, `calendar.window` or `calendar.day`.
