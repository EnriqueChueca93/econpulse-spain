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

## Commands

| Command | What it does |
|---|---|
| `python -m econpulse fetch` | Download every indicator into `data/` and print the latest values |
| `python -m econpulse fetch --only cpi,gdp` | Fetch just those indicators |
| `python -m econpulse list` | Print the latest values from data already saved (no download) |
| `python -m econpulse build` | Rebuild `site/` from data already saved |
| `python -m econpulse update` | Fetch, then build |

## Layout

```
econpulse/            Python package
  indicators.yaml     the indicator registry: every series the site tracks
  sources/            one client per data provider (ine, eurostat, ecb, derived)
  transforms.py       y/y, m/m, q/q, 3-month annualised, changes
  store.py            data/series/<id>.csv + data/catalog.json
  fetch.py            fetches everything; one failing source never stops the rest
  snapshot.py         latest values, changes and display strings
  build.py            writes site/ (data goes in site/data/snapshot.js)
templates/, static/   HTML template, CSS and JavaScript for the site
data/                 fetched history (tracked in git)
site/                 build output, open site/index.html (not tracked)
tests/                pytest suite
```

## Adding an indicator

Add an entry to `econpulse/indicators.yaml` (the header comment explains each field), then run
`python -m econpulse fetch --only <id>`. No code changes are needed for INE, Eurostat or ECB series.

- **INE:** use the *series* code (e.g. `IPC290750`), found on any INE table via the series' info link.
- **Eurostat:** dataset code plus `params` that fix every dimension except time.
- **ECB:** `FLOW/SERIES_KEY`, as shown on data.ecb.europa.eu.

## Tests

```bash
.venv/Scripts/python -m pytest            # offline tests
.venv/Scripts/python -m pytest -m live    # also call the real APIs
```
