"""Spanish for the International page (Batch 33c-2): Spain and its comparators (econpulse/pages.py "international",
and the facts, tables and charts written by econpulse/peers.py), and the Spanish names of the site's comparator
countries and their central banks, used on every page that shows them (International, Housing, Pensions, Trade).
Read by scripts/write_catalogue.py; the keys are the English exactly as the code writes it.
"""

PAIRS: dict[str, str] = {}

# ---------------------------------------------------------------- the countries and central banks (peers.COUNTRIES,
# peers.CENTRAL_BANKS): the chooser's chips, the tables' rows, the rankings' bars and the line charts' series. Those
# the Trade page or the frame added already are repeated here with the same Spanish.
PAIRS.update({
    "Spain": "España",
    "Euro area": "Zona del euro",
    "France": "Francia",
    "Germany": "Alemania",
    "Italy": "Italia",
    "Netherlands": "Países Bajos",
    "Portugal": "Portugal",
    "Poland": "Polonia",
    "United Kingdom": "Reino Unido",
    "United States": "Estados Unidos",
    "Canada": "Canadá",
    "Japan": "Japón",
    "ECB": "BCE",
    "ECB deposit rate": "Tipo de depósito del BCE",
    "National Bank of Poland": "Banco Nacional de Polonia",
    "Bank of England": "Banco de Inglaterra",
    "US Federal Reserve": "Reserva Federal",
    "Bank of Canada": "Banco de Canadá",
    "Bank of Japan": "Banco de Japón",
})

# ---------------------------------------------------------------- the blocks, panels and charts (pages.py)
PAIRS.update({
    "Spain next to the euro area and ten comparators: France, Germany, Italy, the Netherlands, Portugal and Poland in the EU, and the United Kingdom, the United States, Canada and Japan. The sections below take growth, jobs, prices and interest rates, the public finances, the current account and the IMF's outlook in turn.":
        "España junto a la zona del euro y diez comparables: Francia, Alemania, Italia, los Países Bajos, Portugal y "
        "Polonia en la UE, y el Reino Unido, Estados Unidos, Canadá y Japón. Las secciones siguientes repasan, una a "
        "una, el crecimiento, el empleo, los precios y los tipos de interés, las finanzas públicas, la balanza por "
        "cuenta corriente y las perspectivas del FMI.",
    "GDP growth, y/y": "Crecimiento del PIB, a/a",
    "Core inflation": "Inflación subyacente",
    "10-year yield": "Rentabilidad a 10 años",
    "Policy rate": "Tipo oficial",
    "Inflation is the harmonised index (HICP) in the EU and each country's CPI elsewhere; core inflation leaves out food and energy, where a current measure is available. 10-year yields are monthly averages. The euro-area countries share the ECB's deposit rate; the US rate is the mid-point of the Fed's target range. Sources: INE, Eurostat, ECB, OECD, BIS, US BLS and BEA.":
        "La inflación es la del índice armonizado (IPCA) en la UE y la del IPC de cada país en el resto; la subyacente "
        "excluye los alimentos y la energía, donde hay una medida actual. Las rentabilidades a 10 años son medias "
        "mensuales. Los países de la zona del euro comparten el tipo de depósito del BCE; el tipo de EE. UU. es el "
        "punto medio de la horquilla objetivo de la Reserva Federal. Fuentes: INE, Eurostat, BCE, OCDE, BPI, BLS y BEA "
        "de EE. UU.",
    # Growth
    "How fast each economy is growing, how far it has come since the end of 2019, the last quarter before the pandemic, and how rich it is per head at purchasing power.":
        "A qué ritmo crece cada economía, cuánto ha avanzado desde finales de 2019, el último trimestre antes de la "
        "pandemia, y cuál es su PIB per cápita en paridad de poder adquisitivo.",
    "Real GDP since 2019": "PIB real desde 2019",
    "Fourth quarter of 2019 = 100": "Cuarto trimestre de 2019 = 100",
    "Q4 2019": "T4 2019",
    "Real GDP, % change on a year earlier": "PIB real, variación interanual, %",
    # Jobs
    "Unemployment, for everyone and for people under 25, and the share of people aged 15 to 64 in work. Spain's unemployment and youth unemployment are the highest of the group.":
        "El paro, total y de los menores de 25 años, y el porcentaje de personas de 15 a 64 años con empleo. El paro y "
        "el paro juvenil de España son los más altos del grupo.",
    "% · changes on a year earlier in percentage points": "% · variaciones interanuales en puntos porcentuales",
    "1-yr change": "Variación en 1 año",
    "Employment rate, 15-64": "Tasa de empleo, 15-64",
    "Unemployment and youth unemployment are seasonally adjusted monthly rates; youth unemployment and the employment rate follow the OECD's harmonised definitions (people aged 15 to 24, and 15 to 64), and Eurostat's for the euro area (under 25). Sources: Eurostat, OECD, US BLS.":
        "El paro y el paro juvenil son tasas mensuales desestacionalizadas; el paro juvenil y la tasa de empleo siguen "
        "las definiciones armonizadas de la OCDE (personas de 15 a 24 años, y de 15 a 64), y las de Eurostat para la "
        "zona del euro (menores de 25). Fuentes: Eurostat, OCDE, BLS de EE. UU.",
    "% of the labour force": "% de la población activa",
    "People aged 15-24, % of the labour force that age": "Personas de 15 a 24 años, % de la población activa de esa edad",
    "People aged 15-64 in work, % of the population that age": "Personas de 15 a 64 años con empleo, % de la población de esa edad",
    "% of the labour force, seasonally adjusted": "% de la población activa, desestacionalizado",
    # Prices and interest rates
    "Inflation, policy rates and what governments pay to borrow for ten years. Spain, France, Germany, Italy, the Netherlands and Portugal share the ECB's rates; Poland, the UK, the US, Canada and Japan set their own.":
        "La inflación, los tipos oficiales y lo que pagan los Estados por endeudarse a diez años. España, Francia, "
        "Alemania, Italia, los Países Bajos y Portugal comparten los tipos del BCE; Polonia, el Reino Unido, EE. UU., "
        "Canadá y Japón fijan los suyos.",
    "% · spread in basis points": "% · diferencial en puntos básicos",
    "Spread over Germany": "Diferencial con Alemania",
    "Inflation on a year earlier (HICP in the EU, CPI elsewhere). 10-year yields and spreads over Germany's are monthly averages; spreads are shown for the euro-area countries. Sources: INE, Eurostat, ECB, OECD, BIS, US BLS.":
        "Inflación interanual (IPCA en la UE, IPC en el resto). Las rentabilidades a 10 años y los diferenciales con "
        "Alemania son medias mensuales; los diferenciales se muestran para los países de la zona del euro. Fuentes: INE, "
        "Eurostat, BCE, OCDE, BPI, BLS de EE. UU.",
    "% change on a year earlier (HICP in the EU, CPI elsewhere)": "Variación interanual, % (IPCA en la UE, IPC en el resto)",
    "%, end of month; the ECB sets the rate for the euro-area countries":
        "%, fin de mes; el BCE fija el tipo de los países de la zona del euro",
    "%, monthly average": "%, media mensual",
    "Borrowing costs over Germany": "Coste de financiación frente a Alemania",
    "10-year yield minus Germany's, basis points, monthly averages":
        "Rentabilidad a 10 años menos la de Alemania, puntos básicos, medias mensuales",
    # Pay and productivity
    "Real pay, compensation per employee after consumer prices, and productivity, output per person employed, over the past year and since 2019, from the European Commission's AMECO database.":
        "Los salarios reales, la remuneración por asalariado descontada la inflación, y la productividad, la producción "
        "por ocupado, en el último año y desde 2019, según la base de datos AMECO de la Comisión Europea.",
    # Public finances
    "Budget balances, the interest governments pay and their debt, all as a share of GDP, from the IMF's World Economic Outlook, with where it expects debt to be by the end of its projections.":
        "Los saldos presupuestarios, los intereses que pagan las administraciones públicas y su deuda, todo en "
        "porcentaje del PIB, según las Perspectivas de la economía mundial del FMI, con el nivel de deuda que prevé al "
        "final de sus proyecciones.",
    "Gross debt, % of GDP; the latest years are the IMF's projections":
        "Deuda bruta, % del PIB; los últimos años son proyecciones del FMI",
    # The current account
    "What each economy earns from the rest of the world, less what it pays: trade in goods and services, income and transfers. Spain has run a surplus every year since 2012, after a deficit of 9.4% of GDP in 2007, before the financial crisis.":
        "Lo que cada economía ingresa del resto del mundo, menos lo que le paga: el comercio de bienes y servicios, las "
        "rentas y las transferencias. España registra superávit todos los años desde 2012, tras un déficit del 9.4% del "
        "PIB en 2007, antes de la crisis financiera.",
    "% of GDP; the latest years are the IMF's projections": "% del PIB; los últimos años son proyecciones del FMI",
    # The IMF's outlook
    "What the IMF expects for growth, inflation and unemployment this year and next, from its latest World Economic Outlook. Its forecasts for Spain sit next to the other forecasters' on the Analysis page.":
        "Lo que espera el FMI para el crecimiento, la inflación y el paro este año y el próximo, según sus últimas "
        "Perspectivas de la economía mundial. Sus previsiones para España figuran junto a las de las demás "
        "instituciones en la página de Análisis.",
})

# ---------------------------------------------------------------- where Spain ranks (peers.facts, peers.outlook_facts)
# {rank} is the bare number in Spanish: the ordinal sign agrees with the noun ("el 3.º más rápido", "la 3.ª cifra").
PAIRS.update({
    "GDP since the end of 2019": "El PIB desde finales de 2019",
    "y/y, {period}": "a/a, {period}",
    "the fastest of {n} · {when}": "el más rápido de los {n} · {when}",
    "{rank} fastest of {n} · {when}": "el {rank}.º más rápido de los {n} · {when}",
    "the highest of {n} · {when}": "la cifra más alta de los {n} · {when}",
    "{rank} highest of {n} · {when}": "la {rank}.ª cifra más alta de los {n} · {when}",
    "the largest rise of {n} · {when}": "la mayor subida de los {n} · {when}",
    "{rank} largest rise of {n} · {when}": "la {rank}.ª mayor subida de los {n} · {when}",
    "Growth in {year}": "Crecimiento en {year}",
    "Unemployment in {year}": "Paro en {year}",
    "Debt in {year}": "Deuda en {year}",
    "IMF, {edition}": "FMI, {edition}",
    "the latest edition": "la última edición",
})

# ---------------------------------------------------------------- the tables (peers.growth_table, finances_table,
# outlook_table, pay_table)
PAIRS.update({
    "Country": "País",
    "Real GDP and GDP per head · {period}": "PIB real y PIB per cápita · {period}",
    "GDP growth, y/y %": "Crecimiento del PIB, a/a %",
    "Against end-2019 %": "Frente a finales de 2019 %",
    "GDP per head, PPP $ ({year})": "PIB per cápita, $ PPA ({year})",
    "Spain = 100": "España = 100",
    "GDP growth compares the latest quarter with a year earlier; a period after a figure means it is older than the others'. Against end-2019 compares real GDP with the fourth quarter of 2019, the last before the pandemic. GDP per head at purchasing power (international dollars) is the IMF's World Economic Outlook figure for {year}. Sources: INE, Eurostat, OECD, US BEA, IMF.":
        "El crecimiento del PIB compara el último trimestre con el mismo de un año antes; un periodo junto a una cifra "
        "indica que es más antigua que las demás. La columna frente a finales de 2019 compara el PIB real con el cuarto "
        "trimestre de 2019, el último antes de la pandemia. El PIB per cápita en paridad de poder adquisitivo (dólares "
        "internacionales) es la cifra de las Perspectivas de la economía mundial del FMI para {year}. Fuentes: INE, "
        "Eurostat, OCDE, BEA de EE. UU., FMI.",
    "% of GDP · IMF, {edition}": "% del PIB · FMI, {edition}",
    "Budget balance {year}": "Saldo presupuestario {year}",
    "Primary balance {year}": "Saldo primario {year}",
    "Net interest {year}": "Intereses netos {year}",
    "Debt {year}": "Deuda {year}",
    "Debt since 2019, pp": "Deuda desde 2019, pp",
    "Debt {year} (projected)": "Deuda {year} (proyección)",
    "General government, from the IMF's World Economic Outlook ({edition}): {year} is mostly outturn, and the IMF's estimate where the year's accounts are not final. The budget balance is net lending (a negative figure is a deficit); the primary balance leaves out interest, so net interest (paid less received) is the gap between the two. Debt is gross debt; the last column is the IMF's projection for {last}.":
        "Administraciones públicas, según las Perspectivas de la economía mundial del FMI ({edition}): {year} es sobre "
        "todo dato observado, y estimación del FMI donde las cuentas del año no son definitivas. El saldo "
        "presupuestario es la capacidad o necesidad de financiación (una cifra negativa es un déficit); el saldo "
        "primario excluye los intereses, así que los intereses netos (pagados menos cobrados) son la diferencia entre "
        "ambos. La deuda es la deuda bruta; la última columna es la proyección del FMI para {last}.",
    "% · IMF World Economic Outlook, {edition}": "% · Perspectivas de la economía mundial del FMI, {edition}",
    "GDP growth {year}": "Crecimiento del PIB {year}",
    "Inflation {year}": "Inflación {year}",
    "Unemployment {year}": "Paro {year}",
    "The IMF's projections: real GDP growth and average consumer price inflation over the year, and the unemployment rate on each country's own definition (so the levels compare less well than the changes). The IMF updates them in April and October. The forecasters followed for Spain alone are on the Analysis page.":
        "Proyecciones del FMI: crecimiento del PIB real e inflación media de los precios de consumo en el año, y tasa "
        "de paro según la definición de cada país (por eso los niveles se comparan peor que las variaciones). El FMI "
        "las actualiza en abril y octubre. Las previsiones de otras instituciones, que se siguen solo para España, "
        "están en la página de Análisis.",
    "% change · European Commission (AMECO), {year}": "Variación, % · Comisión Europea (AMECO), {year}",
    "Real pay, {year}": "Salarios reales, {year}",
    "Real pay since 2019": "Salarios reales desde 2019",
    "Productivity, {year}": "Productividad, {year}",
    "Productivity since 2019": "Productividad desde 2019",
    "Real pay is compensation per employee (wages and employers' social contributions) deflated by consumer prices; productivity is real GDP per person employed. Annual figures from the European Commission's AMECO database: {year} is partly the Commission's estimate. Not available for Canada, whose AMECO figures stop in 2024.":
        "Los salarios reales son la remuneración por asalariado (sueldos y cotizaciones sociales a cargo de los "
        "empleadores) deflactada por los precios de consumo; la productividad es el PIB real por ocupado. Cifras "
        "anuales de la base de datos AMECO de la Comisión Europea: {year} es en parte una estimación de la Comisión. No "
        "disponible para Canadá, cuyas cifras en AMECO terminan en 2024.",
})

# ---------------------------------------------------------------- the rankings (peers.*_ranking)
PAIRS.update({
    "GDP against the end of 2019": "El PIB frente a finales de 2019",
    "Real GDP, % change on the fourth quarter of 2019": "PIB real, variación sobre el cuarto trimestre de 2019, %",
    "INE, Eurostat, OECD, US BEA": "INE, Eurostat, OCDE, BEA de EE. UU.",
    "GDP per head at purchasing power": "PIB per cápita en paridad de poder adquisitivo",
    "Spain = 100, IMF figures for {year}": "España = 100, cifras del FMI para {year}",
    "IMF World Economic Outlook": "Perspectivas de la economía mundial del FMI",
    "IMF World Economic Outlook, {edition}": "Perspectivas de la economía mundial del FMI, {edition}",
    "Government debt": "Deuda pública",
    "Gross debt, % of GDP": "Deuda bruta, % del PIB",
    "Budget balance": "Saldo presupuestario",
    "General government net lending, % of GDP (negative = deficit)":
        "Capacidad o necesidad de financiación de las AA. PP., % del PIB (negativo = déficit)",
    "Net interest paid by governments": "Intereses netos pagados por las administraciones públicas",
    "Interest paid less interest received, % of GDP": "Intereses pagados menos intereses cobrados, % del PIB",
    "Current account": "Cuenta corriente",
    "Balance with the rest of the world, % of GDP": "Saldo con el resto del mundo, % del PIB",
    "GDP growth in {year}": "Crecimiento del PIB en {year}",
    "IMF projection, %": "Proyección del FMI, %",
    "Compensation per employee after consumer prices, % change on 2019":
        "Remuneración por asalariado descontados los precios de consumo, variación sobre 2019, %",
    "Real GDP per person employed, % change on 2019": "PIB real por ocupado, variación sobre 2019, %",
    "European Commission (AMECO)": "Comisión Europea (AMECO)",
})
PAIRS["EU"] = "UE"   # the European Union, on the Pensions page's comparisons
