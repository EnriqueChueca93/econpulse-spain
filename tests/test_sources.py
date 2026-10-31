"""Parsers for each source, on small recorded payloads (no network)."""

import pandas as pd
import pytest

from econpulse.sources import derived, ecb, eurostat, ine
from econpulse.sources.base import parse_period


@pytest.mark.parametrize("label, expected", [
    ("2026-09", "2026-09-01"),
    ("2026M09", "2026-09-01"),
    ("2026-Q3", "2026-07-01"),
    ("2026Q4", "2026-10-01"),
    ("2026", "2026-01-01"),
    ("2026-10-30", "2026-10-30"),
])
def test_parse_period(label, expected):
    assert parse_period(label) == pd.Timestamp(expected)


def test_parse_period_rejects_unknown():
    with pytest.raises(ValueError):
        parse_period("Sept 2026")


def test_ine_parse_months_quarters_and_flash():
    payload = {
        "COD": "X", "Nombre": "Nacional. Índice general. Variación anual. ",
        "Data": [
            {"Fecha": 0, "FK_TipoDato": 1, "FK_Periodo": 9, "Anyo": 2026, "Valor": 4.2, "Secreto": False},
            {"Fecha": 0, "FK_TipoDato": 3, "FK_Periodo": 10, "Anyo": 2026, "Valor": 4.9, "Secreto": False},
            {"Fecha": 0, "FK_TipoDato": 1, "FK_Periodo": 11, "Anyo": 2026, "Valor": None, "Secreto": False},
        ],
    }
    result = ine.parse(payload)
    assert list(result.series.index) == [pd.Timestamp("2026-09-01"), pd.Timestamp("2026-10-01")]
    assert result.series.iloc[-1] == 4.9
    assert result.meta["flash"] is True

    quarterly = {"Data": [{"Fecha": 0, "FK_TipoDato": 2, "FK_Periodo": 21, "Anyo": 2026, "Valor": 127.17}]}
    q = ine.parse(quarterly)
    assert q.series.index[0] == pd.Timestamp("2026-07-01")
    assert q.meta["flash"] is False


def test_ine_parse_empty_raises():
    with pytest.raises(ValueError):
        ine.parse({"Data": []})


def test_eurostat_parse_sparse_values():
    payload = {
        "label": "Unemployment", "id": ["freq", "geo", "time"], "size": [1, 1, 3],
        "dimension": {"time": {"category": {"index": {"2026-07": 0, "2026-08": 1, "2026-09": 2}}}},
        "value": {"0": 10.4, "2": 10.3},  # August missing
    }
    s = eurostat.parse(payload).series
    assert list(s.index) == [pd.Timestamp("2026-07-01"), pd.Timestamp("2026-09-01")]
    assert list(s) == [10.4, 10.3]


def test_eurostat_parse_rejects_ambiguous_query():
    payload = {"id": ["unit", "time"], "size": [5, 1],
               "dimension": {"time": {"category": {"index": {"2026-09": 0}}}}, "value": {"0": 1}}
    with pytest.raises(ValueError, match="unit"):
        eurostat.parse(payload)


def test_eurostat_parse_error_payload():
    with pytest.raises(ValueError):
        eurostat.parse({"error": [{"status": 400, "label": "bad"}]})


def test_ecb_parse_csv():
    text = "KEY,FREQ,TIME_PERIOD,OBS_VALUE\nA,D,2026-10-29,2.5\nA,D,2026-10-30,2.5\nA,D,2026-10-31,\n"
    s = ecb.parse(text).series
    assert list(s.index) == [pd.Timestamp("2026-10-29"), pd.Timestamp("2026-10-30")]
    assert s.iloc[-1] == 2.5


def test_derived_subtract_aligns_and_scales():
    idx = pd.date_range("2026-07-01", periods=3, freq="MS")
    es = pd.Series([3.9, 4.0, 3.93], index=idx)
    de = pd.Series([3.5, 3.48], index=idx[1:])
    s = derived.compute("subtract", {"a": "es", "b": "de", "scale": 100}, {"es": es, "de": de}).series
    assert list(s.index) == list(idx[1:])
    assert s.round(4).tolist() == [50.0, 45.0]


def test_source_urls():
    assert "IPC290750" in ine.source_url("IPC290750")
    assert ecb.source_url("FM/D.U2.EUR.4F.KR.DFR.LEV").endswith("FM/FM.D.U2.EUR.4F.KR.DFR.LEV")
    assert "une_rt_m" in eurostat.source_url("une_rt_m")
