"""Spanish for the IMF-style tables, part B (Batch 33c-3): Table 3 (Selected Financial Soundness Indicators),
Table 4 (Balance of Payments), Table 5 (External Debt) and the monetary and credit table, in their annual, quarterly
and monthly views (econpulse/sectortables.py). Terms follow the IMF's Spanish usage: the Financial Soundness
Indicators compilation guide, the sixth edition of the Balance of Payments Manual (MBP6), the external debt
statistics guide and the ECB's Spanish balance-sheet items. Tables 1-2, the DSA and the shared captions are in
catalogue_imf_a.py. Read by scripts/write_catalogue.py; the keys are the English exactly as the code writes it.
"""

PAIRS: dict[str, str] = {}

# ---------------------------------------------------------------- the tables' introductions and units
PAIRS.update({
    "Bank capital, asset quality and profitability, banks' exposures at home, and the debt of firms and households.":
        "El capital, la calidad de los activos y la rentabilidad de los bancos, sus exposiciones en España y la "
        "deuda de empresas y hogares.",
    "Spain's transactions with the rest of the world, and the investment position they build up.":
        "Las transacciones de España con el resto del mundo y la posición de inversión que van acumulando.",
    "What Spanish residents owe to non-residents, by sector and instrument.":
        "Lo que los residentes en España deben a los no residentes, por sector e instrumento.",
    "The Banco de España's balance sheet in the Eurosystem, bank lending and deposits, and interest rates.":
        "El balance del Banco de España en el Eurosistema, el crédito y los depósitos bancarios y los tipos de "
        "interés.",
    "Billions of euros": "Miles de millones de euros",
    "Percent of GDP": "Porcentaje del PIB",
    "Billions of euros and percent of GDP": "Miles de millones de euros y porcentaje del PIB",
    "End of year; billions of euros": "Fin de año; miles de millones de euros",
    "End of year; percent of GDP": "Fin de año; porcentaje del PIB",
    "End of year; billions of euros and percent of GDP": "Fin de año; miles de millones de euros y porcentaje del PIB",
    "End of year, unless otherwise indicated": "Fin de año, salvo indicación en contrario",
    "Percent, unless otherwise indicated; end of year": "Porcentaje, salvo indicación en contrario; fin de año",
})

# ---------------------------------------------------------------- Table 3: Selected Financial Soundness Indicators
PAIRS.update({
    "Selected Financial Soundness Indicators": "Indicadores de solidez financiera seleccionados",
    "Deposit takers: consolidated basis": "Sociedades captadoras de depósitos: base consolidada",
    "Regulatory capital to risk-weighted assets": "Capital regulador / activos ponderados por riesgo",
    "Regulatory Tier 1 capital to risk-weighted assets": "Capital regulador de nivel 1 / activos ponderados por riesgo",
    "Tier 1 capital to total assets 1/": "Capital de nivel 1 / activos totales 1/",
    "Nonperforming loans (billions of euros)": "Préstamos en mora (miles de millones de euros)",
    "Nonperforming loans to total gross loans": "Préstamos en mora / total de préstamos brutos",
    "Specific provisions to nonperforming loans": "Provisiones específicas / préstamos en mora",
    "Return on assets 2/": "Rentabilidad de los activos (ROA) 2/",
    "Return on equity 2/": "Rentabilidad del patrimonio (ROE) 2/",
    "Deposit takers: domestic operations": "Sociedades captadoras de depósitos: negocios en España",
    "Nonperforming loans to total loans": "Préstamos en mora / total de préstamos",
    "Specific provisions to nonperforming loans 3/": "Provisiones específicas / préstamos en mora 3/",
    "Exposure to businesses: construction and real estate (billions of euros)":
        "Exposición a empresas: construcción y actividades inmobiliarias (miles de millones de euros)",
    "o/w nonperforming (percent)": "de la cual: en mora (porcentaje)",
    "Exposure to businesses: other (billions of euros)": "Exposición a empresas: resto (miles de millones de euros)",
    "Exposure to households: home purchase (billions of euros)":
        "Exposición a hogares: adquisición de vivienda (miles de millones de euros)",
    "Exposure to households: other (billions of euros) 4/":
        "Exposición a hogares: resto (miles de millones de euros) 4/",
    "Loans to deposits 5/": "Préstamos / depósitos 5/",
    "Corporate sector": "Sector empresarial",
    "Debt (percent of GDP)": "Deuda (porcentaje del PIB)",
    "Debt to total assets 6/": "Deuda / activos totales 6/",
    "Household sector": "Sector de los hogares",
    "Debt (percent of GDP) 7/": "Deuda (porcentaje del PIB) 7/",
    "Real estate market": "Mercado inmobiliario",
    "House prices (percentage change, end of period)": "Precios de la vivienda (variación porcentual, fin de período)",
    "Home sales (2007 = 100)": "Compraventa de viviendas (2007 = 100)",
    "1/ Tier 1 capital over the Basel III leverage exposure measure where reported (from 2022), otherwise over total assets.":
        "1/ Capital de nivel 1 sobre la medida de la exposición de la ratio de apalancamiento de Basilea III cuando "
        "se declara (desde 2022) y, si no, sobre los activos totales.",
    "2/ As in the IMF's database: net income before tax over average total assets, and net income after tax over average capital and reserves.":
        "2/ Como en la base de datos del FMI: resultado neto antes de impuestos sobre los activos totales medios, y "
        "resultado neto después de impuestos sobre el capital y las reservas medios.",
    "3/ Impairment allowances over nonperforming credit to other resident sectors (credit institutions and specialised lenders).":
        "3/ Correcciones de valor por deterioro sobre el crédito en mora a otros sectores residentes (entidades de "
        "crédito y establecimientos financieros de crédito).",
    "4/ Credit to households other than for house purchase, to nonprofit institutions, and unclassified credit.":
        "4/ Crédito a hogares con fines distintos de la adquisición de vivienda, a instituciones sin fines de lucro "
        "y crédito sin clasificar.",
    "5/ Based on loans to and deposits from other resident sectors, as in the IMF's table.":
        "5/ A partir de los préstamos a otros sectores residentes y de los depósitos de estos, como en el cuadro del "
        "FMI.",
    "6/ Debt over the balance sheet total (debt, equity and other liabilities) of nonfinancial corporations.":
        "6/ Deuda sobre el total del balance (deuda, patrimonio neto y otros pasivos) de las sociedades no "
        "financieras.",
    "7/ Total financial liabilities of households (loans, trade credit and other accounts payable), which is what the IMF's figures match; loans alone are about 4 points of GDP lower.":
        "7/ Pasivos financieros totales de los hogares (préstamos, créditos comerciales y otras cuentas por pagar), "
        "que es la magnitud con la que coinciden las cifras del FMI; solo los préstamos quedan unos 4 puntos del PIB "
        "por debajo.",
    "Home sales are INE's count from the property registers; the IMF's index, from another source, runs a little lower.":
        "La compraventa de viviendas es el recuento del INE a partir de los registros de la propiedad; el índice del "
        "FMI, de otra fuente, se sitúa algo por debajo.",
})

# ---------------------------------------------------------------- Table 4: Balance of Payments
PAIRS.update({
    "Balance of Payments": "Balanza de pagos",
    "Trade balance of goods and services": "Balanza de bienes y servicios",
    "Exports of goods and services": "Exportaciones de bienes y servicios",
    "Trade of goods balance": "Balanza de bienes",
    "Imports of goods and services": "Importaciones de bienes y servicios",
    "o.w. Tourism (travel)": "de los cuales: turismo (viajes)",
    "Tourism receipts": "Ingresos por turismo",
    "Tourism payments": "Pagos por turismo",
    "Primary income": "Ingreso primario",
    "Secondary income": "Ingreso secundario",
    "General government": "Administraciones públicas",
    "Other sectors": "Otros sectores",
    "Capital account": "Cuenta de capital",
    "Financial account 1/": "Cuenta financiera 1/",
    "Direct investment": "Inversión directa",
    "Spanish investment abroad": "Inversión española en el exterior",
    "Foreign investment in Spain": "Inversión extranjera en España",
    "Portfolio investment": "Inversión de cartera",
    "Financial derivatives": "Derivados financieros",
    "Other investment": "Otra inversión",
    "o.w. Banco de España": "de la cual: Banco de España",
    "Change in reserve assets": "Variación de los activos de reserva",
    "Errors and omissions": "Errores y omisiones",
    "Net international investment position": "Posición de inversión internacional neta",
    "Valuation changes 2/": "Variaciones de valoración 2/",
    "Eurostat, sixth edition of the IMF's Balance of Payments Manual (BPM6). The World Economic Outlook projects only the current account, as a share of GDP; the euro figure applies it to the WEO's nominal GDP.":
        "Eurostat, sexta edición del Manual de Balanza de Pagos del FMI (MBP6). El World Economic Outlook solo "
        "proyecta la cuenta corriente, en porcentaje del PIB; la cifra en euros aplica ese "
        "porcentaje al PIB nominal del WEO.",
    "1/ Net lending to the rest of the world: net acquisition of foreign assets less net incurrence of liabilities.":
        "1/ Préstamo neto al resto del mundo: adquisición neta de activos exteriores menos pasivos netos incurridos.",
    "2/ The change in the net international investment position not explained by the financial account: changes in prices and exchange rates, and other changes.":
        "2/ La variación de la posición de inversión internacional neta que no explica la cuenta financiera: "
        "variaciones de precios y de tipos de cambio, y otras variaciones.",
})

# ---------------------------------------------------------------- Table 5: External Debt
PAIRS.update({
    "External Debt": "Deuda externa",
    "Gross external debt 1/": "Deuda externa bruta 1/",
    "Bank of Spain": "Banco de España",
    "Other monetary financial institutions": "Otras instituciones financieras monetarias",
    "Other resident sectors": "Otros sectores residentes",
    "Debt securities": "Títulos de deuda",
    "Loans, trade credits and other liabilities": "Préstamos, créditos comerciales y otros pasivos",
    "Deposits": "Depósitos",
    "Direct investment debt liabilities": "Pasivos de deuda por inversión directa",
    "Net external debt 2/": "Deuda externa neta 2/",
    "1/ Liabilities to non-residents in debt instruments at the end of the year, from Eurostat's international investment position (BPM6). The sectors, with direct investment debt, add up to the total; so do the instruments. The IMF's table uses the World Bank's Quarterly External Debt Statistics, which differ slightly.":
        "1/ Pasivos frente a no residentes en instrumentos de deuda a fin de año, de la posición de inversión "
        "internacional de Eurostat (MBP6). Los sectores, junto con la deuda por inversión directa, suman el total; "
        "también los instrumentos. El cuadro del FMI usa las Estadísticas Trimestrales de la Deuda Externa del Banco "
        "Mundial, que difieren ligeramente.",
    "2/ Gross external debt less external assets in debt instruments (Eurostat).":
        "2/ Deuda externa bruta menos activos exteriores en instrumentos de deuda (Eurostat).",
})

# ---------------------------------------------------------------- the monetary and credit table, every view
PAIRS.update({
    "Monetary and Credit Indicators": "Indicadores monetarios y crediticios",
    "Banco de España (billions of euros)": "Banco de España (miles de millones de euros)",
    "Banco de España (percent of GDP)": "Banco de España (porcentaje del PIB)",
    "Total assets": "Activo total",
    "Securities held for monetary policy purposes": "Valores mantenidos con fines de política monetaria",
    "Lending to credit institutions (monetary policy operations)":
        "Crédito a entidades de crédito (operaciones de política monetaria)",
    "Banknotes in circulation": "Billetes en circulación",
    "Credit institutions' reserves and deposits": "Reservas y depósitos de las entidades de crédito",
    "TARGET balance 1/": "Saldo TARGET 1/",
    "Credit and deposits (annual percent change, December)":
        "Crédito y depósitos (variación porcentual anual, diciembre)",
    "Credit to the private sector 2/": "Crédito al sector privado 2/",
    "Loans to households": "Préstamos a hogares",
    "o.w. for house purchase": "de los cuales: para adquisición de vivienda",
    "Loans to non-financial corporations": "Préstamos a sociedades no financieras",
    "Deposits of other resident sectors 3/": "Depósitos de otros sectores residentes 3/",
    "Interest rates (percent)": "Tipos de interés (porcentaje)",
    "ECB deposit facility rate (end of year)": "Tipo de la facilidad de depósito del BCE (fin de año)",
    "3-month Euribor (end of year)": "Euríbor a 3 meses (fin de año)",
    "10-year government bond yield (end of year)": "Rentabilidad de la deuda pública a 10 años (fin de año)",
    "New loans to households for house purchase (December)":
        "Nuevos préstamos a hogares para adquisición de vivienda (diciembre)",
    "New loans to non-financial corporations (December)": "Nuevos préstamos a sociedades no financieras (diciembre)",
    "New household time deposits (December)": "Nuevos depósitos a plazo de los hogares (diciembre)",
    "1/ The Banco de España's net position in the Eurosystem's payment system; negative is a liability.":
        "1/ Posición neta del Banco de España en el sistema de pagos del Eurosistema; un valor negativo es un "
        "pasivo.",
    "2/ Bank loans to households, firms and non-bank financial corporations, adjusted for loan sales and securitisation.":
        "2/ Préstamos bancarios a hogares, empresas y sociedades financieras no bancarias, ajustados de ventas y "
        "titulizaciones de préstamos.",
    "3/ Deposits held at credit institutions and specialised lenders, unadjusted.":
        "3/ Depósitos en entidades de crédito y establecimientos financieros de crédito, sin ajustar.",
})
