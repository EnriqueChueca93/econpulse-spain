"""Batch 29b: pensions against other countries, the ageing population, the 2023 reform and the official
assessments, whose figures are entered by hand and await an AI check (no network)."""

import copy

import numpy as np
import pandas as pd

from econpulse import pensions
from econpulse.__main__ import print_assessments
from econpulse.pages import build_page, page_indicator_ids
from econpulse.registry import load_registry
from econpulse.store import Store
from econpulse.tables import Data


def test_registry():
    inds = load_registry()
    ids = {i.id for i in inds}
    assert page_indicator_ids("pensions") <= ids
    assert sum(i.section == "pensions" for i in inds) == 158
    assert {"pension_spending_eu", "old_age_dep_proj_es", "ss_balance_pl", "public_pensions_jp", "replacement_rate_us"} <= ids


def test_documents_and_checks(tmp_path):
    store = Store(tmp_path / "data")
    docs = {d.id: d for d in pensions.documents(store)}
    assert set(docs) == {"reform2023", "ageing_report_2024", "airef_2025", "airef_2026", "bde_2023"}
    assert all(d.status == pensions.PENDING for d in docs.values())
    assert all(f["label"] and f["value"] and f["where"] for d in docs.values() for f in d.figures)
    projection = docs["ageing_report_2024"].raw["projection"]
    assert all(len(v) == len(projection["years"]) for k, v in projection.items() if k != "years")
    assert docs["reform2023"].raw["mei"][2029] == 1.2 and docs["reform2023"].raw["solidarity"][2045] == [5.5, 6.0, 7.0]

    record = pensions.confirm(store, "airef_2026", "AI check (test)", against="the PDF")
    docs = {d.id: d for d in pensions.documents(store)}
    assert docs["airef_2026"].status == pensions.CHECKED and docs["airef_2026"].check["checked_against"] == "the PDF"
    assert record["fingerprint"] == pensions.fingerprint(docs["airef_2026"].raw)
    changed = copy.deepcopy(docs["airef_2026"].raw)
    changed["figures"][0]["value"] = "1.7% of GDP"
    assert pensions.fingerprint(changed) != record["fingerprint"]       # a changed figure needs a new check
    assert print_assessments(store) == 4


def comparison_store(tmp_path) -> Store:
    store = Store(tmp_path / "data")
    years = pd.date_range("2000-01-01", "2024-01-01", freq="YS")
    for k, (slug, _) in enumerate(pensions.EU_AREAS):
        store.save_series(f"pension_spending_{slug}", pd.Series(10.0 + k * 0.5, index=years))
        store.save_series(f"ss_balance_{slug}", pd.Series(-0.3 + k * 0.1, index=years))
        past = pd.date_range("1960-01-01", "2025-01-01", freq="YS")
        store.save_series(f"old_age_dep_{slug}", pd.Series(np.linspace(15.0, 30.0 + k, len(past)), index=past))
        future = pd.date_range("2022-01-01", "2100-01-01", freq="YS")
        store.save_series(f"old_age_dep_proj_{slug}", pd.Series(np.linspace(30.0, 60.0 + k, len(future)), index=future))
    rates = {"es": 86.3, "fr": 70.0, "de": 53.3, "it": 79.0, "nl": 96.0, "pt": 92.7, "pl": 40.6, "uk": 54.2,
             "us": 51.3, "ca": 45.1, "jp": 42.4}
    for slug, rate in rates.items():
        store.save_series(f"replacement_rate_{slug}", pd.Series([rate], index=[pd.Timestamp("2024-01-01")]))
        store.save_series(f"public_pensions_{slug}", pd.Series(rate / 8, index=pd.date_range("2000-01-01", "2021-01-01", freq="YS")))
    return store


def test_comparisons(tmp_path):
    data = Data(load_registry(), comparison_store(tmp_path))
    facts = {f["label"]: f for f in pensions.comparison_facts(data)}
    assert facts["Pension spending"]["value"] == "10.0% of GDP" and "EU 13.5%" in facts["Pension spending"]["sub"]
    assert facts["Replacement rate"]["sub"].endswith("the third highest of the 11 countries")
    table = pensions.comparison_table(data)
    rows = {r["label"]: r["cells"] for r in table["rows"]}
    assert rows["Spain"][2] == "86.3" and rows["United Kingdom"][0] == "–" and rows["EU"][2] == "–"
    chart = pensions.dependency_chart(data)
    names = [s["name"] for s in chart["series"]]
    assert names == ["Spain", "Spain, projected", "EU", "EU, projected"]
    assert chart["series"][1]["x"][0] == "2026-01-01" and chart["series"][1]["dash"] == "dot"
    ranking = pensions.replacement_ranking(data)
    assert ranking["series"][0]["x"][0] == "Netherlands" and ranking["pick"]


def test_the_page(tmp_path):
    page = build_page("pensions", load_registry(), comparison_store(tmp_path))
    blocks = {b["id"]: b for b in page["blocks"]}
    assert blocks["comparison"]["picker"] and not blocks["ageing"]["picker"]
    assert [d["id"] for d in blocks["reform"]["documents"]] == ["reform2023"]
    assert [d["id"] for d in blocks["assessments"]["documents"]] == ["ageing_report_2024", "airef_2026", "airef_2025", "bde_2023"]
    charts = {c["id"]: c for c in page["charts"]}
    assert charts["pension-projection"]["pick"] and charts["pension-projection"]["subtitle"].endswith("awaiting AI check")
    assert charts["mei"]["series"][0]["y"] == [0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2]
