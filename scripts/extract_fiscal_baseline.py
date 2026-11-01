"""Extract Spain's fiscal baseline for the Fiscal Explorer from two European Commission workbooks
into econpulse/fiscal_baseline.json. Run it again when a new edition comes out (the Debt
Sustainability Monitor every year around February, the Ageing Report every three years):

    .venv/Scripts/python scripts/extract_fiscal_baseline.py

It downloads the two files (about 17 MB) unless given local copies:

    .venv/Scripts/python scripts/extract_fiscal_baseline.py --dsm dsm.xlsx --ar annex.xlsx

Debt Sustainability Monitor 2025 (Institutional Paper 332, February 2026), "country fiches
tables and graphs", sheet ES: the baseline debt projection to 2036 and its drivers, the other
deterministic scenarios, the stochastic percentiles and the debt history since 1970.
2024 Ageing Report (Institutional Paper 279, April 2024), statistical annex: yearly ageing
costs (pensions, health care, long-term care, education), potential growth and the nominal
interest rate assumed for Spain, 2022-2070.
"""

import argparse
import io
import json
import sys
from datetime import date
from pathlib import Path

import openpyxl
import requests

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from econpulse.config import USER_AGENT  # noqa: E402

OUT = ROOT / "econpulse" / "fiscal_baseline.json"
DSM = {"edition": "Debt Sustainability Monitor 2025 (European Commission, Institutional Paper 332, February 2026)",
       "page": "https://economy-finance.ec.europa.eu/publications/debt-sustainability-monitor-2025_en",
       "file": "https://economy-finance.ec.europa.eu/document/download/19852ffb-d8c5-4d47-a402-aa6179dc8051_en"
               "?filename=DSM%202025%20country%20fiches%20tables%20and%20graphs.xlsx"}
AR = {"edition": "2024 Ageing Report (European Commission and EPC, Institutional Paper 279, April 2024)",
      "page": "https://economy-finance.ec.europa.eu/publications/2024-ageing-report-economic-and-budgetary-projections-eu-member-states-2022-2070_en",
      "file": "https://economy-finance.ec.europa.eu/document/download/403cc04f-9487-406b-a48a-22538e0d461c_en"
              "?filename=2024_Ageing_Report-Statistical_annex_all_horizontal_tables.xlsx"}

# DSM baseline rows (column B labels) -> our names
DSM_ROWS = {"Gross debt ratio": "debt", "(1) Primary balance (1.1+1.2+1.3)": "primary_balance",
            "(1.1) Structural primary balance (1.1.1-1.1.2+1.1.3)": "structural_primary_balance",
            "(1.1.1) Structural primary balance (before CoA)": "spb_before_ageing",
            "(1.1.2) Cost of ageing (CoA)": "cost_of_ageing", "Pensions": "coa_pensions", "Health care": "coa_health",
            "Long-term care": "coa_ltc", "Education": "coa_education",
            "(1.1.3) Others (taxes and property income)": "others", "(1.2) Cyclical component": "cyclical",
            "(1.3) One-off and other temporary measures": "one_offs", "(2.1) Interest expenditure": "interest",
            "(2.2) Growth effect (real)": "growth_effect", "(2.3) Inflation effect": "inflation_effect",
            "(3) Stock-flow adjustments": "stock_flow", "Structural balance": "structural_balance",
            "Gross financing needs": "gross_financing_needs"}
SCENARIOS = {"Histo_SPB": "Historical structural primary balance", "Shock SPB": "Lower structural primary balance",
             "Adverse r-g": "Adverse interest-growth differential", "Financial stress": "Financial stress"}
AR_TABLES = {"Table II.1.64:": "pensions", "Table II.1.107:": "health", "Table II.1.114:": "ltc",
             "Table II.1.131:": "education", "Table II.1.14:": "potential_growth", "Table II.1.23:": "interest_rate"}


def load(path_or_url: str) -> openpyxl.Workbook:
    if path_or_url.startswith("http"):
        r = requests.get(path_or_url, headers={"User-Agent": USER_AGENT}, timeout=120)
        r.raise_for_status()
        return openpyxl.load_workbook(io.BytesIO(r.content), read_only=True, data_only=True)
    return openpyxl.load_workbook(path_or_url, read_only=True, data_only=True)


def num(v):
    return round(float(v), 4) if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def years_in(row) -> dict[int, int]:
    """Column index -> year, for a header row of years."""
    return {i: int(v) for i, v in enumerate(row) if isinstance(v, (int, float)) and 1960 <= v <= 2100 and v == int(v)}


def dsm(wb) -> dict:
    rows = list(wb["ES"].iter_rows(values_only=True))
    out, header = {"baseline": {}, "scenarios": {}, "percentiles": {}, "history": {}, "gaps": {}}, None
    gap = None
    for i, r in enumerate(rows):
        r = list(r)
        labels = [c for c in r if isinstance(c, str)]
        if any(isinstance(c, str) and c.startswith("Spain - baseline scenario") for c in r):
            header = years_in(r)
            continue
        if header and len(out["baseline"]) < len(DSM_ROWS):
            for label in labels:
                key = DSM_ROWS.get(label.strip())
                if key and key not in out["baseline"]:
                    pos = r.index(label)
                    values = [num(c) for c in r[pos + 1:]]
                    cols = sorted(header)
                    # Rows with fewer values (the cost of ageing) are right-aligned to the last year.
                    values = [v for v in values if v is not None][:len(cols)]
                    years = [header[c] for c in cols][len(cols) - len(values):]
                    out["baseline"][key] = dict(zip(years, values))
        # S1 and S2: the Commission's long-term sustainability gaps, baseline value (the first number).
        for label in labels:
            if label.startswith("S1 indicator") or label.startswith("S2 indicator"):
                gap = label[:2]
            elif gap and label.strip().startswith("Overall value"):
                first = next((num(c) for c in r if num(c) is not None), None)
                out["gaps"][gap] = first
                gap = None
        if "Drivers of annual change in debt ratio, baseline - ES" in labels:
            scen_header = years_in(rows[i + 1])
            for r2 in rows[i + 2:i + 10]:
                r2 = list(r2)
                for label, name in SCENARIOS.items():
                    if label in r2:
                        pos = r2.index(label)
                        vals = [num(c) for c in r2[pos + 1:pos + 1 + len(scen_header)]]
                        out["scenarios"][name] = dict(zip(sorted(scen_header.values()), vals))
        for c in r:
            if isinstance(c, str) and c.strip() in ("p10", "p20", "p40", "p60", "p80", "p90"):
                pos = r.index(c)
                vals = [num(v) for v in r[pos + 1:pos + 8]]
                if all(v is not None for v in vals) and c.strip() not in out["percentiles"]:
                    out["percentiles"][c.strip()] = dict(zip(range(2024, 2031), vals))
        if labels == ["Debt-to-GDP ratio"] and i + 2 < len(rows) and not out["history"]:
            hist_years = years_in(rows[i + 1])
            values = list(rows[i + 2])
            out["history"] = {y: num(values[c]) for c, y in hist_years.items() if c < len(values) and num(values[c]) is not None}
    return out


def ageing(wb) -> dict:
    rows = list(wb["cross-country_tables"].iter_rows(values_only=True))
    out, current, header = {}, None, None
    for r in rows:
        cells = [c for c in r if c is not None]
        if not cells:
            continue
        first = str(cells[0])
        match = next((name for prefix, name in AR_TABLES.items() if first.startswith(prefix)), None)
        if isinstance(cells[0], str) and first.startswith("Table II."):
            current, header = match, None
            continue
        if current and header is None and len(years_in(r)) > 20:
            header = years_in(r)
            continue
        if current and header and r[0] == "ES" or (current and header and "ES" in r[:2]):
            out[current] = {y: num(r[c]) for c, y in header.items() if num(r[c]) is not None}
            current = None
    return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--dsm", default=DSM["file"])
    p.add_argument("--ar", default=AR["file"])
    args = p.parse_args()
    data = {"extracted": date.today().isoformat(), "country": "Spain", "dsm_source": DSM, "ar_source": AR,
            "dsm": dsm(load(args.dsm)), "ageing_report": ageing(load(args.ar))}
    OUT.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)}: baseline rows {sorted(data['dsm']['baseline'])}, "
          f"scenarios {sorted(data['dsm']['scenarios'])}, ageing series {sorted(data['ageing_report'])}")


if __name__ == "__main__":
    main()
