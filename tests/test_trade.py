"""Batches 26a and 26b: the Trade page, goods trade by product group and partner (Eurostat's Comext), services
by type and export and import prices (no network)."""

import numpy as np
import pandas as pd
import pytest

from econpulse import trade
from econpulse.build import NAV, NAV_SUBPAGES, build_site
from econpulse.registry import load_registry
from econpulse.sources import comext
from econpulse.store import Store
from econpulse.tables import Data


def payload(products: list[str], months: list[str], value) -> dict:
    """Comext-shaped JSON-stat: one value per product and month (None leaves it out)."""
    dims = {"freq": ["M"], "reporter": ["ES"], "partner": ["WORLD"], "product": products, "flow": ["2"],
            "indicators": ["VALUE_IN_EUROS"], "time": months}
    sizes = [len(v) for v in dims.values()]
    values = {}
    for p, prod in enumerate(products):
        for t, month in enumerate(months):
            v = value(prod, month)
            if v is not None:
                values[str(p * len(months) + t)] = v
    return {"id": list(dims), "size": sizes, "value": values,
            "dimension": {d: {"category": {"index": {k: i for i, k in enumerate(v)}}} for d, v in dims.items()}}


def test_groups_cover_every_chapter_once():
    assert comext.chapters("01-05,16") == ["01", "02", "03", "04", "05", "16"] and comext.chapters("total") == ["TOTAL"]
    keys = [i.key for i in load_registry() if i.id.startswith("trade_exp_") and i.key != "TOTAL"]
    assert len(keys) == len(trade.groups()) == 18
    covered = [c for k in keys for c in comext.chapters(k)]
    assert sorted(covered) == comext.CHAPTERS          # each chapter in exactly one group (77 and 98 are unused)


def test_download_in_batches_and_sum(monkeypatch):
    asked = []

    class Response:
        def __init__(self, products):
            self.products = products

        def json(self):
            return payload(self.products, ["2026-07", "2026-08"],
                           lambda p, m: None if (p, m) == ("16", "2026-08") else (1000.0 if p == "TOTAL" else 10.0))

    def get(url, params=None, timeout=None):
        products = [v for k, v in params if k == "product"]
        asked.append((dict((k, v) for k, v in params if k != "product"), products))
        return Response(products)

    comext.clear_cache()
    monkeypatch.setattr(comext.http, "get", get)
    s = comext.fetch("01-05,16", {"flow": "exports"}, since=pd.Timestamp("2026-07-01")).series
    assert all(len(products) <= comext.BATCH for _, products in asked) and len(asked) == 5
    assert asked[0][0]["sinceTimePeriod"] == "2026-07" and asked[0][0]["flow"] == "2"
    assert s.tolist() == [60.0, 50.0]                  # chapter 16 missing in August counts as zero
    asked.clear()
    comext.fetch("84", {"flow": "exports"}, since=pd.Timestamp("2026-07-01"))
    assert asked == []                                 # one download serves every group
    with pytest.raises(ValueError):
        comext.fetch("84", {"flow": "re-exports"})
    comext.clear_cache()


def trade_store(tmp_path) -> Store:
    store = Store(tmp_path / "data")
    m = pd.date_range("2018-01-01", "2026-08-01", freq="MS")
    n = len(m)
    growth = 1 + np.arange(n) / 1000
    store.save_series("trade_exp_total", pd.Series(30_000.0 * growth, index=m))
    store.save_series("trade_imp_total", pd.Series(35_000.0 * growth, index=m))
    for k, (slug, _) in enumerate(trade.groups()):
        store.save_series(f"trade_exp_{slug}", pd.Series((500.0 + 100 * k) * growth, index=m))
        store.save_series(f"trade_imp_{slug}", pd.Series(1_200.0 * growth if slug == "energy" else 900.0 * growth, index=m))
    return store


def test_trade_page(tmp_path):
    data = Data(load_registry(), trade_store(tmp_path))
    page = trade.page(data)
    labels = [f["label"] for f in page["facts"]]
    assert labels == ["Exports of goods", "Imports of goods", "Trade balance", "Balance without energy"]
    assert page["facts"][0]["value"] == "€395.1 bn"            # 12 x 30,000 x 1.0975, to August 2026
    first = page["table"]["rows"][0]
    assert first["label"] == "All goods" and first["cells"][2] == "100.0" and first["cells"][5].startswith("−")
    assert [r["label"] for r in page["table"]["rows"] if r["heading"]] == ["Food and drink", "Energy and materials",
                                                                          "Chemicals and plastics", "Manufactures"]
    ranking = next(c for c in page["rankings"] if c["id"] == "exports-ranking")
    assert ranking["series"][0]["x"][0] == "Other goods" and ranking["series"][0]["y"] == sorted(ranking["series"][0]["y"], reverse=True)
    assert len(page["charts"]) == 2 + 3 + 18
    assert [s["id"] for s in page["sections"]] == ["group-food", "group-materials", "group-chemicals", "group-manufactures"]


def test_trade_page_is_built_under_economic_activity(tmp_path):
    store = trade_store(tmp_path)
    assert "trade.html" not in dict(NAV) and ("trade.html", "Trade in goods and services") in NAV_SUBPAGES["activity.html"]
    assert dict(NAV)["activity.html"] == "Economic activity and external accounts"
    build_site(load_registry(), store, site_dir=tmp_path / "site")
    html = (tmp_path / "site" / "trade.html").read_text(encoding="utf-8")
    assert 'aria-current="page">Economic activity and external accounts</a>' in html and 'id="fig-trade-vehicles"' in html
    assert '<a href="trade.html">Trade in goods and services</a>' in html     # in the tab's dropdown
    assert "<h1>Economic activity and external accounts</h1>" in (tmp_path / "site" / "activity.html").read_text(encoding="utf-8")
    index = (tmp_path / "site" / "data" / "search.js").read_text(encoding="utf-8")
    assert '"Trade by partner","Trade","trade.html#partners"' in index      # its sections are still searchable
    assert "Vehicles and parts (87)" in html and (tmp_path / "site" / "data" / "charts-trade.js").exists()


def partner_payload(partners: list[str], months: list[str], value) -> dict:
    """Comext-shaped JSON-stat for all goods by partner."""
    dims = {"freq": ["M"], "reporter": ["ES"], "partner": partners, "product": ["TOTAL"], "flow": ["2"],
            "indicators": ["VALUE_IN_EUROS"], "time": months}
    values = {str(p * len(months) + t): v for p, part in enumerate(partners) for t, month in enumerate(months)
              if (v := value(part, month)) is not None}
    return {"id": list(dims), "size": [len(v) for v in dims.values()], "value": values,
            "dimension": {d: {"category": {"index": {k: i for i, k in enumerate(v)}}} for d, v in dims.items()}}


def test_totals_for_every_partner_in_one_request(monkeypatch):
    asked = []

    class Response:
        def json(self):
            return partner_payload(["WORLD", "FR", "CN"], ["2026-07", "2026-08", "2026-09"],
                                   lambda p, m: None if m == "2026-09" else {"WORLD": 1000.0, "FR": 150.0, "CN": 20.0}[p])

    def get(url, params=None, timeout=None):
        asked.append(list(params))
        return Response()

    comext.clear_cache()
    monkeypatch.setattr(comext.http, "get", get)
    since = pd.Timestamp("2026-07-01")
    fr = comext.fetch("TOTAL", {"flow": "exports", "partner": "FR"}, since=since).series
    cn = comext.fetch("TOTAL", {"flow": "exports", "partner": "CN"}, since=since).series
    assert len(asked) == 1 and ("product", "TOTAL") in asked[0] and not any(k == "partner" for k, _ in asked[0])
    assert fr.tolist() == [150.0, 150.0] and cn.tolist() == [20.0, 20.0]     # the month without figures is left out
    with pytest.raises(ValueError):
        comext.fetch("TOTAL", {"flow": "exports", "partner": "XX"}, since=since)
    comext.clear_cache()


def test_registry_matches_the_page():
    ids = {i.id for i in load_registry()}
    assert all(f"trade_exp_{s}" in ids and f"trade_imp_{s}" in ids for s, _, _ in trade.PARTNERS)
    assert all(f"svc_exp_{s}" in ids for s, _ in trade.SERVICES[1:] + trade.BUSINESS)
    assert all(trade.SERVICE_IDS[s][0] in ids for s in ("total", "travel"))
    assert all(f"export_prices_{s}" in ids and f"import_prices_{s}" in ids for s, _, _ in trade.PRICES)
    assert {"terms_of_trade", "terms_of_trade_goods", "terms_of_trade_industrial"} <= ids


def full_store(tmp_path) -> Store:
    store = trade_store(tmp_path)
    m = pd.date_range("2018-01-01", "2026-08-01", freq="MS")
    growth = 1 + np.arange(len(m)) / 1000
    for slug, exp, imp in (("eu", 18_000, 19_000), ("non_eu", 12_000, 16_000), ("france", 4_000, 3_000),
                           ("germany", 3_000, 4_000), ("china", 600, 3_500)):
        store.save_series(f"trade_exp_{slug}", pd.Series(exp * growth, index=m))
        store.save_series(f"trade_imp_{slug}", pd.Series(imp * growth, index=m))
    q = pd.date_range("2015-01-01", "2026-04-01", freq="QS")
    qg = 1 + np.arange(len(q)) / 100
    for ind_id, v in (("bop_q_exports_services", 60_000), ("bop_q_imports_services", 30_000),
                      ("bop_q_travel_credit", 25_000), ("bop_q_travel_debit", 8_000)):
        store.save_series(ind_id, pd.Series(v * qg, index=q))
    for slug, _ in trade.SERVICES[1:] + trade.BUSINESS:
        store.save_series(f"svc_exp_{slug}", pd.Series(4_000.0 * qg, index=q))
        store.save_series(f"svc_imp_{slug}", pd.Series(2_000.0 * qg, index=q))
    pm = pd.date_range("2015-01-01", "2026-09-01", freq="MS")
    ex, im = np.linspace(90, 121, len(pm)), np.linspace(90, 110, len(pm))
    for slug, _, _ in trade.PRICES:
        store.save_series(f"export_prices_{slug}", pd.Series(ex, index=pm))
        store.save_series(f"import_prices_{slug}", pd.Series(im, index=pm))
    store.save_series("terms_of_trade_industrial", pd.Series(ex / im * 100, index=pm))
    for ind_id in ("terms_of_trade", "terms_of_trade_goods"):
        store.save_series(ind_id, pd.Series(100 + np.sin(np.arange(len(q))), index=q))
    return store


def test_partners_services_and_prices(tmp_path):
    data = Data(load_registry(), full_store(tmp_path))
    page = trade.page(data)
    extras = {x["id"]: x for x in page["extras"]}
    assert list(extras) == ["partners", "services", "prices"]

    partners = extras["partners"]
    assert [r["label"] for r in partners["table"]["rows"]] == ["All partners", "European Union", "France", "Germany",
                                                               "Outside the EU", "China"]
    facts = {f["label"]: f for f in partners["facts"]}
    assert facts["Exports sold in the EU"]["value"] == "60.0%" and facts["Largest deficit"]["value"] == "China"
    assert facts["Largest market"]["value"] == "France" and facts["Largest supplier"]["value"] == "Germany"
    balances = next(c for c in partners["charts"] if c["id"] == "trade-partner-balances")
    assert [s["name"] for s in balances["series"]] == ["France", "Germany", "China"]   # Portugal has no data here

    services = extras["services"]
    rows = {r["label"]: r for r in services["table"]["rows"]}
    assert rows["Research and development"]["indent"] == 2 and services["table"]["caption"].endswith("Q2 2026")
    main = sum(float(rows[label]["cells"][0]) for _, label in trade.SERVICES)
    assert abs(float(rows["All services"]["cells"][0]) - main - float(rows["Other services"]["cells"][0])) < 0.5  # rounding
    assert [f["label"] for f in services["facts"]][-1] == "Exports other than tourism"

    prices = extras["prices"]
    assert [r["label"] for r in prices["table"]["rows"]] == [label for _, label, _ in trade.PRICES]
    assert [f["label"] for f in prices["facts"]] == ["Export prices", "Import prices", "Terms of trade",
                                                     "Export prices without energy"]
    assert {c["id"] for c in prices["charts"]} == {"prices-yoy", "terms-of-trade", "export-prices-groups",
                                                   "import-prices-groups"}
    assert len(page["charts"]) == 23 + 4 + 5 + 4


def test_new_sections_are_built(tmp_path):
    build_site(load_registry(), full_store(tmp_path), site_dir=tmp_path / "site")
    html = (tmp_path / "site" / "trade.html").read_text(encoding="utf-8")
    assert all(f'id="{s}"' in html for s in ("partners", "services", "prices"))
    assert 'id="fig-services-tourism"' in html and 'id="fig-terms-of-trade"' in html and "Rankings by product" in html
