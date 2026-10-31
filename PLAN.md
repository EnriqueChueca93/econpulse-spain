# EconPulse Spain — Build Plan

A running read on the health of the Spanish economy, modelled on [econvitals.org](https://econvitals.org/).
Plan written 30 Oct 2026. Work proceeds in small batches (section 5); tick them off as they land.

---

## 1. What we're replicating, and what changes for Spain

econvitals.org today has:

- **Home page:** 12 key-indicator tiles · "The Economy in Four Questions" · an activity/inflation composite (z-scores vs. history and vs. forecasts) · a summary block per section
- **Section pages:** GDP, Labor, Inflation, Financial (incl. Fed), Fiscal, Other, International
- **Extras:** Tools (GDP trackers, Fedspeak, Taylor rule, rate decomposer…), AI-written Briefings, release Calendar, email signup

| econvitals feature | EconPulse Spain |
|---|---|
| Key indicators strip | **Keep**, with Spanish equivalents (section 4) |
| Four questions | **Keep**, reworded for Spain |
| Composite vs. its own history (z-scores) | **Keep** (Batch 7) |
| Composite vs. forecasts (surprise index) | **Stretch goal**: needs consensus forecasts for each release, which aren't freely available for Spain |
| Fed section, CME FedWatch | **Becomes the ECB section.** Spain has no monetary policy of its own. The market-implied rate path is approximated, because no free €STR OIS feed exists |
| GDP nowcasts (GDPNow, Goldman, Kalshi) | **Replaced** by our own bridge-equation nowcast with a published track record (Batch 7). AIReF, Banco de España and FUNCAS publish as web pages and PDFs, not data feeds, so their panel is left out for now |
| Sell-side commentary | **Drop** (paid and copyrighted) |
| ISM / PMI | **Replace** with the European Commission sentiment surveys, which are free. HCOB PMI is proprietary |
| Email briefings, AI blogs | **After launch** (Batch 9+) |
| — | **New, Spain-only:** prima de riesgo, Euribor (most Spanish mortgages are variable-rate), Social Security registrations (*afiliación*), tourism, electricity price, regional (CCAA) view |

---

## 2. Architecture

One Python codebase. Its output is a plain static website that opens by double-click now and can be uploaded unchanged later.

```
9-EconPulse_Spain/
├── econpulse/                     Python package
│   ├── sources/                   one client per provider: ine.py, eurostat.py, ecb.py, bde.py,
│   │                              markets.py, segsocial.py, ree.py …
│   ├── indicators.yaml            every indicator: id, source, code, unit, freq, transform, section
│   ├── transforms.py              y/y, m/m, q/q, 3-month annualised, moving averages, seasonal adj.
│   ├── store.py                   history → data/series/*.csv, plus metadata and last-updated
│   ├── analytics/                 composites, decompositions, nowcast (later batches)
│   ├── charts.py                  Plotly figure specs, written in Python
│   ├── build.py                   Jinja2 templates + data → site/
│   └── __main__.py                CLI: python -m econpulse fetch | build | update
├── templates/                     HTML templates (base, home, one per section)
├── static/                        CSS, vendored plotly.min.js (no internet needed to view)
├── data/                          fetched history (small CSVs, tracked in git)
├── site/                          BUILD OUTPUT: open site/index.html
├── tests/
├── update.bat                     double-click: fetch, build, open the site
└── .github/workflows/             (Batch 9) scheduled update and deploy
```

**Data flow:** sources → store (CSV) → transforms and analytics → snapshot → build → `site/`

### Key decisions

- **Static site, not a server app.** The same `site/` folder works from your disk today and on GitHub Pages, Cloudflare Pages or Netlify later, all free. No Streamlit or Dash server to keep running. The site *is* the dashboard.
- **Data shipped as `.js`, not `.json`.** Browsers block `fetch()` on `file://` pages, so each page loads `data/*.js` (`window.EP = {...}`) with a `<script>` tag. That works offline and online. `.json` copies are written too, for a possible public API later.
- **Charts written in Python with Plotly**, drawn by a vendored `plotly.min.js`. You stay in Python, and you get a PNG download button like econvitals has.
- **Python only.** Python 3.14 and git are installed. Node isn't, and the site doesn't need it.
  Dependencies: `requests pandas pyyaml jinja2 plotly statsmodels openpyxl pytest`.
- **Registry-driven.** A new indicator is one YAML entry, not new code.
- **Failures stay contained.** A broken feed shows "stale since …" on its tile instead of breaking the build.
- **Every number shows its "as of" date and links to its source.**

---

## 3. Data sources

Status after Batch 6 (31 Oct 2026): 242 indicators. All sources are official or public and are accessed with an honest `EconPulseSpain` User-Agent:

| Provider | Access | Status | Covers |
|---|---|---|---|
| **INE** | JSON API `servicios.ine.es/wstempus` | ✅ in use (125 indicators) | GDP (CNTR): spending and output components, contributions to growth, jobs, productivity, unit labour costs; CPI with core and special groups, rents; producer prices (IPRI); EPA rates; industrial production, retail, house prices, labour costs (ETCL), tourism (FRONTUR, EGATUR), home sales, mortgages (HPT), house prices new and second-hand; by region: unemployment, house prices, CPI, GDP per head |
| **Eurostat** | JSON-stat API | ✅ in use (45) | GDP growth, HICP, core and unemployment for the euro area and peers (DE, FR, IT, PT, NL); annual deficit, debt, interest, revenue and spending; monthly and long-term unemployment, HICP (rates and index, Spain and euro area), labour cost index, EC sentiment surveys and price expectations, government debt and balance, current account |
| **ECB Data Portal** | SDMX REST, CSV | ✅ in use (31) | policy rates, €STR, peers' 10-year yields, household debt (financial accounts), housing-loan growth, new mortgage lending, euro reference rates (USD, GBP, CHF, JPY), AAA euro-area yield curve (spot and forward rates), mortgage rates (MIR), convergence yields |
| **Banco de España** | REST API `app.bde.es/bierest` | ✅ in use (18) | building permits; daily Spanish yield curve (12-month bill, 3, 5, 10, 15 and 30 years), German 10y, prima de riesgo, Euribor, IBEX 35; registered unemployment, pay rises agreed in collective agreements, car sales, hotel nights, balance of payments |
| **Seguridad Social** | spreadsheet linked from its statistics page | ✅ in use (1) | average registrations (*afiliados*), total system, since 2001 |
| **Red Eléctrica (REE)** | REData API `apidatos.ree.es` | ✅ in use (2) | day-ahead electricity price (daily average of 15-minute prices), daily demand |
| **FRED** | public CSV, no key | ✅ in use (8) | Brent spot (US EIA), European gas (IMF); US GDP, CPI, core CPI, unemployment, 10-year yield, Fed funds target |
| **EconPulse calculations** | from the series above | ✅ in use (12) | Brent in euros, 10-year spreads over Germany, GDP deflator, real wages, real house prices, average mortgage, primary balance, monthly electricity demand |
| ~~Yahoo Finance~~ | unofficial API | ❌ dropped | IBEX 35 now comes from Banco de España and Brent from FRED |
| **AIReF · FUNCAS · BdE projections** | web pages / PDF | ⏸ not automated | GDP nowcast, forecaster consensus, official projections: no stable data feed (AIReF's MIPred page has moved); a hand-updated file is an option |

**Gotchas found already:**
- INE's CPI table 50902 stops at Dec 2025, because CPI moved to new tables in 2026. The registry pins INE *series* codes rather than table IDs, and a freshness check flags any series that stops updating.
- Eurostat's HICP dataset `prc_hicp_manr` also stops at Dec 2025. The replacement is `prc_hicp_minr` (ECOICOP ver. 2), and its item dimension is now `coicop18`.
- Eurostat has no Spanish **services or retail confidence** after Sep 2024 (France's continues). The freshness check caught it, and both were dropped.
- Banco de España's own *afiliados* series (`D_1JCCTETT`) stops at Dec 2025, probably because of the switch to the CNAE-2025 industry classification. Registrations come straight from the Seguridad Social instead. Its PX-Web server has no API, so we read the "19_Serie afiliación media" spreadsheet.
- Banco de España serves at most 36 months of a daily series per request, so the first fetch walks back year by year to 2000 (about 3 minutes). After that, `fetch` downloads only recent observations and merges them into the stored history (about 10 seconds).
- REE serves prices only at hourly resolution, in windows of about a week. They're fetched in 7-day chunks and averaged to a daily price.
- The machine clock may not be on Spanish time. "Today" for freshness checks and request windows is Madrid time.
- STL's default seasonal smoothing (a local line) extrapolates recent swings at the end of a series: the 2026 energy surge was being read as seasonality, which put CPI and HICP monthly rates far apart (−1.7% vs +8.6% annualised for the same month). The seasonal factors now use a local constant (`seasonal_deg=0`), and CPI and HICP agree.
- The labour cost survey (ETCL) is unadjusted, and bonuses move between quarters, so seasonally adjusted quarterly rates flip sign depending on the method. Wages are compared with a year earlier; Eurostat's labour cost index is the adjusted measure.
- Banco de España table CSVs (`www.bde.es/webbe/es/estadisticas/compartido/datos/csv/be24NN.csv`) are a good way to find series codes: the level of registered unemployment (`D_1JA0D000`) and agreed pay rises came from tables 24.15 and 24.22.
- Banco de España has no daily Spanish 2-year yield or 3- and 6-month bills in its API; the curve uses the 12-month bill and the 3, 5, 10, 15 and 30-year bonds.
- No free feed of €STR swap rates exists, so "what markets expect" uses the ECB's AAA euro-area forward rates. They include a term premium; the page says so.
- Euro high-yield credit spreads are on FRED, but they are ICE's proprietary data and FRED only keeps three years, so they are left out. Euro Stoxx 50 and gold still have no clean free source.
- The ECB meeting calendar is a list in `econpulse/policy.py`, taken from the ECB's published schedule and running to December 2028. After the last date, the page links to the ECB calendar.
- The tourism series picked in Batch 2 (`FREG287`) was all visitors, including same-day visitors (144 million in 2025), not tourists. It now uses `FREG286`, tourists only (96.8 million in 2025); the home tile changed from 18.5 to 12.3 million for August.
- Eurostat's euro area is `EA21` from 2026 for unemployment (Bulgaria joined); GDP growth still uses `EA20`.
- Building permits reach Banco de España several months late, so that series is allowed 240 days before it counts as "not updating". Annual series are dated 1 January and published 4–12 months after the year ends, so their default allowance is now 850 days.
- Regional and country series are written once in `indicators.yaml` with `for_each` over a list (17 regions, 5 peer countries), not 100 near-identical entries.

---

## 4. Indicator map (US → Spain)

### 4.1 Key indicators strip

| econvitals | EconPulse Spain | Source | Freq |
|---|---|---|---|
| Real GDP q/q ann. | Real GDP q/q and y/y (Spanish convention: not annualised) | INE CNTR | Q |
| Payrolls | *Afiliados* to Social Security, monthly change (SA) | Min. Inclusión | M, early in month |
| Unemployment | Unemployment rate: EPA (official, quarterly) and Eurostat (monthly SA) | INE / Eurostat | Q / M |
| PCE y/y | CPI (IPC) y/y | INE | M, plus flash |
| Core PCE y/y | Core CPI (*subyacente*: excludes unprocessed food and energy) y/y | INE | M |
| Core CPI y/y | HICP (IPCA) y/y, the measure the ECB targets | INE / Eurostat | M |
| Fed funds target | ECB deposit facility rate | ECB | at each change |
| 10-year | Spain 10-year bond yield | BdE | D |
| 2Y–10Y spread | **Prima de riesgo** (Spain 10y − Germany 10y, bp) | BdE + Bundesbank | D |
| S&P 500 | IBEX 35 | Yahoo | D |
| Brent | Brent in €, plus the electricity pool price | Yahoo / REE | D |
| Broad dollar | EUR/USD | ECB | D |

### 4.2 The Economy in Four Questions, Spanish version

1. **Is inflation coming back to 2%?** HICP and core, y/y and 3-month annualised. The 3-month figure uses seasonal adjustment we compute ourselves, because INE doesn't publish SA CPI.
2. **Is the labour market cooling?** Registrations last month and their 3-month average, plus the unemployment rate against a year ago.
3. **Is growth holding up?** Domestic final demand (private consumption plus investment), q/q and y/y.
4. **Why are Spain's borrowing costs moving?** The change in the 10-year yield since 31 Dec, split into the German Bund (euro-wide rates) and the prima de riesgo (Spain-specific risk). This replaces econvitals' breakeven/real-rate split, which has no Spanish equivalent.

### 4.3 Section pages

- **GDP & productivity:** CNTR expenditure components (household and government consumption; investment split into construction and equipment; exports split into goods and services; imports), GVA by sector, hours and FTE jobs, productivity, unit labour costs, GDP deflator. Nowcast panel: AIReF MIPred, BdE, FUNCAS.
- **Labour:** registrations (total, SA, by sector, by regime), *paro registrado*, EPA (unemployment, activity and employment rates, youth and long-term unemployment, temporary-contract rate), share of permanent contracts, vacancies, regional breakdown.
- **Wages:** ETCL labour cost per worker and per hour, wage increases agreed in collective agreements (*convenios*), real wages, minimum wage (SMI) history, ECB wage tracker (euro area).
- **Inflation:** IPC headline, core and components (food, energy, services, non-energy industrial goods, rents), HICP, flash estimate, producer prices (IPRI), electricity and fuel prices, Spain against the euro area, inflation expectations (EC consumer survey, ECB SPF, ECB Consumer Expectations Survey).
- **Financial:** Spanish yield curve (latest, one month ago, end of last year), 10y and prima de riesgo, Bund, €STR, **12-month Euribor**, new mortgage rates, IBEX 35, Euro Stoxx 50, EUR/USD and other crosses, Brent, TTF, gold, euro credit spreads. Markets table with 1-day, 1-week and YTD columns, as on econvitals.
- **ECB:** deposit rate, MRO and €STR history, next meeting date, expected path (ECB Survey of Monetary Analysts plus a Euribor-curve proxy), and a Taylor rule for the euro area *and* for Spain, which shows the "one size fits all" gap.
- **Fiscal:** general government deficit and debt (IGAE, BdE, Eurostat), AIReF assessments, Treasury issuance, interest bill, NGEU funds.
- **Other activity:** retail sales, industrial production, EC sentiment (ESI, industry, services, consumers), car registrations, electricity demand, **tourism** (FRONTUR arrivals, EGATUR spending, hotel nights), household saving rate, current account.
- **Housing:** house prices (INE IPV), home sales, new mortgages, building permits, rents, household debt and debt service.
- **International:** Spain against the euro area, Germany, France, Italy, Portugal, the Netherlands, the UK and the US: GDP, inflation, core, unemployment, policy rate, 10y.
- **Regions (new):** a table or map of the 17 autonomous communities: unemployment, registrations, house prices, GDP per capita.

---

## 5. Batches

Each batch is sized for one working session, ends with something you can open or run, and is committed to git.

### Batch 0 — Scaffold *(small)* ✅ done 30 Oct 2026
- `git init`, folder structure, virtual environment, `requirements.txt`, `.gitignore`, README
- `update.bat` and the CLI skeleton (`python -m econpulse update`)
- A placeholder `site/index.html` with one tile of dummy data, loaded through a `data/*.js` file
- **Done when:** double-clicking `site/index.html` shows the tile, offline.

### Batch 1 — Core data layer (INE, Eurostat, ECB) ✅ done 30 Oct 2026
*Result: 34 indicators (16 INE, 8 Eurostat, 9 ECB, 1 derived prima de riesgo) fetched in about 10 seconds; 42 offline tests plus 3 live API tests. The home page placeholder shows 10 live tiles and a table of every indicator.*
- A shared `Series` format and the store (CSV plus metadata)
- Clients for the three APIs already verified
- `indicators.yaml` with about 20 indicators: GDP, CPI, core, HICP, EPA, monthly unemployment, ECB rates, EUR/USD, ESI…
- Transforms: y/y, m/m, q/q, 3-month annualised, rolling averages
- Tests on the transforms, plus one smoke test per client
- **Done when:** `python -m econpulse fetch` fills `data/` and prints a table of latest values.

### Batch 2 — Remaining sources and robustness ✅ done 30 Oct 2026
*Result: 61 indicators from 7 sources, plus 2 derived (Brent in €, monthly ES–DE spread). The first fetch backfills history in about 3 minutes; later updates take about 10 seconds. There is a `status` freshness report, and 62 offline plus 8 live tests. The home page has 13 tiles in econvitals order. Deferred: household debt and the level of registered unemployment (both landed later, in Batches 6 and 4), and Euro Stoxx 50 and gold (no clean free source yet).*
- Banco de España (yields, Euribor, mortgage rates, household debt, balance of payments), Bundesbank 10y, Yahoo markets
- Seguridad Social and SEPE downloads (Excel parsing), REE or OMIE electricity price
- Retries, caching, per-source failure isolation, a "stale data" flag, a freshness report
- **Done when:** about 60 indicators update in one command, and a broken source doesn't stop the rest.

### Batch 3 — Site v1: home page ✅ done 30 Oct 2026
*Result: 12 server-rendered pages (home, 10 section pages, data page) with a shared header, navigation, light/dark theme with a toggle, and a mobile layout. The home page has 16 tiles in four themed rows (activity, prices, rates, markets), the Four Questions and three Plotly charts (HICP vs core; Spain vs Germany 10y; SA registrations), each with a hover readout, PNG download and data table. The chart palette was checked with the dataviz validator, and all pairs pass in both modes. Seasonal adjustment (STL) moved forward from Batch 4, because the Four Questions need it. 69 offline tests.*
- Jinja2 templates, CSS in an econvitals-like clean style (light and dark), navigation
- Key indicators strip and the Four Questions block, with live data
- Vendored Plotly and a chart helper with PNG download
- **Done when:** `update.bat` fetches, builds and opens a working home page.

### Batch 4 — Sections I: GDP, Labour, Wages, Inflation ✅ done 31 Oct 2026
*Result: the four pages are filled, with 9 tables and 25 charts. Each page is a set of blocks (sub-heading, intro, tables, charts), defined in `econpulse/pages.py`; the tables are computed in `econpulse/tables.py`. 41 new indicators (102 in all): GDP components, contributions to growth, output by sector, the GDP deflator, jobs, productivity and unit labour costs; EPA rates, long-term unemployment, the level of registered unemployment; labour costs per worker and per hour, the labour cost index, agreed pay rises, real wages; CPI special groups, rents, producer prices, the HICP index, euro-area core inflation, consumers' price expectations. GDP: q/q and y/y with INE's contributions (not annualised, Spanish practice). Labour: average monthly change (1, 3, 12 months), levels, EPA and Eurostat rates. Wages: annual growth now, a quarter ago and a year ago. Inflation: 1-, 3- and 6-month annualised rates plus 12-month, with the CPI flash shown as a note. Charts support stacked bars, a line over bars, end labels pushed apart, and dropping end labels on phones. The registrations tile now headlines the seasonally adjusted monthly change, as econvitals does for payrolls, with the published y/y change below it. 85 offline and 8 live tests.*
- Charts plus the econvitals-style tables (1-month, 3-month and 12-month columns; latest, one month ago, one year ago)
- Seasonal adjustment exists since Batch 3 (`sa_*` transforms). Use it in the tables, and decide whether the registrations tile switches from the official y/y change to the SA monthly change, as econvitals does for payrolls
- Fill the section pages using the chart helper from Batch 3 (`charts.py` specs + `app.js`)

### Batch 5 — Sections II: Financial and ECB ✅ done 31 Oct 2026
*Result: both pages are filled, with 6 tables, 14 charts and two computed extras. Financial: a markets table (latest, 1-day, 1-week, YTD, 1-year; rates in bp, prices in %) covering yields, the prima de riesgo, Euribor, the IBEX 35, four euro exchange rates and energy; the Spanish yield curve (latest, a month earlier, end of last year) and its spread over the AAA euro-area curve at each maturity; the prima de riesgo since 2008; and Euribor and mortgage rates. A mortgage check shows what a typical variable-rate mortgage (€150,000, 25 years, Euribor + 0.9 pp) costs at this month's Euribor against a year earlier. ECB: a key-facts strip (deposit rate, last change, next decision with a countdown, €STR), policy rates, recent decisions read from the deposit rate, rates against euro-area inflation, the deposit rate since 1999, and a market-implied path from AAA forward rates. 17 new indicators (119 in all). New building blocks: market-move and spread columns, curve charts (category axis), step lines, a facts strip and callouts. 94 offline and 8 live tests.*
- Yield curve, prima de riesgo, Euribor, markets table (1-day, 1-week, YTD), ECB rate history and expected path

### Batch 6 — Sections III: Other, Housing, Fiscal, International, Regions ✅ done 31 Oct 2026
*Result: every section page is now filled, and a new Regions page joins the navigation. Activity: industry, retail, car sales and monthly electricity demand; EC surveys; tourism with year-to-date totals; the current account. Housing: house prices (new, second-hand, after inflation since the 2007 peak), sales, mortgages, the average mortgage, new lending, building permits, household debt and housing-loan growth. Fiscal: the annual balance, primary balance, interest, revenue, spending and debt, plus the latest four quarters. International: a peer table (Spain, euro area, Germany, France, Italy, Portugal, the Netherlands, the US) with GDP growth, inflation, core, unemployment, 10-year yields and policy rates; rankings; spreads over Germany since 2008. Regions: a table of the 17 autonomous communities (unemployment and its change, house prices, inflation, GDP per head) and four ranking charts. 123 new indicators (242 in all). New building blocks: `for_each` in the registry, panel tables, ranking charts, year-to-date columns, rolling 12-month totals and 4-quarter averages, `average` and `add` calculations, rebased and rescaled chart series, and chart sources that credit a calculation's inputs. Fixed on the way: the tourism series counted all visitors. 105 offline and 8 live tests.*
- Tourism, electricity, sentiment, housing, fiscal and the comparison table across countries and regions

### Batch 7 — EconPulse originals (analytics) ✅ done 31 Oct 2026
*Result: a new Analysis page and an "EconPulse readings" strip on the home page, all computed in `econpulse/analytics.py`. Composites: 10 activity and 7 inflation indicators scored against their own record since 2013 (robust z-scores using the median and MAD, Covid years left out, clipped at ±3), averaged with weights that fall by a quarter for each month a reading ages. Activity is +0.2 (close to normal) and inflation +1.7 (hotter than normal). Nowcast: a bridge equation for this quarter's GDP from SA registrations, industrial production and last quarter's growth, with missing months projected by AR(1). Q4 2026 is +0.7% q/q. Its record since 2023 is a 0.23 pp typical error, against 0.27 for repeating the previous quarter and 0.26 for the long-run average; inputs that made the record worse (retail sales, sentiment) were dropped, and the page warns that this flatters it. Decomposition: changes in Spain's 10-year yield split into Bund and prima de riesgo, and the yield since 2010 in two stacked parts. Taylor rules: 0.5% neutral real rate + HICP + 0.5 × inflation gap − unemployment gap (trend by HP filter), for the euro area (4.8%) and Spain (6.5%) against the ECB's 2.50%. Not done: the AIReF, Banco de España and FUNCAS forecast panel, which has no data feed. 113 offline and 8 live tests.*
- Activity and inflation composites: z-scores against history since 2013, weighted towards the newest prints
- 10-year decomposition (Bund plus prima de riesgo)
- Nowcast panel (AIReF, BdE, FUNCAS) plus a simple bridge-equation nowcast of our own
- Spain and euro-area Taylor rules

### Batch 8 — Calendar, "what changed", About
- Release calendar (INE calendar, Social Security, ECB meetings) and the "Today / Coming up" bar
- Automatic "what changed since the last update" notes, rule-based
- About and methodology page, data-freshness page

### Batch 9 — Go online
- GitHub repository, GitHub Actions on a schedule (e.g. 07:30 and 18:30 Madrid time) that runs `update` and deploys `site/` to GitHub Pages; custom domain optional
- Optional later: email digest, AI-written daily briefing, more tools (rate decomposer, Economy vs. Trend)

---

## 6. Open decisions

1. ~~**Language**~~ **Decided 30 Oct 2026:** English UI, with Spanish official names alongside (e.g. "Social Security registrations · *Afiliados medios*").
2. **Name and domain:** "EconPulse Spain" for now. Needed by Batch 9.
3. **Hosting account:** the GitHub account to use. Needed by Batch 9.
4. **Update frequency once online:** daily or twice daily (markets want more often than macro data).
5. **History window for z-scores:** econvitals uses 2013 onwards; the same works for Spain and avoids the 2008–12 crisis dominating the scale.

---

## 7. Conventions

- Follow Spanish statistical conventions: GDP q/q is not annualised, y/y is the headline. Annualised rates appear only where they help comparison with the US.
- Units and dates appear with every number. Sources appear under every chart.
- Use only official and free data. Never reproduce copyrighted commentary.
- Before relying on a series, check that it is still updating. INE sometimes moves series to new tables (see section 3).
