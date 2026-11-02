"""Spanish for the section pages, part II (Batch 33c): the pages' introductions, Fiscal, Economic activity and
external accounts, and Regions. Read by scripts/write_catalogue.py; the keys are the English exactly as the code
writes it. The Analysis and Trade pages have files of their own (catalogue_analysis.py, catalogue_trade.py).
"""

PAIRS: dict[str, str] = {}

# ---------------------------------------------------------------- the pages' introductions (build.SECTION_PAGES)
PAIRS.update({
    "Government deficit and debt, the IMF-style fiscal tables, and debt sustainability.":
        "El déficit y la deuda de las Administraciones públicas, los cuadros fiscales al estilo del FMI y la "
        "sostenibilidad de la deuda.",
    "Industry, retail, sentiment surveys, tourism, electricity demand, the external accounts and the IMF-style balance of payments and external debt tables; trade in goods and services has a page of its own.":
        "La industria, el comercio minorista, las encuestas de confianza, el turismo, la demanda eléctrica, las cuentas "
        "exteriores y los cuadros de balanza de pagos y deuda externa al estilo del FMI; el comercio de bienes y "
        "servicios tiene su propia página.",
    "House prices, affordability and rents, Spain against its comparators, building and households, sales, mortgages and credit, household wealth, and commercial property.":
        "Los precios de la vivienda, la accesibilidad y los alquileres, España frente a sus comparables, la construcción "
        "y los hogares, las compraventas, las hipotecas y el crédito, la riqueza de los hogares y el sector inmobiliario "
        "comercial.",
    "The Social Security's contributory pensions: how many and how much, by class, scheme and region, what they cost, new and ended pensions, and the maximum and minimum amounts; Spain against its comparators, the ageing population, the 2023 reform and what the official assessments say.":
        "Las pensiones contributivas de la Seguridad Social: cuántas son y de qué cuantía, por clase, régimen y comunidad, "
        "lo que cuestan, las altas y las bajas, y las cuantías máximas y mínimas; España frente a sus comparables, el "
        "envejecimiento de la población, la reforma de 2023 y lo que dicen las evaluaciones oficiales.",
    "Spain next to the euro area and ten comparators: France, Germany, Italy, the Netherlands, Portugal, Poland, the United Kingdom, the United States, Canada and Japan; growth, jobs, prices, public finances and the IMF's outlook.":
        "España junto a la zona del euro y diez comparables: Francia, Alemania, Italia, los Países Bajos, Portugal, "
        "Polonia, el Reino Unido, Estados Unidos, Canadá y Japón; crecimiento, empleo, precios, finanzas públicas y las "
        "previsiones del FMI.",
    "The 17 autonomous communities: unemployment, house prices, inflation and income per head.":
        "Las 17 comunidades autónomas: paro, precios de la vivienda, inflación y renta per cápita.",
    "Macroscope's own readings: the economy against its history, data surprises, a GDP nowcast, what forecasters expect, the 10-year yield split in two, and Taylor rules.":
        "Las lecturas propias de Macroscope: la economía frente a su historia, las sorpresas en los datos, una "
        "estimación en tiempo real del PIB, lo que esperan los analistas, la rentabilidad a 10 años dividida en dos y "
        "las reglas de Taylor.",
})

# ---------------------------------------------------------------- Fiscal
PAIRS.update({
    "€ bn": "mm €",          # a chart's unit
    "€ mn": "mill. €",
    "Budget balance": "Saldo presupuestario",
    "The general government (state, regions, local councils and social security) as reported to the European Commission. EU rules set reference values of a 3% deficit and 60% debt.":
        "Las Administraciones públicas (Estado, comunidades autónomas, corporaciones locales y Seguridad Social), según "
        "lo notificado a la Comisión Europea. Las reglas de la UE fijan valores de referencia de un 3% de déficit y un "
        "60% de deuda.",
    "% of GDP, calendar year": "% del PIB, año natural",
    "% of GDP, calendar years": "% del PIB, años naturales",
    "% of GDP, quarterly": "% del PIB, trimestral",
    "Year before": "Año anterior",
    "Before interest (primary balance)": "Sin intereses (saldo primario)",
    "Interest paid": "Intereses pagados",
    "Debt at year end": "Deuda a final de año",
    "A negative balance is a deficit.": "Un saldo negativo es un déficit.",
    "Latest quarters": "Últimos trimestres",
    "Budget balance, past four quarters": "Saldo presupuestario, últimos cuatro trimestres",
    "The quarterly balance is not seasonally adjusted, so it is averaged over four quarters.":
        "El saldo trimestral no está desestacionalizado, así que se promedia en cuatro trimestres.",
    "EU limit": "Límite de la UE",
    "EU reference": "Referencia de la UE",
    "Government debt": "Deuda pública",
    "Debt": "Deuda",
    "Interest on the debt": "Intereses de la deuda",
    "Interest": "Intereses",
    "Revenue and spending": "Ingresos y gastos",
    "Revenue": "Ingresos",
    "Tables 2a and 2b of the IMF's 2026 Article IV report for Spain: revenue, spending and the balances in euros and in % of GDP, from Eurostat's accounts for the general government. The World Economic Outlook projects only the totals, so the other lines show … in the projection years.":
        "Los cuadros 2a y 2b del informe del Artículo IV de 2026 del FMI sobre España: ingresos, gastos y saldos en euros "
        "y en % del PIB, de las cuentas de las Administraciones públicas de Eurostat. El World Economic Outlook solo "
        "proyecta los totales, así que las demás líneas muestran … en los años de proyección.",
    "What drives the debt ratio, in the IMF's layout (DSA 1: Eurostat for past years, the World Economic Outlook for projections), and how it fares under stress, from the European Commission's Debt Sustainability Monitor (DSA 2), since the IMF does not publish its own stress tests as data. The Fiscal Explorer runs the Commission's baseline to 2070.":
        "Qué mueve la ratio de deuda, con el formato del FMI (DSA 1: Eurostat para los años pasados, el World Economic "
        "Outlook para las proyecciones), y cómo se comporta en escenarios de tensión, del Debt Sustainability Monitor de "
        "la Comisión Europea (DSA 2), ya que el FMI no publica sus propias pruebas de tensión como datos. El Explorador "
        "fiscal proyecta el escenario base de la Comisión hasta 2070.",
    "Public debt: baselines and fan chart": "Deuda pública: escenarios base y gráfico de abanico",
    "% of GDP; the Commission's baseline with the 10th and 90th percentiles of its stochastic projections, and the IMF's projection":
        "% del PIB; el escenario base de la Comisión con los percentiles 10 y 90 de sus proyecciones estocásticas, y la "
        "proyección del FMI",
    "Commission baseline": "Escenario base de la Comisión",
    "10th percentile": "Percentil 10",
    "90th percentile": "Percentil 90",
    "IMF (WEO)": "FMI (WEO)",
    "Public debt under the Commission's stress tests": "La deuda pública en las pruebas de tensión de la Comisión",
    "% of GDP; baseline and three of the Commission's four stress tests (all four are in DSA 2)":
        "% del PIB; escenario base y tres de las cuatro pruebas de tensión de la Comisión (las cuatro están en el DSA 2)",
    "Baseline": "Escenario base",
    "Adverse r − g": "r − g adverso",
    "Lower primary balance": "Menor saldo primario",
})

# ---------------------------------------------------------------- Economic activity and external accounts
PAIRS.update({
    "Industry and retail": "Industria y comercio minorista",
    "Monthly signs of how much the economy is producing and selling. Electricity demand arrives daily, ahead of everything else, but moves with the weather.":
        "Señales mensuales de cuánto produce y vende la economía. La demanda eléctrica llega cada día, antes que todo lo "
        "demás, pero se mueve con el tiempo atmosférico.",
    "Industrial production and retail sales are seasonally and calendar adjusted by INE. Car sales and electricity demand are not, so only the 12-month change is shown.":
        "La producción industrial y las ventas minoristas están corregidas de efectos estacionales y de calendario por el "
        "INE. Las matriculaciones y la demanda eléctrica no, así que solo se muestra la variación a 12 meses.",
    "Retail sales, real": "Ventas minoristas, en términos reales",
    "Car sales": "Matriculaciones de turismos",
    "Past 12 months, thousands of cars": "Últimos 12 meses, miles de turismos",
    "Electricity demand": "Demanda eléctrica",
    "Average daily demand, % change on a year earlier": "Demanda media diaria, variación interanual, %",
    "Sentiment": "Confianza",
    "The European Commission asks firms and households every month how things are going. Surveys come out before the hard data they foreshadow.":
        "La Comisión Europea pregunta cada mes a empresas y hogares cómo van las cosas. Las encuestas se publican antes "
        "que los datos que anticipan.",
    "Survey": "Encuesta",
    "Index or balance": "Índice o saldo",
    "Economic sentiment (average = 100)": "Sentimiento económico (media = 100)",
    "Economic sentiment": "Sentimiento económico",
    "Index, long-run average = 100": "Índice, media de largo plazo = 100",
    "Confidence": "Confianza",
    "Balance of positive minus negative answers": "Saldo de respuestas positivas menos negativas",
    "Consumer confidence": "Confianza del consumidor",
    "Industry confidence": "Confianza industrial",
    "Construction confidence": "Confianza en la construcción",
    "Consumers": "Consumidores",
    "Confidence indicators are balances: the share of positive answers minus negative ones, so zero means as many optimists as pessimists. Spanish services and retail confidence stopped in 2024.":
        "Los indicadores de confianza son saldos: la proporción de respuestas positivas menos la de negativas, así que "
        "cero significa tantos optimistas como pesimistas. La confianza de los servicios y del comercio minorista en "
        "España dejó de publicarse en 2024.",
    "International tourists": "Turistas internacionales",
    "Spain is one of the world's most visited countries. Arrivals and spending come from INE's border surveys (FRONTUR, EGATUR), receipts from the balance of payments.":
        "España es uno de los países más visitados del mundo. Las llegadas y el gasto proceden de las encuestas en "
        "frontera del INE (FRONTUR, EGATUR); los ingresos, de la balanza de pagos.",
    "Latest month, not seasonally adjusted; changes in %": "Último mes, sin desestacionalizar; variaciones en %",
    "Tourists": "Turistas",
    "Tourist spending": "Gasto de los turistas",
    "Their spending": "Su gasto",
    "Tourism receipts (balance of payments)": "Ingresos por turismo (balanza de pagos)",
    "Tourism receipts, past 12 months": "Ingresos por turismo, últimos 12 meses",
    "Past 12 months, millions": "Últimos 12 meses, millones",
    "Past 12 months, € billion": "Últimos 12 meses, miles de millones de €",
    "Year to date sums the months since January and compares them with the same months a year earlier.":
        "En lo que va de año suma los meses desde enero y los compara con los mismos meses del año anterior.",
    "Current account": "Cuenta corriente",
    "What Spain earns from the rest of the world against what it pays: trade, tourism, income and transfers. A surplus means Spain lends to the rest of the world.":
        "Lo que España ingresa del resto del mundo frente a lo que paga: comercio, turismo, rentas y transferencias. Un "
        "superávit significa que España presta al resto del mundo.",
    "% of GDP or € million": "% del PIB o millones de €",
    "Current account balance": "Saldo por cuenta corriente",
    "Current account, past 12 months": "Cuenta corriente, últimos 12 meses",
    "Current account, % of GDP (quarter)": "Cuenta corriente, % del PIB (trimestre)",
    "Current account, % of GDP (past 4 quarters)": "Cuenta corriente, % del PIB (últimos 4 trimestres)",
    "% of GDP, average of the past four quarters": "% del PIB, media de los últimos cuatro trimestres",
    "Average": "Media",
    "Demand": "Demanda",
    "Tables 4 and 5 of the IMF's 2026 Article IV report for Spain: the balance of payments, in euros and in % of GDP, and external debt by sector and instrument, from Eurostat. The World Economic Outlook projects only the current account, so the other lines show … in the projection years.":
        "Los cuadros 4 y 5 del informe del Artículo IV de 2026 del FMI sobre España: la balanza de pagos, en euros y en % "
        "del PIB, y la deuda externa por sector e instrumento, de Eurostat. El World Economic Outlook solo proyecta la "
        "cuenta corriente, así que las demás líneas muestran … en los años de proyección.",
})

# ---------------------------------------------------------------- Regions
PAIRS.update({
    "Spain's 17 autonomous communities differ widely in unemployment, house prices and income per head. Regional figures come from INE's labour force survey, house price index, CPI and regional accounts.":
        "Las 17 comunidades autónomas de España difieren mucho en paro, precios de la vivienda y renta per cápita. Las "
        "cifras regionales proceden de la encuesta de población activa, el índice de precios de vivienda, el IPC y la "
        "contabilidad regional del INE.",
    "Region": "Comunidad",
    "%, unless stated": "%, salvo indicación",
    "Change on a year": "Variación en un año",
    "House prices, y/y": "Precios de la vivienda, a/a",
    "GDP per head, Spain = 100": "PIB per cápita, España = 100",
    "Unemployment comes from the labour force survey (EPA), not seasonally adjusted. Ceuta and Melilla are left out: their survey samples are small.":
        "El paro procede de la encuesta de población activa (EPA), sin desestacionalizar. Se dejan fuera Ceuta y "
        "Melilla: sus muestras son pequeñas.",
    "Unemployment by region": "Paro por comunidades",
    "% of the labour force (EPA)": "% de la población activa (EPA)",
    "House prices by region": "Precios de la vivienda por comunidades",
    "Inflation by region": "Inflación por comunidades",
    "CPI, % change on a year earlier": "IPC, variación interanual, %",
    "GDP per head by region": "PIB per cápita por comunidades",
    "Spain = 100, current prices": "España = 100, precios corrientes",
})
# The communities' own names (proper names, the same in both languages)
for name in ("Andalucía", "Aragón", "Asturias", "Illes Balears", "Canarias", "Cantabria", "Castilla y León",
             "Castilla-La Mancha", "Cataluña", "Comunitat Valenciana", "Extremadura", "Galicia", "Madrid", "Murcia",
             "Navarra", "País Vasco", "La Rioja"):
    PAIRS[name] = name
