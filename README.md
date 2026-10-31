# EconPulse Spain

A running read on the health of the Spanish economy, modelled on [econvitals.org](https://econvitals.org/).
Python fetches official data (INE, Eurostat, ECB…) and builds a static website that opens straight from disk
and can later be hosted anywhere. See [PLAN.md](PLAN.md) for the roadmap.

## Quick start (Windows)

Double-click **`update.bat`**. The first run sets up a Python environment; every run fetches the latest
data, rebuilds the site and opens `site/index.html` in your browser.

Or from a terminal:

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python -m econpulse update
```

## The site

- **Home** (`site/index.html`): 16 key-indicator tiles, "The economy in four questions" and three charts.
- **Section pages** (GDP, Labour market, Inflation, …): every indicator in that area. Charts and detailed tables come in Batches 4–6.
- **Data** (`site/data.html`): every series, its source and whether it is up to date.

Pages are plain HTML and work offline: Plotly is copied from the Python package, with no CDN. Light/dark
follows the system setting, and the moon button switches it.

## Commands

| Command | What it does |
|---|---|
| `python -m econpulse fetch` | Download every indicator into `data/` and print the latest values |
| `python -m econpulse fetch --only cpi,gdp` | Fetch just those indicators |
| `python -m econpulse list` | Print the latest values from data already saved (no download) |
| `python -m econpulse build` | Rebuild `site/` from data already saved |
| `python -m econpulse update` | Fetch, then build |
| `python -m econpulse status` | Freshness report: failures, series that stopped updating, per source |

The first fetch downloads full history (about 3 minutes, mostly 27 years of daily Banco de España data).
After that, only recent observations are downloaded and merged in (about 10 seconds).

## Layout

```
econpulse/            Python package
  indicators.yaml     the indicator registry: every series the site tracks
  sources/            one client per data provider: ine, eurostat, ecb, bde (Banco de España),
                      segsocial (Seguridad Social), ree (Red Eléctrica), fred, derived
  transforms.py       y/y, m/m, q/q, 3-month annualised, changes
  store.py            data/series/<id>.csv + data/catalog.json
  fetch.py            fetches everything; one failing source never stops the rest
  seasonal.py         EconPulse seasonal adjustment (STL), used by the sa_* transforms
  snapshot.py         latest values, changes and display strings
  questions.py        "The economy in four questions" on the home page
  charts.py           chart specifications (data and wording; colours come from the CSS theme)
  build.py            renders every page into site/ (chart data goes in site/data/*.js)
templates/            Jinja2 pages: base layout, home, section pages, data page
static/               style.css (light/dark tokens), app.js (theme toggle, Plotly charts)
data/                 fetched history (tracked in git)
site/                 build output, open site/index.html (not tracked)
tests/                pytest suite
```

## Adding an indicator

Add an entry to `econpulse/indicators.yaml` (the header comment explains each field), then run
`python -m econpulse fetch --only <id>`. No code changes are needed for series from a supported source.

- **INE:** use the *series* code (e.g. `IPC290750`), found on any INE table via the series' info link.
- **Eurostat:** dataset code plus `params` that fix every dimension except time.
- **ECB:** `FLOW/SERIES_KEY`, as shown on data.ecb.europa.eu.
- **Banco de España:** the series code from the first row of any table's CSV download (e.g. `DPUG0B1F0ZP`).
- **FRED:** the series id (e.g. `DCOILBRENTEU`).
- **Derived:** `subtract` or `divide` two indicators defined earlier in the file.

## Tests

```bash
.venv/Scripts/python -m pytest            # offline tests
.venv/Scripts/python -m pytest -m live    # also call the real APIs
```
