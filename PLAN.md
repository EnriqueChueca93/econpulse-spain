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
| GDP nowcasts (GDPNow, Goldman, Kalshi) | **Replace** with AIReF MIPred, Banco de España projections and the FUNCAS Panel; our own simple nowcast comes later |
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

These sources were test-called on 30 Oct 2026:

| Provider | Access | Status | Covers |
|---|---|---|---|
| **INE** | JSON API `servicios.ine.es/wstempus` | ✅ works | GDP (CNTR), CPI, core, HICP, EPA, industrial production, retail, house prices, labour cost (ETCL), vacancies, tourism, mortgages, home sales |
| **Eurostat** | JSON-stat API | ✅ works (Spain unemployment SA 10.2% in Aug → 10.3% in Sep; ESI 105.1) | monthly unemployment, HICP, EC sentiment surveys, government debt and deficit, international comparisons |
| **ECB Data Portal** | SDMX REST, CSV | ✅ works (deposit rate 2.50%) | policy rates, €STR, euro-area yield curve, FX reference rates, bank lending rates (MIR), SPF expectations |
| **Banco de España** | REST API `app.bde.es/bierest` | ✅ online; series codes still need mapping | Spanish yields and curve, Euribor, mortgage rates, household debt, credit, balance of payments, government debt (PDE) |
| **Yahoo Finance** | chart API (unofficial) | ✅ works (IBEX 35: 18,652.9) | IBEX 35, Euro Stoxx 50, Brent, TTF gas, gold, FX. Needs a fallback |
| **REE** | `apidatos.ree.es` | ⚠️ returned an error today; retest, fallback is OMIE daily files | daily electricity pool price, electricity demand |
| **Seguridad Social / SEPE** | Excel/CSV downloads | 🔲 to build (download and parse) | registrations (total, SA, by sector), registered unemployment (*paro registrado*) |
| **AIReF · FUNCAS · BdE projections** | web pages / Excel | 🔲 to build | GDP nowcast, forecaster consensus, official projections |
| **Bundesbank / ECB** | SDMX | 🔲 to build | German 10y yield, for the prima de riesgo |
| **FRED** (free key) | REST | 🔲 optional | ICE BofA euro credit spreads, US comparison series |

**Gotchas found already:**
- INE's CPI table 50902 stops at Dec 2025, because CPI moved to new tables in 2026. The registry pins INE *series* codes rather than table IDs, and a freshness check flags any series that stops updating.
- Eurostat's HICP dataset `prc_hicp_manr` also stops at Dec 2025. The replacement is `prc_hicp_minr` (ECOICOP ver. 2), and its item dimension is now `coicop18`.

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

### Batch 2 — Remaining sources and robustness
- Banco de España (yields, Euribor, mortgage rates, household debt, balance of payments), Bundesbank 10y, Yahoo markets
- Seguridad Social and SEPE downloads (Excel parsing), REE or OMIE electricity price
- Retries, caching, per-source failure isolation, a "stale data" flag, a freshness report
- **Done when:** about 60 indicators update in one command, and a broken source doesn't stop the rest.

### Batch 3 — Site v1: home page
- Jinja2 templates, CSS in an econvitals-like clean style (light and dark), navigation
- Key indicators strip and the Four Questions block, with live data
- Vendored Plotly and a chart helper with PNG download
- **Done when:** `update.bat` fetches, builds and opens a working home page.

### Batch 4 — Sections I: GDP, Labour, Wages, Inflation
- Charts plus the econvitals-style tables (1-month, 3-month and 12-month columns; latest, one month ago, one year ago)
- Seasonal adjustment for CPI 3-month annualised (statsmodels)

### Batch 5 — Sections II: Financial and ECB
- Yield curve, prima de riesgo, Euribor, markets table (1-day, 1-week, YTD), ECB rate history and expected path

### Batch 6 — Sections III: Other, Housing, Fiscal, International, Regions
- Tourism, electricity, sentiment, housing, fiscal and the comparison table across countries and regions

### Batch 7 — EconPulse originals (analytics)
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

1. **Language:** English UI with Spanish official names (default), Spanish only, or bilingual EN/ES. Needed by Batch 3.
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
