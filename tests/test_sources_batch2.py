"""Parsers and request planning for the Batch 2 sources (no network)."""

import io
from datetime import date

import openpyxl
import pandas as pd
import pytest

from econpulse.sources import bde, derived, fred, ree, segsocial


# ---------------------------------------------------------------- Banco de España

def test_bde_parse_descending_with_gaps():
    item = {
        "fechas": ["2026-10-28T09:15:00Z", "2026-10-27T09:15:00Z", "2026-10-26T09:15:00Z"],
        "valores": [4.028, None, 3.95],
    }
    s = bde.parse(item)
    assert list(s.index) == [pd.Timestamp("2026-10-26"), pd.Timestamp("2026-10-28")]
    assert s.iloc[-1] == 4.028


def test_bde_daily_ranges():
    today = date(2026, 10, 30)
    # No history yet: walk back year by year.
    assert bde._daily_ranges(None, 2024, today) == ["2024", "2025", "2026"]
    # Recent history: one short request.
    assert bde._daily_ranges(pd.Timestamp("2026-10-20"), 2000, today) == ["3M"]
    assert bde._daily_ranges(pd.Timestamp("2026-03-01"), 2000, today) == ["12M"]
    assert bde._daily_ranges(pd.Timestamp("2024-06-01"), 2000, today) == ["36M"]
    # Very old history: years from the last stored one.
    assert bde._daily_ranges(pd.Timestamp("2020-05-01"), 2000, today) == ["2020", "2021", "2022", "2023", "2024", "2025", "2026"]


def test_bde_error_payloads(monkeypatch):
    class Resp:
        def __init__(self, payload):
            self.payload = payload

        def json(self):
            return self.payload

    monkeypatch.setattr(bde.http, "get", lambda *a, **k: Resp({"errNum": 412, "errMsgDebug": "El rango MAX no es correcto"}))
    with pytest.raises(ValueError, match="412"):
        bde.fetch("X", freq="M")
    monkeypatch.setattr(bde.http, "get", lambda *a, **k: Resp([{"codigo": "X", "errNum": 404}]))
    with pytest.raises(ValueError, match="not found"):
        bde.fetch("X", freq="M")


# ---------------------------------------------------------------- FRED

def test_fred_parse_skips_missing():
    text = "observation_date,DCOILBRENTEU\n2026-10-23,120.5\n2026-10-26,.\n2026-10-27,123.1\n"
    s = fred.parse(text, "DCOILBRENTEU").series
    assert list(s.index) == [pd.Timestamp("2026-10-23"), pd.Timestamp("2026-10-27")]
    assert s.iloc[-1] == 123.1


# ---------------------------------------------------------------- Seguridad Social

def _registrations_workbook() -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Datos totales de afiliados Medios en alta por Regímenes"])
    ws.append(["Régimen", "REGIMEN GENERAL\n", None, "TOTAL SISTEMA"])
    ws.append(["Periodo", "Régimen General (1)", None, None])
    ws.append(["Agosto 2026", 18000000.0, None, 22345226.4])
    ws.append(["Septiembre 2026", 18100000.0, None, 22437553.1])
    ws.append(["(1) Incluye ...", None, None, None])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_segsocial_parse_reads_named_column():
    s = segsocial.parse(_registrations_workbook(), "TOTAL SISTEMA")
    assert list(s.index) == [pd.Timestamp("2026-08-01"), pd.Timestamp("2026-09-01")]
    assert s.iloc[-1] == pytest.approx(22437553.1)


def test_segsocial_missing_column():
    with pytest.raises(ValueError, match="not found"):
        segsocial.parse(_registrations_workbook(), "NO SUCH COLUMN")


def test_segsocial_finds_link_on_page():
    html = ('<a href="/wps/wcm/connect/wss/abc/19_Serie+afiliaci%C3%B3n+media+por+reg%C3%ADmenes.xlsx'
            '?MOD=AJPERES&amp;CACHEID=X">(XLS, 53 KB)</a>')
    url = segsocial.find_file_url(html)
    assert url.startswith("https://www.seg-social.es/wps/wcm/connect/wss/abc/19_Serie+afiliaci")
    assert "&CACHEID=X" in url
    assert segsocial.find_file_url("<html>nothing here</html>") is None


# ---------------------------------------------------------------- Red Eléctrica

def test_ree_windows():
    assert ree.windows(date(2026, 1, 1), date(2026, 1, 16), 7) == [
        (date(2026, 1, 1), date(2026, 1, 7)), (date(2026, 1, 8), date(2026, 1, 14)), (date(2026, 1, 15), date(2026, 1, 16))]
    assert ree.windows(date(2024, 6, 1), date(2026, 2, 1), None) == [
        (date(2024, 6, 1), date(2024, 12, 31)), (date(2025, 1, 1), date(2025, 12, 31)), (date(2026, 1, 1), date(2026, 2, 1))]


def test_ree_intraday_prices_average_to_daily(monkeypatch):
    payload = {"included": [
        {"attributes": {"title": "PVPC", "values": []}},
        {"attributes": {"title": "Precio mercado spot", "values": [
            {"value": 100.0, "datetime": "2026-10-28T00:00:00.000+01:00"},
            {"value": 200.0, "datetime": "2026-10-28T23:45:00.000+01:00"},
            {"value": 50.0, "datetime": "2026-10-29T00:00:00.000+01:00"},
        ]}},
    ]}

    class Resp:
        def json(self):
            return payload

    monkeypatch.setattr(ree.http, "get", lambda *a, **k: Resp())
    monkeypatch.setattr(ree, "madrid_today", lambda: date(2026, 10, 29))
    s = ree.fetch("spot_price", since=pd.Timestamp("2026-10-28")).series
    assert s.to_dict() == {pd.Timestamp("2026-10-28"): 150.0, pd.Timestamp("2026-10-29"): 50.0}


def test_ree_error_payload():
    with pytest.raises(ValueError, match="REE error"):
        ree.parse({"errors": [{"detail": "no disponibles"}]}, "Demanda")


# ---------------------------------------------------------------- Derived

def test_derived_divide_fills_holidays_only_when_asked():
    brent = pd.Series([120.0, 123.0], index=pd.to_datetime(["2026-10-26", "2026-10-27"]))
    eurusd = pd.Series([1.2], index=pd.to_datetime(["2026-10-26"]))  # no fixing on the 27th
    inputs = {"brent": brent, "fx": eurusd}
    plain = derived.compute("divide", {"a": "brent", "b": "fx"}, inputs).series
    assert len(plain) == 1
    filled = derived.compute("divide", {"a": "brent", "b": "fx", "fill": 5}, inputs).series
    assert filled.round(4).tolist() == [100.0, 102.5]
