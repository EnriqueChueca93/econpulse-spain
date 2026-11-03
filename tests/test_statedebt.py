"""Batch 34b: the State's debt from the Tesoro's list of securities (no network)."""

from datetime import date

import pandas as pd
import pytest

from econpulse import i18n, statedebt
from econpulse.registry import load_registry
from econpulse.sources import tesoro
from econpulse.store import Store
from econpulse.tables import Data


def page(bond_rows: list[str], letra_rows: list[str]) -> str:
    """A page shaped like the Tesoro's "Valores en circulación"."""
    row = lambda cells: "<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>"
    return (
        '<p>(*) Datos a 16/10/2026. (El saldo en circulación de cada valor se actualiza…)</p>'
        '<table class="circ-table" id="tablaLetras"><thead><tr><th>Código ISIN</th><th>Fecha de vencimiento</th>'
        '<th>Saldo en circulación (*)</th></tr></thead><tbody>' + "".join(letra_rows) + '</tbody></table>'
        '<table class="circ-table" id="tablaByo"><thead><tr><th>Código ISIN</th><th>Fecha de vencimiento</th>'
        '<th>Saldo en circulación (*)</th><th>Coeficiente de indexación</th><th>Valor facial</th></tr></thead><tbody>'
        + "".join(bond_rows) + '</tbody></table><p>(*) Datos a 20/10/2026.</p>'
    ), row


def sample() -> str:
    _, row = page([], [])
    letras = [row([f"ES0L0270{i:04d}", f"15/0{i}/2027", "8.000,0"]) for i in range(1, 7)]
    bonds = [row(["ES00000128H5  O 1,30**", "31/10/2026", "28.000,0", "", ""]),          # matured before the fetch
             row(["ES0000011868 O 6,00", "31/01/2029", "26.658,8", "", ""]),               # an old issue, no **
             row(["ES00000128S2  O €i 0,65**", "30/11/2027", "22.998,0", "1,31518", "17.486,6"]),
             row(["ES0000012J07 O 1,00** (1)", "30/07/2042", "18.385,0", "", ""]),
             row(["ES0000012J15  B 0,00**", "29/02/2028", "22.790,2", "", ""])]
    bonds += [row([f"ES00000129{i:02d}  O 3,00**", f"30/04/{2030 + i}", "30.000,0", "", ""]) for i in range(40)]
    html, _ = page(bonds, letras)
    return html


def test_the_tesoro_page_is_read_security_by_security():
    snap = tesoro.parse(sample())
    assert len(snap["letras"]) == 6 and len(snap["bonds"]) == 45
    assert snap["as_of"] == {"letras": "2026-10-16", "bonds": "2026-10-20"}
    by = {b["isin"]: b for b in snap["bonds"]}
    assert by["ES0000011868"]["coupon"] == 6.0 and by["ES0000011868"]["type"] == "O"
    assert by["ES00000128S2"]["linked"] and by["ES00000128S2"]["amount"] == 22998.0
    assert by["ES0000012J07"]["green"] and by["ES0000012J15"]["type"] == "B" and by["ES0000012J15"]["coupon"] == 0.0
    # Securities that matured since the page's date are left out from the day of the fetch.
    letras, bonds = tesoro.outstanding(snap, date(2026, 11, 3))
    assert "ES00000128H5" not in {b["isin"] for b in bonds} and len(bonds) == 44 and len(letras) == 6


def test_a_page_that_reads_wrong_is_refused():
    bad = sample().replace("<td>ES0000011868 O 6,00</td>", "<td>ES0000011868 O</td>")
    with pytest.raises(ValueError, match="could not be read"):
        tesoro.parse(bad)
    with pytest.raises(ValueError, match="two tables"):
        tesoro.parse("<html><table><tr><td>x</td></tr></table></html>")


def test_repayments_by_year():
    snap = tesoro.parse(sample())
    on = date(2026, 11, 3)
    years = statedebt.repayments(snap, on)
    assert min(years) == 2026 and max(years) == 2069
    # 2027: six Letras (48.0) and the inflation-linked bond (23.0) fall due; coupons on everything still out.
    principal, interest = years[2027]
    assert principal == pytest.approx(48 + 22.998)
    coupons_2027 = (6.0 * 26.6588 + 0.65 * 22.998 + 1.0 * 18.385 + 3.0 * 30 * 40) / 100
    assert interest == pytest.approx(coupons_2027)
    # The rest of 2026: only the inflation-linked bond's 30 November coupon falls after 3 November.
    assert years[2026] == pytest.approx((0.0, 0.65 * 22.998 / 100))
    # A 29 February maturity pays its coupon on 28 February in other years; zero coupon, no interest.
    assert years[2028][0] == pytest.approx(22.7902)
    assert sum(p for p, _ in years.values()) == pytest.approx(sum(x["amount"] for x in sum(tesoro.outstanding(snap, on), [])) / 1000)


def test_the_check_and_the_facts(tmp_path):
    store = Store(tmp_path / "data")
    snap = tesoro.parse(sample())
    store.save_series("state_debt_outstanding", pd.Series([1.0], index=pd.DatetimeIndex(["2026-11-03"])))
    store.save_catalog({"state_debt_outstanding": {"securities": snap}})
    data = Data(load_registry(), store)
    assert statedebt.check(data)[0] == statedebt.PENDING
    facts = statedebt.facts(data)
    assert facts[-1]["value"] == "awaiting AI check" and facts[0]["value"].startswith("€")
    statedebt.confirm(store, "AI check (Claude)", against="the Tesoro's page")
    status, record = statedebt.check(data)
    assert status == statedebt.CHECKED and record["as_of"]["bonds"] == "2026-10-20"
    with i18n.using("es"):
        facts = statedebt.facts(Data(load_registry(), store))
        assert facts[-1]["value"] == "verificado por IA" and facts[0]["value"].endswith("mm €")
    # A new edition (an amount changed after an auction) needs a new check.
    snap["bonds"][1]["amount"] += 1000
    store.save_catalog({"state_debt_outstanding": {"securities": snap}})
    assert statedebt.check(Data(load_registry(), store))[0] == statedebt.PENDING


def test_the_bubbles_by_group(tmp_path):
    store = Store(tmp_path / "data")
    store.save_series("state_debt_outstanding", pd.Series([1.0], index=pd.DatetimeIndex(["2026-11-03"])))
    store.save_catalog({"state_debt_outstanding": {"securities": tesoro.parse(sample())}})
    spec = statedebt.bonds_chart(Data(load_registry(), store))
    assert spec["kind"] == "bubble" and [s["name"] for s in spec["series"]] == ["Ordinary", "Inflation-linked", "Green"]
    assert sum(len(s["x"]) for s in spec["series"]) == 44 and spec["series"][1]["text"] == ["ES00000128S2"]
