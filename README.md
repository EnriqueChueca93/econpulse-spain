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

## The site online

**https://enriquechueca93.github.io/econpulse-spain/** (repository:
[EnriqueChueca93/econpulse-spain](https://github.com/EnriqueChueca93/econpulse-spain)).

A GitHub Actions workflow ([.github/workflows/update.yml](.github/workflows/update.yml)) runs once a day at
17:30 UTC (18:30 Madrid in winter, 19:30 in summer): it runs the offline tests, fetches the data, rebuilds the
site, commits the updated `data/` back to the repository as "Data update …" and publishes `site/` to GitHub
Pages. Pushing code changes rebuilds and republishes from the saved data. To update by hand, open the
repository's **Actions** tab, pick "Update and deploy" and click **Run workflow**.

Because the workflow commits data every day, run `git pull` before working locally. If a local update changed
`data/` and you only want the code, `git checkout -- data` discards the local data before pulling.

## The site

- **Home** (`site/index.html`): 16 key-indicator tiles, EconPulse readings (activity and inflation against their
  history, the GDP nowcast, the ECB rate against a Taylor rule), "The economy in four questions" and three charts.
- **GDP, Labour market, Wages, Inflation**: econvitals-style tables (1-, 3-, 6- and 12-month changes; latest,
  a month ago, a year ago; contributions to growth) and 25 charts, each with a data table and PNG download.
- **Financial, ECB**: a markets table (1-day, 1-week, YTD, 1-year moves), the Spanish yield curve against the
  AAA euro-area curve, the prima de riesgo, Euribor with a mortgage check, ECB rates and decisions, the next
  ECB meeting and a market-implied rate path.
- **Fiscal, Activity, Housing, International, Regions**: the public finances, activity and tourism, the housing
  market and household debt, Spain against its peers, and the 17 autonomous communities.
- **Tools**: Economy vs pre-COVID trend, an interactive Taylor rule and an interest rate decomposer; change a
  setting and the numbers and charts recompute in the browser.
- **Analysis**: EconPulse's own calculations, each explained on the page: activity and inflation composites,
  a GDP nowcast with its track record, the 10-year yield split into Bund and prima de riesgo, and Taylor rules
  for the euro area and Spain.
- **Calendar** (`site/calendar.html`): releases in the past week and the next two months; every page has a
  "Coming up" bar.
- **Data** (`site/data.html`): a freshness summary, then every series, its source and whether it is up to date.
- **About** (`site/about.html`): sources, how the numbers are made, and limits.

Pages are plain HTML and work offline: Plotly is copied from the Python package, with no CDN. Light/dark
follows the system setting, and the moon button switches it.

## Commands

| Command | What it does |
|---|---|
| `python -m econpulse fetch` | Download every indicator into `data/`, refresh INE's release calendar, log what changed since the last fetch, and print the latest values |
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
                      segsocial (Seguridad Social), ree (Red Eléctrica), oecd, bis, bls,
                      dbnomics, eia, worldbank, bundesbank, fred (local use only), derived
  transforms.py       y/y, m/m, q/q, 3-month annualised, changes
  store.py            data/series/<id>.csv + data/catalog.json
  fetch.py            fetches everything; one failing source never stops the rest
  seasonal.py         EconPulse seasonal adjustment (STL), used by the sa_* transforms and tables
  snapshot.py         latest values, changes and display strings
  questions.py        "The economy in four questions" on the home page
  charts.py           chart specifications (data and wording; colours come from the CSS theme)
  tables.py           econvitals-style section tables (horizons, levels, market moves, contributions,
                      year to date) and panels (one row per country or region)
  pages.py            what each section page shows: blocks of tables and charts
  policy.py           ECB meeting calendar, rate decisions, the mortgage check
  analytics.py        composites, GDP nowcast, 10-year decomposition, Taylor rules
  tools.py            data for the interactive tools (the browser does the arithmetic, static/tools.js)
  schedule.py         release calendar: INE's iCal, the Social Security rule, ECB decisions
  changes.py          "what changed": notes on new releases, revisions and big market moves
  build.py            renders every page into site/ (chart data goes in site/data/*.js)
templates/            Jinja2 pages: base layout, home, section pages, data page
static/               style.css (light/dark tokens), app.js (theme toggle, Plotly charts)
data/                 fetched history, the release calendar (calendar.json) and the log of
                      what changed (releases.json), all tracked in git
site/                 build output, open site/index.html (not tracked)
tests/                pytest suite
```

## Adding an indicator

Add an entry to `econpulse/indicators.yaml` (the header comment explains each field), then run
`python -m econpulse fetch --only <id>`. No code changes are needed for series from a supported source.
For the same measure across countries or regions, write one entry with `for_each` over a list
(see `countries` and `regions` at the top of the file).
To show it in a section table or chart, add a `Row` or a chart series to that page in `econpulse/pages.py`.

- **INE:** use the *series* code (e.g. `IPC290750`), found on any INE table via the series' info link.
- **Eurostat:** dataset code plus `params` that fix every dimension except time.
- **ECB:** `FLOW/SERIES_KEY`, as shown on data.ecb.europa.eu.
- **Banco de España:** the series code from the first row of any table's CSV download (e.g. `DPUG0B1F0ZP`).
- **OECD:** `dataflow/series key` as in the OECD Data Explorer; empty key positions are wildcards that must match one series.
- **BIS:** `dataflow/series key`, e.g. `WS_CBPOL/D.GB` (Bank of England rate).
- **World Bank:** the column header in the monthly prices sheet, e.g. `Gold`.
- **FRED:** the series id (e.g. `DCOILBRENTEU`). FRED does not answer GitHub's servers, so the online site avoids it.
- **Derived:** `subtract`, `add` or `divide` two indicators defined earlier in the file, `deflate` one by a
  price index, or `average` a daily series over complete months.

## Tests

```bash
.venv/Scripts/python -m pytest            # offline tests
.venv/Scripts/python -m pytest -m live    # also call the real APIs
```
