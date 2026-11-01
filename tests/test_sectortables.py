"""Batch 19: the IMF-style sector tables and their workbook (no network)."""

import pandas as pd
import pytest
from openpyxl import load_workbook

from econpulse import sectortables as st
from econpulse.build import build_site
from econpulse.registry import load_registry
from econpulse.store import Store
from econpulse.tables import Data

YEARS = pd.date_range("2015-01-01", "2025-01-01", freq="YS")
WEO = pd.date_range("2015-01-01", "2031-01-01", freq="YS")


def annual(values, index=YEARS):
    return pd.Series(values, index=index[:len(values)], dtype=float)


@pytest.fixture
def store(tmp_path):
    store = Store(tmp_path / "data")
    n = len(YEARS)
    store.save_series("gdp_growth_annual", annual([2.0] * n))
    store.save_series("fc_imf_gdp", annual([2.0] * len(WEO), WEO))
    store.save_series("gdp_nominal_annual", annual([1000.0 * 1.04 ** k for k in range(n)]))
    store.save_series("trade_balance_annual", annual([40.0] * n))
    store.save_series("deficit_annual", annual([-3.0] * n))
    store.save_series("interest_annual", annual([2.4] * n))
    store.save_series("interest_received_annual", annual([0.5] * n))
    store.save_series("public_investment_annual", annual([2.9] * n))
    store.save_series("fc_imf_unemployment", annual([10.0] * len(WEO), WEO))
    store.save_series("fc_imf_employment", annual([100 * 1.01 ** k for k in range(len(WEO) - 4)], WEO))
    # Monthly HICP rising 0.25% a month; quarterly EPA employment and unemployment.
    m = pd.date_range("2014-01-01", "2026-09-01", freq="MS")
    store.save_series("hicp_index", pd.Series([100 * 1.0025 ** k for k in range(len(m))], index=m))
    q = pd.date_range("2014-01-01", "2026-07-01", freq="QS")
    store.save_series("employment_epa", pd.Series([20000 + 50 * k for k in range(len(q))], index=q, dtype=float))
    store.save_series("unemployment_epa", pd.Series([12.0] * len(q), index=q))
    catalog = store.load_catalog()
    catalog["fc_imf_gdp"] = {"status": "ok", "published": "2026-10-13"}
    store.save_catalog(catalog)
    return store


def cells(store, label, first=2015, last=2031):
    data = Data(load_registry(), store)
    rows = st.values(st.REAL_SECTOR, data, first, last, 2025)
    return dict(zip(range(first, last + 1), next(r["cells"] for r in rows if not r["heading"] and r["label"] == label)))


def test_years_and_edition(store):
    data = Data(load_registry(), store)
    assert st.years(data) == (2025, 2031)
    assert st.weo_edition(data) == "October 2026"


def test_actual_years_from_statistics_projections_from_the_weo(store):
    gdp = cells(store, "Gross domestic product")
    assert gdp[2025] == 2.0 and gdp[2026] == 2.0
    # The WEO publishes no consumption: projections show as missing ("…" on the page).
    assert cells(store, "Private consumption")[2026] is None
    # Unemployment: the mean of the four quarters, then the WEO.
    u = cells(store, "Unemployment rate (percent of total labor force)")
    assert u[2025] == pytest.approx(12.0) and u[2026] == 10.0


def test_derived_lines_follow_the_imf_definitions(store):
    # Primary balance: balance plus interest paid less interest received (the WEO's definition).
    assert cells(store, "Primary balance 5/")[2025] == pytest.approx(-3.0 + 2.4 - 0.5)
    # Trade balance in % of GDP from euros.
    assert cells(store, "Trade balance (goods and services)")[2015] == pytest.approx(4.0)
    # Average and end-of-period inflation from the monthly index (complete years only).
    avg = cells(store, "Headline inflation (average) 2/")
    eop = cells(store, "Headline inflation (end of period) 2/")
    assert avg[2025] == pytest.approx((1.0025 ** 12 - 1) * 100) and eop[2025] == pytest.approx((1.0025 ** 12 - 1) * 100)
    # Labour force = employment / (1 - unemployment rate): with a constant rate it grows with employment.
    lf, emp = cells(store, "Labor force"), cells(store, "Employment")
    assert lf[2025] == pytest.approx(emp[2025]) and lf[2026] == pytest.approx(1.0)
    # The WEO's employment ends in 2027, so later projection years are missing.
    assert emp[2027] == pytest.approx(1.0) and emp[2028] is None


def test_public_savings_rows(store):
    data = Data(load_registry(), store)
    rows = [r for r in st.values(st.REAL_SECTOR, data, 2025, 2025, 2025) if not r["heading"]]
    publics = [r["cells"][0] for r in rows if r["label"] == "Public"]
    assert publics == [pytest.approx(2.9), pytest.approx(-0.1)]   # investment, then savings


def test_web_table_shape(store):
    t = st.web_table(st.REAL_SECTOR, Data(load_registry(), store))
    assert t["columns"] == [str(y) for y in range(2023, 2032)]
    assert t["column_notes"] == [""] * 3 + ["proj."] * 6
    assert "IMF projections (World Economic Outlook, October 2026) from 2026" in t["caption"]
    gdp = next(r for r in t["rows"] if r["label"] == "Gross domestic product")
    consumption = next(r for r in t["rows"] if r["label"] == "Private consumption")
    assert gdp["cells"][0] == "2.0" and consumption["cells"][-1] == st.NA and consumption["indent"] == 1
    assert st.fmt(-0.04) == "0.0" and st.fmt(-1234.5) == "−1,234.5"


def test_no_table_without_annual_gdp(tmp_path):
    data = Data(load_registry(), Store(tmp_path / "empty"))
    assert st.web_table(st.REAL_SECTOR, data) is None and st.facts(data) == []
    assert st.write_workbook(data, tmp_path / "x.xlsx") is False


def test_every_line_reads_registered_indicators():
    ids = {i.id for i in load_registry()}
    for t in st.TABLES:
        assert t.indicator_ids() <= ids, t.indicator_ids() - ids
        assert len(t.sheet) <= 31


def test_the_workbook_and_the_gdp_page(store, tmp_path):
    site = tmp_path / "site"
    build_site(load_registry(), store, site_dir=site)
    wb = load_workbook(site / "data" / st.WORKBOOK)
    assert wb.sheetnames == ["Contents", "T1 Real sector", "T2a Fiscal EUR bn", "T2b Fiscal % GDP", "DSA1 Baseline",
                             "DSA2 EC stress tests"]
    ws = wb["T1 Real sector"]
    assert ws["A1"].value == "Table 1. Spain: Main Economic Indicators" and ws.freeze_panes == "B5"
    header = [c.value for c in ws[4]]
    assert header[1] == 2015 and header[17] == 2031 and header[18] == "Source, actual years"
    gdp_row = next(r for r in ws.iter_rows(min_row=5, values_only=True) if r[0] == "Gross domestic product")
    assert gdp_row[1] == 2.0 and gdp_row[12] == 2.0 and gdp_row[18] == "Eurostat" and gdp_row[19] == "IMF WEO"
    cons = next(r for r in ws.iter_rows(min_row=5, values_only=True) if r[0] == "Private consumption")
    assert cons[12] == st.NA and cons[19] == st.NA
    html = (site / "gdp.html").read_text(encoding="utf-8")
    assert '<h2 id="real-sector">' in html and f'href="data/{st.WORKBOOK}"' in html
    assert 'href="gdp.html#real-sector"' in html            # in the GDP tab's dropdown
    data_page = (site / "data.html").read_text(encoding="utf-8")
    assert f'href="data/{st.WORKBOOK}" download' in data_page
    fiscal_page = (site / "fiscal.html").read_text(encoding="utf-8")
    assert '<h2 id="government-operations">' in fiscal_page and '<h2 id="debt-sustainability">' in fiscal_page
    assert 'id="fig-dsa-fan"' in fiscal_page and "DSA 2. Public Debt: European Commission" in fiscal_page


@pytest.fixture
def fiscal_store(store):
    n = len(YEARS)
    gdp = [1000.0 * 1.04 ** k for k in range(n)]
    for ind_id, share_of_gdp in [("gg_revenue_eur", 0.42), ("gg_spending_eur", 0.45), ("gg_taxes_production_eur", 0.11),
                                 ("gg_taxes_income_eur", 0.12), ("gg_capital_taxes_eur", 0.004),
                                 ("gg_social_contributions_eur", 0.13), ("gg_nonproduced_eur", 0.0002),
                                 ("gg_interest_paid_eur", 0.024), ("gg_interest_received_eur", 0.005)]:
        store.save_series(ind_id, annual([g * share_of_gdp for g in gdp]))
    store.save_series("gg_balance_eur", annual([g * -0.03 for g in gdp]))
    # Debt: 100% of GDP, then 99%...; the real growth (2%) and deflator (2%) series.
    store.save_series("gg_debt_eur", annual([g * (1.0 - 0.01 * k) for k, g in enumerate(gdp)]))
    store.save_series("gdp_deflator_growth_annual", annual([2.0] * n))
    store.save_series("fc_imf_revenue", annual([5e11] * len(WEO), WEO))
    store.save_series("fc_imf_revenue_gdp", annual([43.0] * len(WEO), WEO))
    return store


def by_label(table, store, first=2015, last=2031):
    data = Data(load_registry(), store)
    return {r["label"]: dict(zip(range(first, last + 1), r["cells"]))
            for r in st.values(table, data, first, last, 2025) if not r["heading"]}


def test_government_operations(fiscal_store):
    eur, gdp = by_label(st.FISCAL_EUR, fiscal_store), by_label(st.FISCAL_GDP, fiscal_store)
    y = 2020
    nominal = 1000.0 * 1.04 ** (y - 2015)
    assert eur["Taxes"][y] == pytest.approx(nominal * (0.11 + 0.12 + 0.004) / 1000)    # € bn from € mn
    assert eur["Expense"][y] == pytest.approx(nominal * (0.45 - 0.0002) / 1000)       # TE less nonproduced assets
    assert gdp["Revenue"][y] == pytest.approx(42.0) and gdp["Social contributions"][y] == pytest.approx(13.0)
    assert gdp["Primary balance 4/"][y] == pytest.approx(-3.0 + 2.4 - 0.5)
    # Projections: the WEO's totals only.
    assert eur["Revenue"][2026] == pytest.approx(500.0) and gdp["Revenue"][2026] == 43.0
    assert eur["Taxes"][2026] is None


def test_debt_dynamics_add_up(fiscal_store):
    dsa = by_label(st.DSA_BASELINE, fiscal_store)
    y = 2020
    d_prev = 100.0 - 0.01 * 100 * (y - 1 - 2015)
    assert dsa["Public debt"][y] == pytest.approx(d_prev - 1.0)
    # Effective rate: interest paid over last year's debt; r and g effects as in the IMF's template.
    i = 0.024 * 1.04 / (d_prev / 100) * 100   # 2.4% of this year's GDP over last year's debt (GDP grows 4%)
    assert dsa["Effective interest rate (percent) 4/"][y] == pytest.approx(i)
    r = (1 + i / 100) / 1.02 - 1
    assert dsa["Real interest rate"][y] == pytest.approx(r / 1.02 * d_prev)
    assert dsa["Real growth rate"][y] == pytest.approx(-0.02 / 1.02 * d_prev)
    # The parts add up to the change in debt.
    flows = (dsa["Primary deficit"][y] + dsa["Automatic debt dynamics"][y]
             + dsa["Other identified flows: (minus) interest revenues 2/"][y])
    assert dsa["Contribution of identified flows 1/"][y] == pytest.approx(flows)
    assert dsa["Change in public debt"][y] == pytest.approx(flows + dsa["Contribution of residual 3/"][y])


def test_commission_stress_tests_come_from_the_dsm_file(tmp_path):
    data = Data(load_registry(), Store(tmp_path / "data"))
    raw = st.fiscal.load()["dsm"]
    assert st.span(st.DSA_STRESS, data) == (int(max(raw["history"])), int(max(raw["baseline"]["debt"])))
    t = st.web_table(st.DSA_STRESS, data)
    assert t["columns"][0] == max(raw["history"]) and t["column_notes"][0] == "" and t["column_notes"][1] == "proj."
    assert "European Commission projections" in t["caption"] and "Debt Sustainability Monitor" in t["note"]
    base = next(r for r in t["rows"] if r.get("label") == "Baseline (no policy change)")
    assert base["cells"][-1] == st.fmt(raw["baseline"]["debt"][max(raw["baseline"]["debt"])])
    fan = st.dsa_fan_chart(data)
    assert [s["name"] for s in fan["series"]] == ["Commission baseline", "90th percentile", "10th percentile"]
    assert fan["series"][1]["slot"] == fan["series"][2]["slot"] == 1
    facts = st.dsa_facts(data)
    assert any(f["label"].startswith("Sustainability gap S1") for f in facts)
