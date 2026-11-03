"""Spanish for the Tools page and the Fiscal Explorer (Batch 33d, part A). Read by scripts/write_catalogue.py; the keys
are the English exactly as the code writes it.

Most of these two pages is in their Spanish templates (templates/es/tools.html, templates/es/fiscal-explorer.html)
and in the words static/tools.js and static/fiscal.js carry for themselves; here is the text the Python modules put
in the pages' data (econpulse/tools.py, econpulse/fiscal.py), and the pages' descriptions in the English templates.
Labels the catalogue has already (Household consumption, Gross public debt, Primary balance...) are not repeated.
"""

PAIRS: dict[str, str] = {}

# ---------------------------------------------------------------- the pages' descriptions (templates/*.html)
PAIRS.update({
    "Interactive tools for the Spanish economy: change a setting and every number and chart recomputes in your browser.":
        "Herramientas interactivas sobre la economía española: cambie un ajuste y todas las cifras y gráficos se "
        "recalculan en su navegador.",
    "Spain's public debt and deficits, past and projected, with levers to try other paths.":
        "La deuda y los déficits públicos de España, pasados y proyectados, con palancas para probar otras sendas.",
})

# ---------------------------------------------------------------- Tools: the series against their pre-COVID trend (tools.TREND_SERIES)
PAIRS.update({
    "Real GDP": "PIB real",
    "Retail sales (real)": "Ventas minoristas (en términos reales)",
    "Consumer prices (SA)": "Precios de consumo (desest.)",
})

# ---------------------------------------------------------------- Fiscal Explorer: "The Past" (fiscal.HISTORY) and its sources
PAIRS.update({
    "Debt and balances": "Deuda y saldos",
    "Spending (general government)": "Gasto",          # the group "Spending" ("Spending" alone is demand, on the GDP page)
    "Spending by function": "Gasto por funciones",
    "Overall balance": "Saldo presupuestario",
    "Total revenue": "Ingresos totales",
    "Taxes on production and imports (VAT, excise)": "Impuestos sobre la producción y las importaciones (IVA, impuestos especiales)",
    "Taxes on income and wealth": "Impuestos sobre la renta y el patrimonio",
    "Total spending": "Gasto total",
    "Social benefits in cash": "Prestaciones sociales en efectivo",
    "Public employees' pay": "Remuneración de los empleados públicos",
    "Public investment": "Inversión pública",
    "Old age (mostly pensions)": "Vejez (sobre todo pensiones)",
    "Health (spending by function)": "Sanidad",       # "Health" alone is the industry, on the labour pages
    "Debt Sustainability Monitor 2025 (European Commission, Institutional Paper 332, February 2026)":
        "Debt Sustainability Monitor 2025 (Comisión Europea, Institutional Paper 332, febrero de 2026)",
    "2024 Ageing Report (European Commission and EPC, Institutional Paper 279, April 2024)":
        "Ageing Report 2024 (Comisión Europea y Comité de Política Económica, Institutional Paper 279, abril de 2024)",
})
