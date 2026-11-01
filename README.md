# EconPulse Spain

A running read on the health of the Spanish economy, modelled on [econvitals.org](https://econvitals.org/).
Python fetches official data (INE, Eurostat, ECB…) and builds a static website that opens straight from disk
and can later be hosted anywhere. See [PLAN.md](PLAN.md) for the roadmap.

## Quick start (Windows)

Double-click **`EconPulse.exe`** in the project folder. It builds the site from the data already saved
(a few seconds), serves it on this computer only and opens it in your browser at `http://localhost:8765/`
(or the next free port); close its window to stop it. Run `EconPulse.exe --update` to fetch the latest data
first (a few minutes). It runs the project's own Python (`.venv`), so it always shows the current code and
data; it is a 6 KB launcher for `python -m econpulse serve`, built from `scripts/launcher/EconPulse.cs` with
the C# compiler that comes with Windows (`.venv\Scripts\python.exe scripts\build_launcher.py`; the .exe is
not kept in git). The data in a local copy are as fresh as the last `git pull` or `--update`.

**`update.bat`** also sets up the Python environment on a first run, then fetches the latest data, rebuilds
the site and opens `site/index.html` from disk.

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
  history and against a simple forecast, the GDP nowcast, the ECB rate against a Taylor rule), "The economy in four
  questions" and three charts.
- **GDP, Labour market, Wages, Inflation**: econvitals-style tables (1-, 3-, 6- and 12-month changes; latest,
  a month ago, a year ago; contributions to growth) and 25 charts, each with a data table and PNG download.
  The Inflation page also measures underlying inflation across the ~180 detailed HICP items: weighted median,
  10% and 30% trimmed means, how widespread price rises are, and the items rising fastest and slowest.
- **Financial, ECB**: a markets table (1-day, 1-week, YTD, 1-year moves), the Spanish yield curve against the
  AAA euro-area curve, the prima de riesgo, Euribor with a mortgage check, ECB rates and decisions, the next
  ECB meeting and a market-implied rate path.
- **Fiscal, Activity, Housing, International, Regions**: the public finances, activity and tourism, the housing
  market and household debt, Spain against its peers, and the 17 autonomous communities.
- **Tools**: Economy vs pre-COVID trend, an interactive Taylor rule and an interest rate decomposer; change a
  setting and the numbers and charts recompute in the browser. **Fiscal Explorer** (`site/fiscal-explorer.html`):
  Spain's debt and deficits since 1970 and to 2070, starting from the European Commission's baseline (reproduced
  exactly to 2036, extended by EconPulse on the Commission's long-term assumptions), with levers for the budget,
  ageing costs, growth, inflation and interest rates, a goal-solver and shareable scenario links; after
  Econvitals' Fiscal Explorer. **ECB-speak** (`site/ecb-speak.html`): how hawkish or dovish the ECB's Governing
  Council sounds, from every member's speech since September 2022 (ECB and BIS full texts), scored with
  EconPulse's published word lists rather than an AI; after Econvitals' Fedspeak Tracker. **Global central bank stance**
  (`site/stance.html`): Econvitals' Global Central Bank Stance Matrix for twelve central banks, shown natively
  and credited (Econvitals places its own work in the public domain, CC0 1.0).
- **Sector tables** (`site/sector-tables.html`): every IMF-style table on one page, with a switch between amounts
  in euros and percent of GDP, and twelve charts from the tables' data.
- **IMF-style sector tables**: the tables of the IMF's 2026 Article IV report for Spain, rebuilt from public
  data (actual years from INE, Eurostat and the ECB, projections from the IMF's World Economic Outlook; "…" where
  the WEO does not publish a line). Each is on its section page (Table 1, main economic indicators, on the GDP
  page; Tables 2a and 2b, government operations, and the debt sustainability tables on the Fiscal page, the
  stress tests from the European Commission's Debt Sustainability Monitor; Tables 4 and 5, the balance of payments
  and external debt, on the Activity page; Table 3, financial soundness, on the Financial page, from the IMF's own
  FSI database and the Banco de España; Table 6, monetary and credit indicators, on the ECB page) and all are in
  one Excel workbook,
  `site/data/econpulse-spain-sector-tables.xlsx`, with history from 2015.
- **Analysis**: EconPulse's own calculations, each explained on the page: activity and inflation composites,
  data surprises (the latest figures against a simple statistical forecast), a GDP nowcast with its track record,
  what forecasters expect for this year and next, the 10-year yield split into Bund and prima de riesgo, and
  Taylor rules for the euro area and Spain.
- **Calendar** (`site/calendar.html`): releases in the past week and the next two months; every page has a
  "Coming up" bar.
- **Data** (`site/data.html`): a freshness summary, a link to the sector tables workbook, then every series,
  its source and whether it is up to date.
- **About** (`site/about.html`): sources, how the numbers are made, and limits.

Each tab in the navigation has a dropdown of its page's sections. Pages are plain HTML and work offline: Plotly is copied from the Python package, with no CDN. Light/dark
follows the system setting, and the moon button switches it. Every chart has a "Copy link" button that copies
the page address with the chart's anchor (`#fig-<chart id>`), and `site/feed.xml` is an RSS feed of what
each update changed (linked in every page's footer).

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
                      dbnomics, eia, worldbank, bundesbank, imf, bdeproj (Banco de España
                      projections), funcas, fred (local use only), derived; webtables.py reads
                      the HTML tables of the sources that publish web pages
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
  surprises.py        data surprises: each figure against a one-step AR(1) forecast
  underlying.py       underlying inflation on the Inflation page (the measures come from sources/hicpdist.py)
  forecasts.py        the forecasters' table, read automatically, with the AI check (data/forecast_checks.json)
  forecasts.yaml      optional overrides by hand, for an edition the automatic sources have not picked up
  tools.py            data for the interactive tools (the browser does the arithmetic, static/tools.js)
  schedule.py         release calendar: INE's iCal, the Social Security rule, ECB decisions
  changes.py          "what changed": notes on new releases, revisions and big market moves
  feed.py             the RSS feed of those notes (site/feed.xml; absolute links use config.SITE_URL)
  stance.py           the central bank stance page, from Econvitals' public data (saved to data/stance.json)
  fiscal.py           the Fiscal Explorer's baseline and data (the levers run in static/fiscal.js)
  ecbspeak.py         ECB-speak: collects the Governing Council's speeches (data/ecbspeak.json) and analyses them
  speechscore.py      the hawkish/dovish word lists and the score
  fiscal_baseline.json  the Commission's Spain baseline, extracted by scripts/extract_fiscal_baseline.py
  sectortables.py     IMF-style sector tables: their lines, the section-page tables and the Excel workbook
  serve.py            serves site/ on this computer for `python -m econpulse serve` (what EconPulse.exe runs)
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
- **DBnomics:** `provider/dataset/series` as on db.nomics.world, e.g. `AMECO/ZUTN/ESP.1.0.0.0.ZUTN`.
- **BIS:** `dataflow/series key`, e.g. `WS_CBPOL/D.GB` (Bank of England rate).
- **World Bank:** the column header in the monthly prices sheet, e.g. `Gold`.
- **FRED:** the series id (e.g. `DCOILBRENTEU`). FRED does not answer GitHub's servers, so the online site avoids it.
- **Derived:** `subtract`, `add` or `divide` two indicators defined earlier in the file, `deflate` one by a
  price index, or `average` a daily series over complete months.

## Forecasts and the AI check

Every forecaster is read automatically: the IMF, OECD and European Commission from their data services, the
Banco de España from its latest report's projections table, and the FUNCAS Panel from its web page or PDF,
whose reference table also gives the government's and AIReF's latest forecasts. Figures read this way count
only after an **AI check**: until then their row shows an "awaiting AI check" badge and is left out of the
average, the facts and the chart. A new edition, or any change to the figures, needs a new check.

```bash
.venv/Scripts/python -m econpulse forecasts                      # figures, sources, and which await a check
.venv/Scripts/python -m econpulse confirm bde --against "the report's table of 9 Oct"   # after checking
```

The check means an AI (for example Claude, in a session on this repository) opens each source, compares the
figures with the publisher's own document, and only then runs `confirm`, which records the edition's
fingerprint in `data/forecast_checks.json`; `--note` adds a caveat under the table. Commit that file. The
daily run's `status` step lists forecasts awaiting a check. To show an edition the automatic sources have
not picked up yet, enter it by hand in `econpulse/forecasts.yaml` (the comment at its top explains how).

## Updating the Fiscal Explorer's baseline

The Fiscal Explorer starts from two European Commission workbooks: the Debt Sustainability Monitor (a new edition
each year, around February) and the Ageing Report (every three years; the next is due in 2027). When a new edition
comes out, update the two download links at the top of `scripts/extract_fiscal_baseline.py` and run it:

```bash
.venv/Scripts/python scripts/extract_fiscal_baseline.py
```

It rewrites `econpulse/fiscal_baseline.json`; check that the tests still pass (they confirm that the debt equation
reproduces the Commission's path and that the model's S1 matches the Commission's), then commit the file.

## Tests

```bash
.venv/Scripts/python -m pytest            # offline tests
.venv/Scripts/python -m pytest -m live    # also call the real APIs
```
