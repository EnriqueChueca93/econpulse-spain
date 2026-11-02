"""Spanish for the IMF-style tables, part A (Batch 33c-3): Table 1 (Main Economic Indicators), Tables 2a-2b
(General Government Operations), DSA 1-2 (debt sustainability), and the captions, notes, units, sources, facts
and charts all the tables share (econpulse/sectortables.py). Tables 3-5 and the monetary table are in
catalogue_imf_b.py. Read by scripts/write_catalogue.py; the keys are the English exactly as the code writes it.

Terms follow the IMF's Spanish (Article IV staff reports, GFSM 2014 / MEFP 2014, BPM6 / MBP6), in the Spanish of
Spain: Administraciones públicas (the IMF's gobierno general), ingresos, gasto, préstamo neto / endeudamiento neto, brecha del producto, flujos
generadores de deuda, ajuste stock-flujo. World Economic Outlook and Debt Sustainability Monitor keep their names.
"""

PAIRS: dict[str, str] = {}

# ---------------------------------------------------------------- shared by every table: titles, captions, notes, units and the page's facts
PAIRS.update({
    "Table {n}": "Cuadro {n}",
    "proj.": "proy.",
    "Annual": "Anual",
    "Monthly": "Mensual",
    "{unit} · actual data to {year}": "{unit} · datos observados hasta {year}",
    "{unit} · quarterly data to {period}": "{unit} · datos trimestrales hasta {period}",
    "{unit} · monthly data to {period}": "{unit} · datos mensuales hasta {period}",
    ", {projections} from {year}": ", {projections} a partir de {year}",
    "IMF projections (World Economic Outlook, {edition})": "proyecciones del FMI (World Economic Outlook, {edition})",
    "European Commission projections": "proyecciones de la Comisión Europea",
    "IMF's 2026 Article IV staff report for Spain":
        "informe del personal técnico del FMI sobre la consulta del Artículo IV de 2026 con España",
    "After the {report}.": "Con el formato del {report}.",
    "{na} not available: the IMF's database does not publish the line. After the {report}; past years differ where the data have been revised since.":
        "{na} no disponible: la base de datos del FMI no publica la línea. Con el formato del {report}; los años "
        "anteriores difieren cuando los datos se han revisado desde entonces.",
    "Lines published only once a year are left out; {na} not yet published.":
        "Se omiten las líneas que solo se publican una vez al año; {na} aún no publicado.",
    "Source: {edition}, Spain's country fiche.": "Fuente: {edition}, ficha de España.",
    "Percent change unless otherwise indicated": "Variación porcentual, salvo indicación en contrario",
    "Percent change on a year earlier unless otherwise indicated":
        "Variación porcentual interanual, salvo indicación en contrario",
    "Percent of GDP unless otherwise indicated": "Porcentaje del PIB, salvo indicación en contrario",
    "Percent of GDP, unless otherwise indicated": "Porcentaje del PIB, salvo indicación en contrario",
    "Percent of the quarter's GDP": "Porcentaje del PIB del trimestre",
    "Percent of the quarter's GDP, unless otherwise indicated":
        "Porcentaje del PIB del trimestre, salvo indicación en contrario",
    "Billions of euros unless otherwise indicated": "Miles de millones de euros, salvo indicación en contrario",
    "Billions of euros, unless otherwise indicated": "Miles de millones de euros, salvo indicación en contrario",
    "Percent, unless otherwise indicated; end of quarter":
        "Porcentaje, salvo indicación en contrario; fin de trimestre",
    "End of period, unless otherwise indicated": "Fin de periodo, salvo indicación en contrario",
    "End of quarter; billions of euros": "Fin de trimestre; miles de millones de euros",
    "End of quarter; percent of GDP over the past four quarters":
        "Fin de trimestre; porcentaje del PIB de los últimos cuatro trimestres",
    "Actual data": "Datos observados",
    "to {year}": "hasta {year}",
    "INE, Eurostat, the ECB": "INE, Eurostat, BCE",
    "Projections": "Proyecciones",
    "World Economic Outlook database": "Base de datos del World Economic Outlook",
    "Every table, from 2015": "Todos los cuadros, desde 2015",
    "Excel workbook": "Libro de Excel (en inglés)",
    "The IMF's main table for Spain: demand, saving and investment, prices, the labour market, and a summary of the external and public accounts.":
        "El cuadro principal del FMI para España: demanda, ahorro e inversión, precios, mercado laboral y un resumen "
        "de las cuentas externas y públicas.",
    "Revenue, spending and the balances of the general government, from Eurostat's accounts.":
        "Ingresos, gastos y saldos de las Administraciones públicas, según las cuentas de Eurostat.",
    "What changes the debt, in the IMF's layout, and how it fares under the European Commission's stress tests. In percent of GDP, DSA 1 splits the change in the debt ratio, growth and inflation included; in euros, the change in the amount owed, which only the deficit, interest and other flows move.":
        "Qué hace variar la deuda, con el formato del FMI, y cómo se comporta en las pruebas de tensión de la Comisión "
        "Europea. En porcentaje del PIB, el DSA 1 desglosa la variación de la ratio de deuda, incluidos el crecimiento "
        "y la inflación; en euros, la variación del importe adeudado, que solo mueven el déficit, los intereses y "
        "otros flujos.",
    "Debt in {year}, IMF": "Deuda en {year}, FMI",
    "World Economic Outlook, {edition}": "World Economic Outlook, {edition}",
    "Debt in {year}, European Commission": "Deuda en {year}, Comisión Europea",
    "No-policy-change baseline": "Escenario base sin cambios de política",
    "Sustainability gap S1, Commission": "Brecha de sostenibilidad S1, Comisión",
    "Adjustment from 2027 that brings debt to 60% of GDP by 2070":
        "Ajuste desde 2027 que lleva la deuda al 60% del PIB en 2070",
})

# ---------------------------------------------------------------- Table 1. Main Economic Indicators (real sector), annual and quarterly
PAIRS.update({
    "Main Economic Indicators": "Principales indicadores económicos",
    "Demand and supply in constant prices": "Demanda y oferta a precios constantes",
    "Gross domestic product": "Producto interior bruto",
    "Private consumption": "Consumo privado",
    "Public consumption": "Consumo público",
    "Gross fixed investment": "Inversión fija bruta",
    "Total domestic demand": "Demanda interna total",
    "Net exports (contribution to growth)": "Exportaciones netas (contribución al crecimiento)",
    "Real GDP per capita": "PIB real per cápita",
    "Savings-investment balance (percent of GDP)": "Saldo ahorro-inversión (porcentaje del PIB)",
    "Savings-investment balance (billions of euros)": "Saldo ahorro-inversión (miles de millones de euros)",
    "Gross domestic investment": "Inversión interna bruta",
    "Private": "Sector privado",
    "Public": "Sector público",
    "National savings": "Ahorro nacional",
    "Foreign savings": "Ahorro externo",
    "Households": "Hogares",
    "Household saving rate (percent of gross disposable income)":
        "Tasa de ahorro de los hogares (porcentaje del ingreso disponible bruto)",
    "Potential output 1/": "Producto potencial 1/",
    "Potential output (percent change) 1/": "Producto potencial (variación porcentual) 1/",
    "Output gap (percent of potential output) 1/": "Brecha del producto (porcentaje del producto potencial) 1/",
    "Headline inflation (average) 1/": "Inflación general (promedio) 1/",
    "Headline inflation (average) 2/": "Inflación general (promedio) 2/",
    "Headline inflation (end of period) 1/": "Inflación general (fin de periodo) 1/",
    "Headline inflation (end of period) 2/": "Inflación general (fin de periodo) 2/",
    "Core inflation (average) 1/": "Inflación subyacente (promedio) 1/",
    "Core inflation (average) 2/": "Inflación subyacente (promedio) 2/",
    "Core inflation (end of period) 1/": "Inflación subyacente (fin de periodo) 1/",
    "Core inflation (end of period) 2/": "Inflación subyacente (fin de periodo) 2/",
    "Employment and wages": "Empleo y salarios",
    "Unemployment rate (percent of total labor force)": "Tasa de desempleo (porcentaje de la población activa total)",
    "Labor productivity 2/": "Productividad laboral 2/",
    "Labor productivity 3/": "Productividad laboral 3/",
    "Labor costs 3/": "Costes laborales 3/",
    "Labor costs 4/": "Costes laborales 4/",
    "Employment": "Empleo",
    "Labor force": "Población activa",
    "Balance of payments (percent of GDP)": "Balanza de pagos (porcentaje del PIB)",
    "Balance of payments (billions of euros)": "Balanza de pagos (miles de millones de euros)",
    "Trade balance (goods and services)": "Balanza comercial (bienes y servicios)",
    "Current account balance 4/": "Saldo por cuenta corriente 4/",
    "Public finance (percent of GDP)": "Finanzas públicas (porcentaje del PIB)",
    "Public finance (billions of euros)": "Finanzas públicas (miles de millones de euros)",
    "General government balance": "Saldo de las Administraciones públicas",
    "General government balance 4/": "Saldo de las Administraciones públicas 4/",
    "Primary balance 5/": "Saldo primario 5/",
    "Structural balance 1/": "Saldo estructural 1/",
    "Structural balance (percent of potential GDP) 1/": "Saldo estructural (porcentaje del PIB potencial) 1/",
    "Primary structural balance 1/": "Saldo primario estructural 1/",
    "Primary structural balance (percent of GDP) 1/": "Saldo primario estructural (porcentaje del PIB) 1/",
    "General government debt": "Deuda de las Administraciones públicas",
    "General government debt 5/": "Deuda de las Administraciones públicas 5/",
    "Memo items": "Partidas informativas",
    "Credit to the private sector 6/": "Crédito al sector privado 6/",
    "Nominal GDP (billions of euros)": "PIB nominal (miles de millones de euros)",
    "Nominal GDP (billions of euros, the quarter)": "PIB nominal (miles de millones de euros, del trimestre)",
    "Real GDP (billions of 2020 euros)": "PIB real (miles de millones de euros de 2020)",
    "1/ IMF staff estimates in every year (World Economic Outlook). Potential output is real GDP over one plus the output gap; the primary structural balance adds interest paid (Eurostat) to the structural balance.":
        "1/ Estimaciones del personal técnico del FMI en todos los años (World Economic Outlook). El producto "
        "potencial es el PIB real dividido entre uno más la brecha del producto; el saldo primario estructural suma "
        "los intereses pagados (Eurostat) al saldo estructural.",
    "2/ Harmonised Index of Consumer Prices. Core excludes energy and unprocessed food, as in the IMF's table.":
        "2/ Índice armonizado de precios de consumo (IAPC). La inflación subyacente excluye la energía y los alimentos "
        "no elaborados, como en el cuadro del FMI.",
    "3/ Output per full-time equivalent job.": "3/ Producto por puesto de trabajo equivalente a tiempo completo.",
    "4/ Total labour cost per worker, all sectors (INE's quarterly labour cost survey). The IMF's line covers the private sector only.":
        "4/ Coste laboral total por trabajador, todos los sectores (encuesta trimestral de coste laboral del INE). La "
        "línea del FMI abarca solo el sector privado.",
    "5/ Following the World Economic Outlook, the primary balance excludes interest earnings as well as interest payments.":
        "5/ Como en el World Economic Outlook, el saldo primario excluye los ingresos por intereses además de los "
        "pagos de intereses.",
    "6/ Annual growth of bank loans to the private sector (households, firms and non-bank financial corporations), adjusted for loan sales and securitisation.":
        "6/ Crecimiento interanual de los préstamos bancarios al sector privado (hogares, empresas y sociedades "
        "financieras no bancarias), corregido de ventas y titulizaciones de préstamos.",
    "Growth rates compare each quarter with the same quarter a year earlier.":
        "Las tasas de crecimiento comparan cada trimestre con el mismo trimestre del año anterior.",
    "1/ Harmonised Index of Consumer Prices; core excludes energy and unprocessed food. Average: the quarter's mean; end of period: its last month.":
        "1/ Índice armonizado de precios de consumo (IAPC); la inflación subyacente excluye la energía y los alimentos "
        "no elaborados. Promedio: media del trimestre; fin de periodo: su último mes.",
    "2/ Output per full-time equivalent job.": "2/ Producto por puesto de trabajo equivalente a tiempo completo.",
    "3/ Total labour cost per worker, all sectors (INE's quarterly labour cost survey).":
        "3/ Coste laboral total por trabajador, todos los sectores (encuesta trimestral de coste laboral del INE).",
    "4/ The quarter's flow in euros (its share of the quarter's GDP times that GDP), not seasonally adjusted.":
        "4/ Flujo del trimestre en euros (su porcentaje del PIB del trimestre multiplicado por ese PIB), sin "
        "desestacionalizar.",
    "4/ The quarter's flow, as a share of the quarter's GDP, not seasonally adjusted.":
        "4/ Flujo del trimestre, en porcentaje del PIB del trimestre, sin desestacionalizar.",
    "5/ End of quarter, in euros.": "5/ Fin de trimestre, en euros.",
    "5/ End of quarter, as a share of GDP over the past four quarters.":
        "5/ Fin de trimestre, en porcentaje del PIB de los últimos cuatro trimestres.",
    "6/ Annual growth of bank loans to the private sector at the end of the quarter, adjusted for loan sales and securitisation.":
        "6/ Crecimiento interanual de los préstamos bancarios al sector privado a fin de trimestre, corregido de "
        "ventas y titulizaciones de préstamos.",
})

# ---------------------------------------------------------------- Tables 2a-2b. General Government Operations, annual and quarterly (GFSM 2014 terms)
PAIRS.update({
    "General Government Operations": "Operaciones de las Administraciones públicas",
    "Taxes": "Impuestos",
    "Indirect taxes": "Impuestos indirectos",
    "o.w. VAT": "de los cuales: IVA",
    "o.w. Excise": "de los cuales: impuestos especiales",
    "Direct taxes": "Impuestos directos",
    "o.w. Private households 2/": "de los cuales: hogares 2/",
    "o.w. Corporate 2/": "de los cuales: sociedades 2/",
    "Capital tax": "Impuestos sobre el capital",
    "Social contributions": "Contribuciones sociales",
    "Other revenue": "Otros ingresos",
    "Expenditure": "Gasto total",
    "Expense": "Gasto",
    "Compensation of employees": "Remuneración a los empleados",
    "Use of goods and services": "Uso de bienes y servicios",
    "Capital 2/": "Gasto de capital 2/",
    "Capital 3/": "Gasto de capital 3/",
    "o.w. Gross capital formation": "del cual: formación bruta de capital",
    "o.w. Capital transfers and investment aid": "del cual: transferencias de capital y ayudas a la inversión",
    "Social benefits": "Prestaciones sociales",
    "Other expense": "Otros gastos",
    "Subsidies": "Subsidios",
    "Other": "Otros",
    "Net acquisition of nonfinancial assets 2/": "Adquisición neta de activos no financieros 2/",
    "Net acquisition of nonfinancial assets 3/": "Adquisición neta de activos no financieros 3/",
    "Gross operating balance": "Resultado operativo bruto",
    "Net lending / borrowing": "Préstamo neto / endeudamiento neto",
    "Memorandum items": "Partidas informativas",
    "Primary balance 3/": "Saldo primario 3/",
    "Primary balance 4/": "Saldo primario 4/",
    "Primary structural balance 5/": "Saldo primario estructural 5/",
    "Structural balance 5/": "Saldo estructural 5/",
    "General government gross debt (Maastricht)": "Deuda bruta de las Administraciones públicas (Maastricht)",
    "General government gross debt (Maastricht) 4/": "Deuda bruta de las Administraciones públicas (Maastricht) 4/",
    "Net debt 5/": "Deuda neta 5/",
    "Central government net lending": "Préstamo neto del gobierno central",
    "Output gap 5/": "Brecha del producto 5/",
    "1/ General government, ESA 2010 accrual accounts (Eurostat), with the IMF's grouping. The World Economic Outlook projects only revenue, expenditure, the balances and debt.":
        "1/ Administraciones públicas, cuentas en base devengado del SEC 2010 (Eurostat), con la agrupación del FMI. El World "
        "Economic Outlook solo proyecta los ingresos, el gasto total, los saldos y la deuda.",
    "2/ Eurostat's detailed tax receipts. The IMF's two sub-lines come from another source: they add up to more than its direct taxes.":
        "2/ Recaudación tributaria detallada de Eurostat. Las dos sublíneas del FMI proceden de otra fuente: suman más "
        "que sus impuestos directos.",
    "3/ As in the IMF's table, capital spending is gross capital formation plus capital transfers, and net acquisition of nonfinancial assets covers nonproduced assets (land, licences) only.":
        "3/ Como en el cuadro del FMI, el gasto de capital es la formación bruta de capital más las transferencias de "
        "capital, y la adquisición neta de activos no financieros solo abarca los activos no producidos (terrenos, "
        "licencias).",
    "4/ Following the World Economic Outlook, the primary balance excludes interest earnings as well as interest payments.":
        "4/ Como en el World Economic Outlook, el saldo primario excluye los ingresos por intereses además de los "
        "pagos de intereses.",
    "5/ IMF staff estimates in every year (World Economic Outlook). The primary structural balance adds interest paid (Eurostat) to the structural balance.":
        "5/ Estimaciones del personal técnico del FMI en todos los años (World Economic Outlook). El saldo primario "
        "estructural suma los intereses pagados (Eurostat) al saldo estructural.",
    "1/ General government, quarterly accrual accounts (Eurostat), each quarter's flows, not seasonally adjusted. Excise and the split of income taxes are published only once a year.":
        "1/ Administraciones públicas, cuentas trimestrales en base devengado (Eurostat), flujos de cada trimestre, sin "
        "desestacionalizar. Los impuestos especiales y el desglose de los impuestos sobre la renta solo se publican "
        "una vez al año.",
    "1/ General government, quarterly accrual accounts (Eurostat), each quarter's flows, not seasonally adjusted, as a share of that quarter's GDP. Excise and the split of income taxes are published only once a year.":
        "1/ Administraciones públicas, cuentas trimestrales en base devengado (Eurostat), flujos de cada trimestre, sin "
        "desestacionalizar, en porcentaje del PIB de ese trimestre. Los impuestos especiales y el desglose de los "
        "impuestos sobre la renta solo se publican una vez al año.",
    "2/ As in the IMF's table, capital spending is gross capital formation plus capital transfers, and net acquisition of nonfinancial assets covers nonproduced assets only.":
        "2/ Como en el cuadro del FMI, el gasto de capital es la formación bruta de capital más las transferencias de "
        "capital, y la adquisición neta de activos no financieros solo abarca los activos no producidos.",
    "3/ Excludes interest earnings as well as interest payments, as in the World Economic Outlook.":
        "3/ Excluye los ingresos por intereses además de los pagos de intereses, como en el World Economic Outlook.",
    "4/ End of quarter.": "4/ Fin de trimestre.",
    "4/ End of quarter; as a share of GDP over the past four quarters.":
        "4/ Fin de trimestre; en porcentaje del PIB de los últimos cuatro trimestres.",
})

# ---------------------------------------------------------------- DSA 1. Public Debt Dynamics: Baseline Scenario, in % of GDP and in euros
PAIRS.update({
    "DSA 1": "DSA 1",
    "Public Debt Dynamics: Baseline Scenario": "Dinámica de la deuda pública: escenario base",
    "Public debt": "Deuda pública",
    "Change in public debt": "Variación de la deuda pública",
    "Contribution of identified flows 1/": "Contribución de los flujos generadores de deuda identificados 1/",
    "Primary deficit": "Déficit primario",
    "Noninterest revenues": "Ingresos excluidos los intereses",
    "Noninterest expenditures": "Gasto excluidos los intereses",
    "Automatic debt dynamics": "Dinámica automática de la deuda",
    "Real interest rate": "Tipo de interés real",
    "Real growth rate": "Tasa de crecimiento real",
    "Other identified flows: (minus) interest revenues 2/":
        "Otros flujos identificados: (menos) ingresos por intereses 2/",
    "Contribution of residual 3/": "Contribución del residuo 3/",
    "Real GDP growth (percent)": "Crecimiento del PIB real (porcentaje)",
    "Inflation (GDP deflator; percent)": "Inflación (deflactor del PIB; porcentaje)",
    "Nominal GDP growth (percent)": "Crecimiento del PIB nominal (porcentaje)",
    "Effective interest rate (percent) 1/": "Tipo de interés efectivo (porcentaje) 1/",
    "Effective interest rate (percent) 4/": "Tipo de interés efectivo (porcentaje) 4/",
    "Interest payments 1/": "Pagos de intereses 1/",
    "(minus) Interest revenues 1/": "(menos) Ingresos por intereses 1/",
    "Other flows (stock-flow adjustment) 2/": "Otros flujos (ajuste stock-flujo) 2/",
    "1/ Primary deficit, automatic debt dynamics and other identified flows. Automatic debt dynamics are (r - g)/(1 + g) times the previous year's debt ratio, split into the real effective interest rate r and real GDP growth g. Spain's debt is in euros, so exchange rates play no part.":
        "1/ Déficit primario, dinámica automática de la deuda y otros flujos identificados. La dinámica automática de "
        "la deuda es (r - g)/(1 + g) por la ratio de deuda del año anterior, desglosada en el tipo de interés real "
        "efectivo r y el crecimiento del PIB real g. La deuda de España está en euros, por lo que los tipos de cambio "
        "no intervienen.",
    "2/ The primary balance excludes interest earnings, as in the World Economic Outlook, so they count as another flow.":
        "2/ El saldo primario excluye los ingresos por intereses, como en el World Economic Outlook, por lo que estos "
        "se cuentan como otro flujo.",
    "3/ Includes stock-flow adjustments (changes in government deposits and other financial assets), which the IMF shows separately as other transactions.":
        "3/ Incluye los ajustes stock-flujo (variaciones de los depósitos del gobierno y de otros activos "
        "financieros), que el FMI presenta por separado como otras transacciones.",
    "4/ Interest paid over the previous year's debt. The World Economic Outlook publishes interest only net of interest earnings, so in projection years the rate and the real interest rate effect are net, and interest earnings are not shown separately.":
        "4/ Intereses pagados sobre la deuda del año anterior. El World Economic Outlook solo publica los intereses "
        "netos de los ingresos por intereses, por lo que en los años de proyección el tipo y el efecto del tipo de "
        "interés real son netos, y los ingresos por intereses no se muestran por separado.",
    "In euros the debt changes only through the deficit and other flows; growth and inflation lower the debt ratio, not the amount owed, so their effects appear only in the percent-of-GDP version.":
        "En euros, la deuda solo varía por el déficit y otros flujos; el crecimiento y la inflación reducen la ratio "
        "de deuda, no el importe adeudado, por lo que sus efectos solo aparecen en la versión en porcentaje del PIB.",
    "1/ Interest paid and received. The World Economic Outlook publishes interest only net of interest earnings, so projection years show net interest and no separate interest revenues.":
        "1/ Intereses pagados y cobrados. El World Economic Outlook solo publica los intereses netos de los ingresos "
        "por intereses, por lo que los años de proyección muestran los intereses netos y no los ingresos por intereses "
        "por separado.",
    "2/ The change in debt the deficit does not explain: mainly changes in government deposits and other financial assets.":
        "2/ Variación de la deuda que el déficit no explica: sobre todo, variaciones de los depósitos del gobierno y "
        "de otros activos financieros.",
})

# ---------------------------------------------------------------- DSA 2. Public Debt: European Commission Baseline and Stress Tests, in % of GDP and in euros
PAIRS.update({
    "DSA 2": "DSA 2",
    "Public Debt: European Commission Baseline and Stress Tests":
        "Deuda pública: escenario base y pruebas de tensión de la Comisión Europea",
    "Gross public debt": "Deuda pública bruta",
    "Gross public debt (billions of euros) 1/": "Deuda pública bruta (miles de millones de euros) 1/",
    "Baseline (no policy change)": "Escenario base (sin cambios de política)",
    "Lower structural primary balance": "Menor saldo primario estructural",
    "Adverse interest-growth differential": "Diferencial tipo de interés-crecimiento adverso",
    "Historical structural primary balance": "Saldo primario estructural histórico",
    "Stochastic projections around the baseline 1/": "Proyecciones estocásticas en torno al escenario base 1/",
    "Stochastic projections around the baseline (billions of euros) 1/ 2/":
        "Proyecciones estocásticas en torno al escenario base (miles de millones de euros) 1/ 2/",
    "80th percentile": "Percentil 80",
    "20th percentile": "Percentil 20",
    "Baseline (billions of euros)": "Escenario base (miles de millones de euros)",
    "Primary balance": "Saldo primario",
    "Structural primary balance": "Saldo primario estructural",
    "Interest expenditure": "Gasto en intereses",
    "Gross financing needs": "Necesidades brutas de financiación",
    "1/ The range of debt paths the Commission simulates from past shocks to growth, interest rates and the primary balance: four in five paths lie between the 10th and 90th percentiles.":
        "1/ Abanico de trayectorias de la deuda que la Comisión simula a partir de perturbaciones pasadas del "
        "crecimiento, los tipos de interés y el saldo primario: cuatro de cada cinco trayectorias se sitúan entre los "
        "percentiles 10 y 90.",
    "2/ The range of debt paths the Commission simulates from past shocks to growth, interest rates and the primary balance: four in five paths lie between the 10th and 90th percentiles.":
        "2/ Abanico de trayectorias de la deuda que la Comisión simula a partir de perturbaciones pasadas del "
        "crecimiento, los tipos de interés y el saldo primario: cuatro de cada cinco trayectorias se sitúan entre los "
        "percentiles 10 y 90.",
    "The baseline assumes no change in policy after the Commission's forecast years: the structural primary balance then moves only with the cost of ageing.":
        "El escenario base supone que no hay cambios de política después de los años de previsión de la Comisión: a "
        "partir de entonces, el saldo primario estructural solo varía con el coste del envejecimiento.",
    "The baseline assumes no change in policy after the Commission's forecast years: the structural primary balance then moves only with the cost of ageing. The stress tests are the Commission's: a lower structural primary balance, a higher interest-growth differential, a temporary rise in market interest rates (financial stress) and a return of the structural primary balance to its historical average.":
        "El escenario base supone que no hay cambios de política después de los años de previsión de la Comisión: a "
        "partir de entonces, el saldo primario estructural solo varía con el coste del envejecimiento. Las pruebas de "
        "tensión son las de la Comisión: un menor saldo primario estructural, un diferencial tipo de "
        "interés-crecimiento más elevado, una subida temporal de los tipos de interés de mercado (tensión financiera) "
        "y la vuelta del saldo primario estructural a su media histórica.",
    "1/ The Commission's debt ratios times its baseline nominal GDP (Eurostat's GDP in 2024, grown at the baseline's nominal growth rate). The stress tests and percentiles are shown at baseline GDP, as a guide to scale: each scenario also has its own path for GDP, which the Commission does not publish.":
        "1/ Ratios de deuda de la Comisión multiplicadas por el PIB nominal de su escenario base (el PIB de Eurostat "
        "de 2024, aumentado a la tasa de crecimiento nominal del escenario base). Las pruebas de tensión y los "
        "percentiles se muestran con el PIB del escenario base, como orientación sobre la magnitud: cada escenario "
        "tiene además su propia trayectoria del PIB, que la Comisión no publica.",
})

# ---------------------------------------------------------------- the charts beside the tables: titles, subtitles, series and sources
PAIRS.update({
    "% change on the year before; actual to {year}, then the IMF's projection":
        "Variación interanual, %; datos observados hasta {year} y, después, proyección del FMI",
    "IMF projection": "Proyección del FMI",
    "Saving, investment and the current account": "Ahorro, inversión y cuenta corriente",
    "% of GDP; the IMF's projections from the first year after the last actual figures":
        "% del PIB; proyecciones del FMI desde el primer año posterior a los últimos datos observados",
    "Gross investment": "Inversión bruta",
    "Government revenue and expenditure": "Ingresos y gastos de las Administraciones públicas",
    "% of GDP; the IMF's projections after the last actual year":
        "% del PIB; proyecciones del FMI después del último año observado",
    "What changes the debt ratio": "Qué mueve la ratio de deuda",
    "Percentage points of GDP: the parts of DSA 1, actual years then the IMF's projections":
        "Puntos porcentuales del PIB: los componentes del DSA 1, años observados y después proyecciones del FMI",
    "Interest rate less growth": "Tipo de interés menos crecimiento",
    "Other flows and residual": "Otros flujos y residuo",
    "Change in debt": "Variación de la deuda",
    "Bank capital": "Capital bancario",
    "% of risk-weighted assets, consolidated, end of year":
        "% de los activos ponderados por riesgo, en base consolidada, fin de año",
    "Regulatory capital": "Capital regulador",
    "Tier 1 capital": "Capital de nivel 1",
    "Nonperforming loans": "Préstamos en mora",
    "% of loans, end of year": "% de los préstamos, fin de año",
    "Domestic business": "Negocio en España",
    "Consolidated (incl. abroad)": "Consolidado (incl. el extranjero)",
    "The current account and its parts": "La cuenta corriente y sus componentes",
    "Primary and secondary income": "Ingreso primario y secundario",
    "External position and debt": "Posición y deuda externas",
    "% of GDP, end of year": "% del PIB, fin de año",
    "Gross external debt": "Deuda externa bruta",
    "Net external debt": "Deuda externa neta",
    "Net investment position": "Posición de inversión neta",
    "Bank lending": "Crédito bancario",
    "Annual % change in December, adjusted for loan sales; firms are non-financial corporations":
        "Variación interanual en diciembre, %, corregida de ventas de préstamos; las empresas son las sociedades no "
        "financieras",
    "Firms": "Empresas",
    "Private sector": "Sector privado",
    "The Banco de España in the Eurosystem": "El Banco de España en el Eurosistema",
    "€ billion, end of year: securities bought for monetary policy, lending to banks, and its TARGET balance (net position in the Eurosystem's payment system)":
        "Miles de millones de €, fin de año: valores adquiridos con fines de política monetaria, préstamos a los "
        "bancos y su saldo TARGET (posición neta en el sistema de pagos del Eurosistema)",
    "Policy securities": "Valores de política monetaria",
    "Lending to banks": "Préstamos a los bancos",
    "TARGET balance": "Saldo TARGET",
    "Eurostat; IMF World Economic Outlook": "Eurostat; World Economic Outlook del FMI",
    "Eurostat; IMF World Economic Outlook; Macroscope calculation":
        "Eurostat; World Economic Outlook del FMI; cálculo de Macroscope",
    "IMF Financial Soundness Indicators database": "Base de datos de indicadores de solidez financiera del FMI",
    "Banco de España; IMF Financial Soundness Indicators database":
        "Banco de España; base de datos de indicadores de solidez financiera del FMI",
    "Eurostat, BPM6": "Eurostat, MBP6",
    "Eurostat, international investment position": "Eurostat, posición de inversión internacional",
    "European Commission (Debt Sustainability Monitor 2025)": "Comisión Europea (Debt Sustainability Monitor 2025)",
    "European Commission (Debt Sustainability Monitor 2025); IMF World Economic Outlook":
        "Comisión Europea (Debt Sustainability Monitor 2025); World Economic Outlook del FMI",
})

# ---------------------------------------------------------------- lines and notes of Tables 3-5 and the monetary table that are in this part (mostly their quarterly and monthly views)
PAIRS.update({
    "Nonperforming loans (percent of GDP)": "Préstamos en mora (porcentaje del PIB)",
    "Exposure to businesses: construction and real estate (percent of GDP)":
        "Exposición a empresas: construcción y actividades inmobiliarias (porcentaje del PIB)",
    "Exposure to businesses: other (percent of GDP)": "Exposición a empresas: resto (porcentaje del PIB)",
    "Exposure to households: home purchase (percent of GDP)":
        "Exposición a hogares: adquisición de vivienda (porcentaje del PIB)",
    "Exposure to households: other (percent of GDP) 4/": "Exposición a hogares: resto (porcentaje del PIB) 4/",
    "Debt (billions of euros)": "Deuda (miles de millones de euros)",
    "Debt (billions of euros) 7/": "Deuda (miles de millones de euros) 7/",
    "House prices (percentage change on a year earlier)": "Precios de la vivienda (variación porcentual interanual)",
    "Home sales (2007 average = 100) 8/": "Compraventa de viviendas (media de 2007 = 100) 8/",
    "1/ Tier 1 capital over the Basel III leverage exposure measure where reported, otherwise over total assets.":
        "1/ Capital de nivel 1 sobre la medida de la exposición de la ratio de apalancamiento de Basilea III cuando se "
        "declara y, si no, sobre los activos totales.",
    "2/ Annualised: net income before tax for the year to date over average assets, and net income after tax over average capital and reserves (IMF FSI database).":
        "2/ Anualizadas: resultado neto antes de impuestos en lo que va de año sobre los activos medios, y resultado "
        "neto después de impuestos sobre el capital y las reservas medios (base de datos de indicadores de solidez "
        "financiera del FMI).",
    "3/ Impairment allowances over nonperforming credit to other resident sectors.":
        "3/ Correcciones de valor por deterioro sobre el crédito en mora a otros sectores residentes.",
    "5/ Loans to and deposits from other resident sectors.":
        "5/ Préstamos a otros sectores residentes y depósitos de estos.",
    "6/ Debt over the balance sheet total of nonfinancial corporations.":
        "6/ Deuda sobre el total del balance de las sociedades no financieras.",
    "7/ Total financial liabilities of households, in euros.":
        "7/ Pasivos financieros totales de los hogares, en euros.",
    "7/ Total financial liabilities of households, as a share of GDP over the past four quarters.":
        "7/ Pasivos financieros totales de los hogares, en porcentaje del PIB de los últimos cuatro trimestres.",
    "8/ Homes sold in the quarter, against the 2007 quarterly average.":
        "8/ Viviendas vendidas en el trimestre, frente a la media trimestral de 2007.",
    "8/ Homes sold in the quarter, against the 2007 quarterly average. Amounts in euros are shares of GDP over the past four quarters.":
        "8/ Viviendas vendidas en el trimestre, frente a la media trimestral de 2007. Los importes en euros se "
        "muestran en porcentaje del PIB de los últimos cuatro trimestres.",
    "Net international investment position 3/": "Posición de inversión internacional neta 3/",
    "Eurostat, BPM6: each quarter's flows, not seasonally adjusted.":
        "Eurostat, MBP6: flujos de cada trimestre, sin desestacionalizar.",
    "Eurostat, BPM6: each quarter's flows, not seasonally adjusted, as a share of that quarter's GDP.":
        "Eurostat, MBP6: flujos de cada trimestre, sin desestacionalizar, en porcentaje del PIB de ese trimestre.",
    "2/ The change in the net international investment position over the quarter not explained by the financial account: changes in prices and exchange rates, and other changes.":
        "2/ Variación de la posición de inversión internacional neta en el trimestre que no explica la cuenta "
        "financiera: variaciones de precios y tipos de cambio, y otras variaciones.",
    "3/ End of quarter.": "3/ Fin de trimestre.",
    "3/ End of quarter; as a share of GDP over the past four quarters.":
        "3/ Fin de trimestre; en porcentaje del PIB de los últimos cuatro trimestres.",
    "1/ Liabilities to non-residents in debt instruments at the end of the quarter, from Eurostat's international investment position (BPM6). The sectors, with direct investment debt, add up to the total; so do the instruments.":
        "1/ Pasivos frente a no residentes en instrumentos de deuda a fin de trimestre, de la posición de inversión "
        "internacional de Eurostat (MBP6). Los sectores, junto con la deuda por inversión directa, suman el total; "
        "también los instrumentos.",
    "2/ Gross external debt less external assets in debt instruments (Eurostat); in euros, its share of GDP over the past four quarters times that GDP.":
        "2/ Deuda externa bruta menos los activos exteriores en instrumentos de deuda (Eurostat); en euros, su "
        "porcentaje del PIB de los últimos cuatro trimestres multiplicado por ese PIB.",
    "Credit and deposits (percent change on a year earlier)": "Crédito y depósitos (variación porcentual interanual)",
    "ECB deposit facility rate": "Tipo de la facilidad de depósito del BCE",
    "10-year government bond yield": "Rentabilidad de la deuda pública a 10 años",
    "New loans to households for house purchase 4/": "Nuevos préstamos a hogares para adquisición de vivienda 4/",
    "New loans to non-financial corporations 4/": "Nuevos préstamos a sociedades no financieras 4/",
    "New household time deposits 4/": "Nuevos depósitos a plazo de los hogares 4/",
    "1/ The Banco de España's net position in the Eurosystem's payment system; negative is a liability. Shares of GDP use GDP over the past four quarters.":
        "1/ Posición neta del Banco de España en el sistema de pagos del Eurosistema; un valor negativo es un pasivo. "
        "Los porcentajes del PIB usan el PIB de los últimos cuatro trimestres.",
    "4/ New business in the month.": "4/ Operaciones nuevas del mes.",
    "4/ New business in the quarter's last month.": "4/ Operaciones nuevas del último mes del trimestre.",
})
