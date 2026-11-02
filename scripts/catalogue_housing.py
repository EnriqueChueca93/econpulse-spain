"""Spanish for the Housing page (Batch 33c-2): the facts, tables and charts econpulse/housing.py writes, and the
page's static text in econpulse/pages.py (section "housing"). Read by scripts/write_catalogue.py; the keys are the
English exactly as the code writes it. Country names are left to the International page's catalogue.
"""

PAIRS: dict[str, str] = {}

# ---------------------------------------------------------------- house prices (pages.py)
PAIRS.update({
    "INE's house price index, built from notarised sales, for new and second-hand homes.":
        "El índice de precios de vivienda (IPV) del INE, elaborado a partir de las compraventas ante notario, para la "
        "vivienda nueva y la de segunda mano.",
    "Prices": "Precios",
    "All homes": "Todas las viviendas",
    "New homes": "Vivienda nueva",
    "Second-hand homes": "Vivienda de segunda mano",
    "Rents (CPI)": "Alquileres (IPC)",
    "House prices are not seasonally adjusted; the quarterly change is as INE reports it. The rents quarterly change uses Macroscope seasonal adjustment.":
        "Los precios de la vivienda no están desestacionalizados; la variación trimestral es la que publica el INE. La "
        "variación trimestral de los alquileres usa la desestacionalización de Macroscope.",
    "Second-hand": "Segunda mano",
    "Real house prices since the boom": "Precios reales de la vivienda desde el boom",
    "House prices deflated by the CPI, Q1 2007 = 100": "Precios de la vivienda deflactados por el IPC, T1 2007 = 100",
    "Q1 2007": "T1 2007",
    "Real house prices": "Precios reales de la vivienda",
})

# ---------------------------------------------------------------- affordability (housing.py and pages.py)
PAIRS.update({
    "What an average home costs against what households earn, and what a new mortgage takes from their income, from the Banco de España's housing indicators, with prices per square metre from mortgage appraisals and asking prices on the two largest property portals.":
        "Lo que cuesta una vivienda media frente a lo que ganan los hogares y la parte de su renta que se lleva una "
        "hipoteca nueva (el esfuerzo de acceso), según los indicadores del mercado de la vivienda del Banco de España, "
        "con los precios por metro cuadrado de las tasaciones hipotecarias y los precios de oferta de los dos mayores "
        "portales inmobiliarios.",
    "An average home costs": "Una vivienda media cuesta",
    "of a household's gross income · {period}; {avg} on average since 1987":
        "de la renta disponible bruta de un hogar · {period}; {avg} de media desde 1987",
    "A new mortgage takes": "Una hipoteca nueva absorbe",
    "of household income in the first year · {period}; {avg} on average":
        "de la renta del hogar el primer año · {period}; {avg} de media",
    "Price per m², appraisals": "Precio por m², tasaciones",
    "Asking price per m²": "Precio de oferta por m²",
    "Ministry of Housing": "Ministerio de Vivienda",
    "Idealista": "Idealista",
    "Fotocasa": "Fotocasa",
    "{source} · {period}, {change} on a year": "{source} · {period}, {change} en un año",
    "Latest and a year earlier": "Último dato y un año antes",
    "A year earlier": "Un año antes",
    "An average home, years of household income": "Vivienda media, años de renta del hogar",
    "A new mortgage, % of household income": "Hipoteca nueva, % de la renta del hogar",
    "Price per m²": "Precio por m²",
    "Appraisals (Ministry of Housing)": "Tasaciones (Ministerio de Vivienda)",
    "Homes up to 5 years old": "Viviendas de hasta 5 años",
    "Homes over 5 years old": "Viviendas de más de 5 años",
    "Asking prices, Idealista": "Precios de oferta, Idealista",
    "Asking prices, Fotocasa": "Precios de oferta, Fotocasa",
    "An average home is a free-market home of 93.75 m² at the appraised price; household income is gross disposable income. The mortgage takes a loan of 80% of the price at the going rate and term, before tax relief. Asking prices are what sellers ask on the portals, usually above the prices homes sell for. Sources: Banco de España, Ministry of Housing, Idealista, Fotocasa.":
        "La vivienda media es una vivienda libre de 93.75 m² a precio de tasación; la renta del hogar es la renta "
        "disponible bruta. La hipoteca financia el 80% del precio al tipo y el plazo vigentes, antes de deducciones "
        "fiscales. Los precios de oferta son los que piden los vendedores en los portales, normalmente por encima de los "
        "precios a los que se venden las viviendas. Fuentes: Banco de España, Ministerio de Vivienda, Idealista, Fotocasa.",
    "House prices and income": "Precio de la vivienda y renta",
    "Years of a household's gross income an average home costs":
        "Años de renta disponible bruta de un hogar que cuesta una vivienda media",
    "What a new mortgage takes": "Esfuerzo de acceso con una hipoteca nueva",
    "First-year payments, % of household gross income": "Pagos del primer año, % de la renta bruta del hogar",
    "Average {value}": "Media {value}",
    "Price per square metre": "Precio por metro cuadrado",
    "€ per m²": "€ por m²",
    "Appraisals": "Tasaciones",
})

# ---------------------------------------------------------------- rents and renting
PAIRS.update({
    "How many households rent, what renting a home out pays against its price, and how fast rents are rising against prices in general.":
        "Cuántos hogares viven de alquiler, qué rentabilidad da alquilar una vivienda frente a su precio y a qué ritmo "
        "suben los alquileres frente a los precios en general.",
    "Households renting": "Hogares que viven de alquiler",
    "{year}; {owners} own their home": "{year}; el {owners} tiene la vivienda en propiedad",
    "Gross rental yield": "Rentabilidad bruta del alquiler",
    "a year's rent over the price · {period}; 10-year bond {bond}":
        "un año de alquiler sobre el precio · {period}; bono a 10 años, {bond}",
    "a year's rent over the price · {period}": "un año de alquiler sobre el precio · {period}",
    "Total return on housing": "Rentabilidad total de la vivienda",
    "rent plus the rise in price, over a year · {period}": "alquiler más la subida del precio, en un año · {period}",
    "Owning and renting": "Propiedad y alquiler",
    "% of households, by tenure of their home": "% de los hogares, por régimen de tenencia de la vivienda",
    "Own": "En propiedad",
    "Rent": "De alquiler",
    "Rental yield and the 10-year bond": "Rentabilidad del alquiler y bono a 10 años",
    "Gross rental yield on housing and Spain's 10-year government yield, %":
        "Rentabilidad bruta del alquiler de vivienda y rentabilidad de la deuda pública española a 10 años, %",
    "Rental yield": "Rentabilidad del alquiler",
    "10-year bond": "Bono a 10 años",
    "Rents and consumer prices": "Alquileres y precios de consumo",
    "All consumer prices": "IPC general",
})

# ---------------------------------------------------------------- against other countries (OECD)
PAIRS.update({
    "Spain's house prices next to its comparators', from the OECD: real prices, and prices against incomes and against rents, each next to its own long-run average. The chips choose which countries the chart draws beside Spain.":
        "Los precios de la vivienda en España junto a los de sus comparables, según la OCDE: precios reales y precios "
        "frente a la renta y frente a los alquileres, cada uno junto a su propia media de largo plazo. Los botones eligen "
        "qué países se dibujan en el gráfico junto a España.",
    "Country": "País",
    "OECD analytical house prices": "Indicadores analíticos de precios de la vivienda de la OCDE",
    "OECD analytical house prices · {period}": "Indicadores analíticos de precios de la vivienda de la OCDE · {period}",
    "Real prices, 1-yr %": "Precios reales, 1 año %",
    "Real prices since 2015 %": "Precios reales desde 2015 %",
    "Price to income": "Precio/renta",
    "Price to rent": "Precio/alquiler",
    "100 = long-run average": "100 = media de largo plazo",
    "Real prices are house prices deflated by consumer prices. The two ratios compare house prices with disposable income per head and with rents, each against the country's own long-run average (the OECD's standardised ratios): above 100, homes are dearer than usual against incomes or rents. The OECD publishes no standardised ratios for Poland, and none against rents for the United States after 2024; some countries' figures come a few quarters late.":
        "Los precios reales son los precios de la vivienda deflactados por los precios de consumo. Las dos ratios "
        "comparan los precios de la vivienda con la renta disponible por habitante y con los alquileres, cada una frente "
        "a la media de largo plazo del propio país (las ratios estandarizadas de la OCDE): por encima de 100, la vivienda "
        "está más cara de lo habitual en relación con la renta o los alquileres. La OCDE no publica ratios "
        "estandarizadas para Polonia, ni frente a los alquileres para Estados Unidos después de 2024; las cifras de "
        "algunos países llegan con unos trimestres de retraso.",
    "House prices against incomes": "Precios de la vivienda frente a la renta",
    "Price-to-income ratio, 100 = the country's long-run average": "Ratio precio/renta, 100 = media de largo plazo del país",
    "House prices against rents": "Precios de la vivienda frente a los alquileres",
    "Price-to-rent ratio, 100 = the country's long-run average":
        "Ratio precio/alquiler, 100 = media de largo plazo del país",
    "Long-run average": "Media de largo plazo",
    "Deflated by consumer prices, 2015 = 100": "Deflactados por los precios de consumo, 2015 = 100",
    "2015": "2015",
})

# ---------------------------------------------------------------- building and households
PAIRS.update({
    "How many homes are being started against how fast the number of households grows. Starts come from the Ministry of Housing (free-market homes since 1980, protected ones since 1970), permits from the architects' associations, and households from INE's labour force survey.":
        "Cuántas viviendas se inician frente al ritmo al que crece el número de hogares. Las viviendas iniciadas "
        "proceden del Ministerio de Vivienda (las libres desde 1980, las protegidas desde 1970), los visados de obra "
        "nueva de los colegios de arquitectos técnicos y los hogares de la encuesta de población activa (EPA) del INE.",
    "{value} at the {year} peak": "{value} en el máximo de {year}",
    "Homes started": "Viviendas iniciadas",
    "past 12 months · {period}; {share} protected; {peak} at the {year} peak":
        "últimos 12 meses · {period}; {share} protegidas; {peak} en el máximo de {year}",
    "past 12 months · {period}; {peak} at the {year} peak": "últimos 12 meses · {period}; {peak} en el máximo de {year}",
    "New homes in building permits": "Viviendas en visados de obra nueva",
    "past 12 months · {period}, {change} on a year": "últimos 12 meses · {period}, {change} en un año",
    "past 12 months · {period}": "últimos 12 meses · {period}",
    "New households": "Hogares nuevos",
    "over a year · {period}; {total} million in all": "en un año · {period}; {total} millones en total",
    "Homes per household": "Viviendas por hogar",
    "{year} census; {before} in {before_year}": "censo de {year}; {before} en {before_year}",
    "{year} census": "censo de {year}",
    "Building": "Construcción",
    "Totals over 12 months; changes on a year earlier": "Totales de 12 meses; variaciones interanuales",
    "Homes started, past 12 months": "Viviendas iniciadas, últimos 12 meses",
    "Free-market": "Libres",
    "Protected": "Protegidas",
    "New homes in building permits, past 12 months": "Viviendas en visados de obra nueva, últimos 12 meses",
    "New households, over a year": "Hogares nuevos, en un año",
    "Investment in housing, real, % on a year": "Inversión en vivienda, en volumen, % interanual",
    "Building costs, % on a year": "Costes de construcción, % interanual",
    "Protected homes are state-supported homes sold or let at capped prices. Until 1979 the ministry counted only protected homes, so the totals start in 1980. Households grow with the population and as households get smaller. Sources: Ministry of Housing, Ministry of Transport (permits and costs), INE (households and investment), via the Banco de España.":
        "Las viviendas protegidas cuentan con ayuda pública y se venden o alquilan a precios limitados. Hasta 1979 el "
        "ministerio solo contaba las viviendas protegidas, así que los totales empiezan en 1980. Los hogares crecen con "
        "la población y a medida que se hacen más pequeños. Fuentes: Ministerio de Vivienda, Ministerio de Transportes "
        "(visados y costes), INE (hogares e inversión), a través del Banco de España.",
    "Past 12 months, thousands": "Últimos 12 meses, miles",
    "Homes started and new households": "Viviendas iniciadas y hogares nuevos",
    "Thousands over a year: homes started in the past 12 months, and the rise in households":
        "Miles en un año: viviendas iniciadas en los últimos 12 meses y aumento del número de hogares",
    "Building permits": "Visados de obra nueva",
    "New homes in permits, past 12 months, thousands": "Viviendas en visados de obra nueva, últimos 12 meses, miles",
    "Permits": "Visados",
})

# ---------------------------------------------------------------- sales
PAIRS.update({
    "How many homes change hands, new and second-hand, counted two ways: sales entered in the property registers (INE) and deeds signed before notaries (Ministry of Housing).":
        "Cuántas viviendas cambian de manos, nuevas y de segunda mano, contadas de dos formas: las compraventas inscritas "
        "en los registros de la propiedad (INE) y las escrituras firmadas ante notario (Ministerio de Vivienda).",
    "Registered sales": "Compraventas inscritas",
    "Sales entered in the property registers in the month (INE).":
        "Compraventas inscritas en los registros de la propiedad en el mes (INE).",
    "Homes sold over 12 months": "Viviendas vendidas en 12 meses",
    "Past 12 months": "Últimos 12 meses",
    "Registered (INE)": "Inscritas (INE)",
    "Signed before notaries (Ministry of Housing)": "Firmadas ante notario (Ministerio de Vivienda)",
    "The registers record a sale when its deed is registered, usually a month or two after it is signed, and the two sources count a home as new differently, so their split differs. Before 2007 the registered sales came quarterly from the registrars.":
        "Los registros anotan una compraventa cuando se inscribe su escritura, normalmente uno o dos meses después de "
        "firmarla, y las dos fuentes definen la vivienda nueva de forma distinta, así que su desglose difiere. Antes de "
        "2007 las compraventas inscritas procedían de los registradores, con periodicidad trimestral.",
    "Before notaries": "Ante notario",
    "New and second-hand sales": "Compraventas de vivienda nueva y de segunda mano",
    "Signed before notaries, past 12 months, thousands": "Firmadas ante notario, últimos 12 meses, miles",
    "New": "Nuevas",
})

# ---------------------------------------------------------------- mortgages and credit
PAIRS.update({
    "How many homes are bought with a mortgage, how much is lent against the price and for how long, how many housing loans go bad, and how much of the economy's debt is secured on property.":
        "Cuántas viviendas se compran con hipoteca, cuánto se presta frente al precio y a qué plazo, cuántos préstamos "
        "para vivienda entran en mora y qué parte de la deuda de la economía tiene garantía inmobiliaria.",
    "A new mortgage lends": "Una hipoteca nueva financia",
    "of the home's price on average · {period}; {over} of mortgages lend more than 80%":
        "del precio de la vivienda, de media · {period}; el {over} de las hipotecas financia más del 80%",
    "of the home's price on average · {period}": "del precio de la vivienda, de media · {period}",
    "Average term": "Plazo medio",
    "of new mortgages on homes · {period}": "de las hipotecas nuevas sobre viviendas · {period}",
    "Housing loans gone bad": "Morosidad del crédito a la vivienda",
    "non-performing · {period}; {peak}": "créditos dudosos · {period}; {peak}",
    "Housing loans": "Crédito a la vivienda",
    "owed by households · {period}; {peak}": "de los hogares · {period}; {peak}",
    "Mortgages on homes": "Hipotecas sobre viviendas",
    "Amount lent on them": "Importe prestado",
    "Average mortgage": "Hipoteca media",
    "New mortgage lending by banks": "Nuevo crédito hipotecario de los bancos",
    "Mortgages come from the property registers (INE), new lending from banks' reports to the ECB, which include renegotiated loans.":
        "Las hipotecas proceden de los registros de la propiedad (INE); el nuevo crédito, de la información que los "
        "bancos envían al BCE, que incluye los préstamos renegociados.",
    "Mortgage market": "Mercado hipotecario",
    "Quarterly": "Trimestral",
    "New mortgages, % of the home's price": "Hipotecas nuevas, % del precio de la vivienda",
    "Share lending more than 80%": "Proporción que financia más del 80%",
    "Average term of new mortgages": "Plazo medio de las hipotecas nuevas",
    "Non-performing housing loans, %": "Tasa de morosidad del crédito a la vivienda, %",
    "Debt secured on property": "Deuda con garantía inmobiliaria",
    "Households' housing loans": "Crédito a los hogares para vivienda",
    "All credit secured on property": "Todo el crédito con garantía inmobiliaria",
    "Of which to builders and developers": "Del cual, a constructoras y promotoras",
    "Loan-to-value and terms of new mortgages on homes from the property registrars; non-performing loans and credit from the Banco de España.":
        "La relación préstamo-valor y los plazos de las hipotecas nuevas sobre viviendas, de los registradores de la "
        "propiedad; la morosidad y el crédito, del Banco de España.",
    "How much new mortgages lend": "Cuánto financian las hipotecas nuevas",
    "%: the average loan against the home's price, and the share of loans over 80% of it":
        "%: el préstamo medio frente al precio de la vivienda y la proporción de préstamos que superan el 80% de este",
    "Loan to value": "Préstamo/valor",
    "Share over 80%": "Más del 80%",
    "Builders and developers": "Constructoras y promotoras",
    "Non-performing housing loans": "Morosidad del crédito a la vivienda",
    "% of housing loans to households": "% del crédito a los hogares para vivienda",
    "Non-performing": "Dudosos",
})

# ---------------------------------------------------------------- household finances and wealth
PAIRS.update({
    "Spanish households have paid down much of the debt they took on in the boom; most mortgages are variable-rate, so rates matter quickly. Their homes are most of what they own.":
        "Los hogares españoles han reducido buena parte de la deuda que contrajeron durante el boom; la mayoría de las "
        "hipotecas son a tipo variable, así que los tipos de interés se notan enseguida. Su vivienda es la mayor parte "
        "de lo que poseen.",
    "Housing wealth": "Riqueza inmobiliaria",
    "€{amount} trillion": "{amount} billones de €",
    "what households' homes are worth · {period}; {times} times their disposable income ({peak} at the {year} peak)":
        "lo que valen las viviendas de los hogares · {period}; {times} veces su renta disponible ({peak} en el máximo "
        "de {year})",
    "what households' homes are worth · {period}": "lo que valen las viviendas de los hogares · {period}",
    "Net financial wealth": "Riqueza financiera neta",
    "disposable income: savings and investments less debts · {period}; the highest since {year}":
        "la renta disponible: ahorro e inversiones menos deudas · {period}; la más alta desde {year}",
    "disposable income: savings and investments less debts · {period}":
        "la renta disponible: ahorro e inversiones menos deudas · {period}",
    "Household debt, % of GDP": "Deuda de los hogares, % del PIB",
    "Household debt, % of disposable income": "Deuda de los hogares, % de la renta disponible",
    "Debt service, % of disposable income": "Servicio de la deuda, % de la renta disponible",
    "Saving rate, % of disposable income (SA)": "Tasa de ahorro, % de la renta disponible (desest.)",
    "Housing loans, growth on a year earlier": "Crédito para vivienda, variación interanual",
    "Debt service is what households pay in interest and principal (BIS). The saving rate is the share of disposable income not spent (INE).":
        "El servicio de la deuda es lo que pagan los hogares en intereses y devolución del principal (BPI). La tasa de "
        "ahorro es la parte de la renta disponible que no se gasta (INE).",
    "Wealth": "Riqueza",
    "€ bn and % of gross disposable income": "mm € y % de la renta disponible bruta",
    "Housing wealth, € bn": "Riqueza inmobiliaria, mm €",
    "Housing wealth, % of disposable income": "Riqueza inmobiliaria, % de la renta disponible",
    "Net financial wealth, % of disposable income": "Riqueza financiera neta, % de la renta disponible",
    "Total wealth, % of disposable income": "Riqueza total, % de la renta disponible",
    "Households and non-profit institutions serving them, from the Banco de España. Net financial wealth is savings and investments less debts.":
        "Hogares e instituciones sin fines de lucro al servicio de los hogares, del Banco de España. La riqueza "
        "financiera neta es el ahorro y las inversiones menos las deudas.",
    "Household debt": "Deuda de los hogares",
    "Household saving rate": "Tasa de ahorro de los hogares",
    "% of disposable income, seasonally adjusted": "% de la renta disponible, desestacionalizada",
    "Saving rate": "Tasa de ahorro",
    "Housing loans and mortgage rates": "Crédito para vivienda y tipos hipotecarios",
    "%: growth of housing loans on a year earlier, and the rate on new mortgages":
        "%: variación interanual del crédito para vivienda y tipo de las hipotecas nuevas",
    "Loan growth": "Crecimiento del crédito",
    "Mortgage rate": "Tipo hipotecario",
    "Household wealth": "Riqueza de los hogares",
    "% of gross disposable income": "% de la renta disponible bruta",
    "Net financial": "Financiera neta",
})

# ---------------------------------------------------------------- commercial property
PAIRS.update({
    "Prices of offices, shops and industrial buildings, from the Banco de España's commercial property price index, and how much of banks' lending goes to property.":
        "Los precios de oficinas, locales comerciales y naves industriales, del índice de precios de inmuebles "
        "comerciales del Banco de España, y qué parte del crédito bancario va al sector inmobiliario.",
    "Commercial property prices": "Precios de los inmuebles comerciales",
    "Offices": "Oficinas",
    "Industrial buildings": "Naves industriales",
    "on a year · {period}; {index} against 100 in 2014": "en un año · {period}; índice {index}, frente a 100 en 2014",
    "Banks' loans for commercial property": "Crédito bancario a inmuebles comerciales",
    "of their loans · {period}; housing loans {homes}": "del crédito total · {period}; crédito a la vivienda, {homes}",
    "of their loans · {period}": "del crédito total · {period}",
    "Index, 2014 = 100; changes in %": "Índice, 2014 = 100; variaciones en %",
    "Index": "Índice",
    "All commercial property": "Todos los inmuebles comerciales",
    "Retail premises": "Locales comerciales",
    "Prime (the best properties and locations)": "Prime (los mejores inmuebles y ubicaciones)",
    "Not seasonally adjusted. Banks' shares of loans come from the Banco de España's financial soundness indicators, whose definitions changed in 2017 and 2022.":
        "Sin desestacionalizar. Las proporciones del crédito bancario proceden de los indicadores de solidez financiera "
        "del Banco de España, cuyas definiciones cambiaron en 2017 y 2022.",
    "Index, 2014 = 100": "Índice, 2014 = 100",
    "2014": "2014",
    "Retail": "Locales",
    "Industrial": "Naves industriales",
})
