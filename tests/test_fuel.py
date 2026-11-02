"""Batch 32b: petrol and diesel prices from the Weekly Oil Bulletin (no network)."""

import io
from datetime import datetime
from types import SimpleNamespace

import numpy as np
import openpyxl
import pandas as pd

from econpulse import fuel
from econpulse.build import build_site
from econpulse.registry import load_registry
from econpulse.sources import oilbulletin
from econpulse.store import Store
from econpulse.tables import Data

PAGE_HTML = ('<a href="/document/download/aaa_en?filename=Weekly%20prices%20with%20Taxes.xlsx">Latest</a>'
             '<a href="/document/download/906e60ca_en?filename=Weekly_Oil_Bulletin_Prices_History_maticni_4web.xlsx">'
             'History</a>')


def bulletin_workbook() -> bytes:
    """The history workbook's layout: column names, a row of product names, a row of units, the weeks (newest
    first) and notes at the foot."""
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    for sheet, tag, scale in (("Prices with taxes", "with_tax", 1.0), ("Prices wo taxes", "wo_tax", 0.6)):
        ws = wb.create_sheet(sheet)
        ws.append(["Consumer prices", "CTR", f"EUR_price_{tag}_euro95", f"EUR_price_{tag}_diesel", "CTR",
                   f"ES_price_{tag}_euro95", f"ES_price_{tag}_diesel"])
        ws.append([None, None, "Euro-super 95", "Gas oil automobile", None, "Euro-super 95", "Gas oil automobile"])
        ws.append(["Date", None, "1000 l", "1000 l", None, "1000 l", "1000 l"])
        ws.append([datetime(2026, 10, 26), "EUR_", 2032.0 * scale, 2201.2 * scale, "ES_", 1751.1 * scale, 1887.8 * scale])
        ws.append([datetime(2026, 10, 19), "EUR_", 2055.4 * scale, 2188.8 * scale, "ES_", 1780.5 * scale, None])
        ws.append(["Notes:", None, None, None, None, None, None])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_the_bulletin_is_read_once_and_in_euros_a_litre(monkeypatch):
    book = bulletin_workbook()
    calls = []

    def fake_get(url, **_):
        calls.append(url)
        return SimpleNamespace(text=PAGE_HTML) if url == oilbulletin.PAGE else SimpleNamespace(content=book)

    monkeypatch.setattr(oilbulletin.http, "get", fake_get)
    oilbulletin.clear_cache()
    try:
        petrol = oilbulletin.fetch("ES_price_with_tax_euro95")
        diesel = oilbulletin.fetch("ES_price_with_tax_diesel")
        pretax = oilbulletin.fetch("ES_price_wo_tax_euro95")
        ea = oilbulletin.fetch("EUR_price_with_tax_diesel")
    finally:
        oilbulletin.clear_cache()
    assert calls == [oilbulletin.PAGE, "https://energy.ec.europa.eu/document/download/906e60ca_en"
                     "?filename=Weekly_Oil_Bulletin_Prices_History_maticni_4web.xlsx"]   # one page, one workbook
    assert list(petrol.series.index) == [pd.Timestamp("2026-10-19"), pd.Timestamp("2026-10-26")]
    assert round(petrol.series.iloc[-1], 6) == 1.7511 and round(pretax.series.iloc[-1], 6) == round(1751.1 * 0.6 / 1000, 6)
    assert len(diesel.series) == 1 and round(ea.series.iloc[-1], 6) == 2.2012     # a blank week is left out
    assert petrol.meta["url"].endswith("Prices_History_maticni_4web.xlsx")


def test_registry_and_tiles():
    inds = {i.id: i for i in load_registry()}
    assert {i for i in inds if inds[i].source == "oilbulletin"} == {
        "petrol_price", "diesel_price", "petrol_price_pretax", "diesel_price_pretax", "petrol_price_ea", "diesel_price_ea"}
    tiles = [i.id for i in sorted((i for i in inds.values() if i.tile), key=lambda i: i.tile)]
    assert tiles[-6:] == ["ibex35", "eurusd", "brent_usd", "electricity_price", "petrol_price", "diesel_price"]
    assert inds["petrol_price"].unit == "€/l" and inds["petrol_price"].source_name.startswith("European Commission")


def fuel_store(tmp_path) -> Store:
    store = Store(tmp_path / "data")
    weeks = pd.date_range("2024-01-01", "2026-10-26", freq="W-MON")
    path = np.linspace(0, 1, len(weeks))
    for fuel_id, start, ea, tax in (("petrol", 1.60, 1.15, 0.67), ("diesel", 1.50, 1.13, 0.73)):
        price = start + 0.25 * path
        store.save_series(f"{fuel_id}_price", pd.Series(price, index=weeks))
        store.save_series(f"{fuel_id}_price_pretax", pd.Series(price * tax, index=weeks))
        store.save_series(f"{fuel_id}_price_ea", pd.Series(price * ea, index=weeks))
    return store


def test_facts(tmp_path):
    facts = fuel.facts(Data(load_registry(), fuel_store(tmp_path)))
    assert [f["label"] for f in facts] == ["Petrol (Euro-super 95), 26 Oct 2026", "Diesel, 26 Oct 2026",
                                           "Taxes in the pump price", "Against the euro area"]
    assert facts[0]["value"] == "€1.850 a litre" and facts[0]["sub"].endswith("% on a year earlier")
    assert facts[2]["value"] == "33%" and facts[2]["sub"] == "of petrol's; 27% of diesel's"
    assert facts[3]["value"] == "−13%" and facts[3]["sub"].endswith("diesel −12%")


def test_the_inflation_page_and_the_home_tiles(tmp_path):
    build_site(load_registry(), fuel_store(tmp_path), site_dir=tmp_path / "site")
    site = tmp_path / "site"
    inflation = (site / "inflation.html").read_text(encoding="utf-8")
    assert 'id="fig-fuel"' in inflation and 'id="fig-fuel-ea"' in inflation
    assert "Taxes in the pump price" in inflation and "At the pump, € a litre" in inflation
    home = (site / "index.html").read_text(encoding="utf-8")
    tiles = home.split('<div class="tiles">', 1)[1].split("</div>", 1)[0]
    assert '<span class="tile-label">Petrol (Euro-super 95)</span>' in tiles
    assert '<span class="tile-label">Diesel</span>' in tiles and "1.850<span class=\"tile-unit\"> €/l</span>" in tiles
    charts = (site / "data" / "charts-inflation.js").read_text(encoding="utf-8")
    assert '"name":"Petrol pre-tax"' in charts and '"dash":"dash"' in charts
