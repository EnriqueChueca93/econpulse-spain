"""Spanish for the section pages, part I (Batch 33b): GDP, Labour market, Every industry, Wages, Inflation,
Financial and ECB. Read by scripts/write_catalogue.py; the keys are the English exactly as the code writes it.
"""

PAIRS: dict[str, str] = {}

# ---------------------------------------------------------------- the pages' introductions (build.SECTION_PAGES)
PAIRS.update({
    "What Spain produces, and who is spending: households, firms, government and the rest of the world.":
        "Lo que produce España y quién gasta: hogares, empresas, Administraciones públicas y el resto del mundo.",
    "Jobs, unemployment and contracts by sector, from the Social Security register and the public employment service, INE's labour force survey (EPA), who works by age, sex, citizenship and education, the effect of an ageing population, worker flows, hours, vacancies and layoffs.":
        "Empleo, paro y contratos por sectores, de la afiliación a la Seguridad Social y del servicio público de empleo; la "
        "encuesta de población activa del INE (EPA); quién trabaja por edad, sexo, nacionalidad y nivel educativo; el efecto "
        "del envejecimiento; los flujos de trabajadores, las horas, las vacantes y los despidos.",
    "Pay and labour costs, how they compare with inflation, and pay by activity: a month, per hour, bonuses and growth.":
        "Salarios y costes laborales, cómo se comparan con la inflación, y los salarios por actividad: al mes, por hora, "
        "pagas extraordinarias y crecimiento.",
    "Consumer prices on Spain's own index (IPC) and the harmonised index the ECB targets (IPCA), underlying inflation across the basket, and energy prices.":
        "Los precios de consumo en el índice propio de España (IPC) y en el armonizado que sigue el objetivo del BCE (IPCA), "
        "la inflación subyacente en toda la cesta y los precios de la energía.",
    "Spanish bond yields and the prima de riesgo, Euribor, the IBEX 35, the euro and commodities, and the IMF-style financial soundness indicators.":
        "La rentabilidad de la deuda española y la prima de riesgo, el euríbor, el IBEX 35, el euro y las materias primas, y "
        "los indicadores de solidez financiera al estilo del FMI.",
    "Spain has no monetary policy of its own: the European Central Bank sets rates for the whole euro area. The IMF-style monetary table shows what that means for the Banco de España and Spanish banks.":
        "España no tiene política monetaria propia: el Banco Central Europeo fija los tipos de toda la zona del euro. El "
        "cuadro monetario al estilo del FMI muestra lo que eso supone para el Banco de España y los bancos españoles.",
})

# ---------------------------------------------------------------- shared by the tables and charts of every page
PAIRS.update({
    # maturities and horizons on the curve charts' axes
    "3m": "3m", "6m": "6m", "9m": "9m", "1y": "1a", "2y": "2a", "3y": "3a", "5y": "5a", "10y": "10a", "15y": "15a",
    "30y": "30a",
    "{caption} · through {period}": "{caption} · hasta {period}",
    "Latest": "Último",
    "Previous": "Anterior",
    "1-mo ago": "Hace 1 mes",
    "1-qtr ago": "Hace 1 trim.",
    "1-yr ago": "Hace 1 año",
    "End-{year}": "Final de {year}",
    "q/q": "t/t",
    "y/y": "a/a",
    "m/m": "m/m",
    "YTD": "En el año",
    "1-mo": "1 mes",
    "3-mo": "3 meses",
    "12-mo": "12 meses",
    "1-mo ann.": "1 mes anualiz.",
    "3-mo ann.": "3 meses anualiz.",
    "6-mo ann.": "6 meses anualiz.",
    "12-mo %": "12 meses %",
    "1-day": "1 día",
    "1-week": "1 semana",
    "1-month": "1 mes",
    "1-yr": "1 año",
    "% change on a year earlier": "Variación interanual, %",
    "Flash estimate for {period}: {figures} on a year earlier. The table follows when INE publishes the full index.":
        "Indicador adelantado de {period}: {figures} interanual. La tabla se actualiza cuando el INE publica el índice completo.",
    "Item": "Concepto",
    "Change": "Variación",
    "Rate": "Tipo",
    "Horizon": "Horizonte",
    "Activity": "Actividad",
    "By activity": "Por actividad",
    "All": "Total",
    "All activities": "Todas las actividades",
    "{change} on a year earlier": "{change} interanual",
    "12 months to {month}": "12 meses hasta {month}",
    "average of the four quarters to {quarter}": "media de los cuatro trimestres hasta {quarter}",
    "Macroscope seasonal adjustment": "desestacionalización de Macroscope",
    "Eurostat; Macroscope calculation": "Eurostat; cálculo de Macroscope",
    # the section template
    "Compare Spain with up to %(n)s:": "Comparar España con hasta %(n)s:",
    "Countries drawn beside Spain on the charts": "Países que se dibujan junto a España en los gráficos",
    "All %(n)s series in this section, with their sources": "Las %(n)s series de esta sección, con sus fuentes",
    "Charts and detailed tables for this page arrive in Batch %(batch)s of the build plan. For now, here is every indicator tracked, with its latest reading.":
        "Los gráficos y las tablas de esta página llegan en la fase %(batch)s del plan. Por ahora, estos son los indicadores que se siguen, con su último dato.",
    "No indicators in this section yet.": "Todavía no hay indicadores en esta sección.",
    # activities (INE's labour cost survey, CNAE-09 sections)
    "Mining": "Industrias extractivas",
    "Manufacturing": "Industria manufacturera",
    "Electricity and gas": "Electricidad y gas",
    "Water and waste": "Agua y residuos",
    "Construction": "Construcción",
    "Trade": "Comercio",
    "Transport and storage": "Transporte y almacenamiento",
    "Hospitality": "Hostelería",
    "Information and IT": "Información y comunicaciones",
    "Finance and insurance": "Finanzas y seguros",
    "Real estate": "Actividades inmobiliarias",
    "Professional services": "Actividades profesionales",
    "Administrative services": "Actividades administrativas",
    "Public administration": "Administración pública",
    "Education": "Educación",
    "Health and social work": "Sanidad y servicios sociales",
    "Arts and recreation": "Actividades artísticas y recreativas",
    "Other services": "Otros servicios",
    "Agriculture": "Agricultura",
    "Industry": "Industria",
    "Services": "Servicios",
    "Goods": "Bienes",
})

# ---------------------------------------------------------------- GDP
PAIRS.update({
    "GDP and its components": "El PIB y sus componentes",
    "Real growth, seasonally and calendar adjusted by INE. Following Spanish practice, quarterly growth is not annualised.":
        "Crecimiento real, corregido de efectos estacionales y de calendario por el INE. Como es habitual en España, "
        "el crecimiento trimestral no se anualiza.",
    "Real growth": "Crecimiento real",
    "% change; contributions in percentage points": "Variación, %; aportaciones en puntos porcentuales",
    "Contrib. q/q": "Aport. t/t",
    "Contrib. y/y": "Aport. a/a",
    "GDP": "PIB",
    "Spending": "Demanda",
    "Domestic demand": "Demanda nacional",
    "Household consumption": "Consumo de los hogares",
    "Government consumption": "Consumo de las AA. PP.",
    "Fixed investment": "Inversión en capital fijo",
    "of which housing": "de la cual, vivienda",
    "Machinery and equipment": "Maquinaria y bienes de equipo",
    "External demand (net exports)": "Demanda externa (exportaciones netas)",
    "External demand": "Demanda externa",
    "Exports": "Exportaciones",
    "Services, including tourism": "Servicios, incluido el turismo",
    "Imports": "Importaciones",
    "Output by sector (gross value added)": "Producción por sectores (valor añadido bruto)",
    "Prices and jobs": "Precios y empleo",
    "Nominal GDP": "PIB nominal",
    "GDP deflator": "Deflactor del PIB",
    "Employment (full-time equivalent jobs)": "Empleo (puestos equivalentes a tiempo completo)",
    "Contributions are percentage points of GDP growth, as published by INE: domestic and external demand add up to GDP growth, give or take rounding.":
        "Las aportaciones son puntos porcentuales del crecimiento del PIB, tal como las publica el INE: la demanda nacional "
        "y la externa suman el crecimiento del PIB, salvo redondeo.",
    "Real GDP growth": "Crecimiento del PIB real",
    "% change on the previous quarter (bars) and on a year earlier (line)": "Variación intertrimestral (barras) e interanual (línea), %",
    "What drives annual growth": "Qué impulsa el crecimiento anual",
    "Contributions to GDP growth on a year earlier, percentage points": "Aportaciones al crecimiento interanual del PIB, puntos porcentuales",
    "Investment": "Inversión",
    "Real fixed investment, % change on a year earlier": "Inversión real en capital fijo, variación interanual, %",
    "Housing": "Vivienda",
    "Equipment": "Bienes de equipo",
    "Real exports, % change on a year earlier; services include tourism": "Exportaciones reales, variación interanual, %; los servicios incluyen el turismo",
    "Output by sector": "Producción por sectores",
    "Real gross value added, % change on a year earlier": "Valor añadido bruto real, variación interanual, %",
    "Productivity and labour costs": "Productividad y costes laborales",
    "Output per job and per hour worked, and the labour cost of each unit of output. INE publishes these as changes on a year earlier.":
        "La producción por puesto de trabajo y por hora trabajada, y el coste laboral de cada unidad producida. "
        "El INE los publica como variaciones interanuales.",
    "Productivity and costs": "Productividad y costes",
    "Productivity per full-time equivalent job": "Productividad por puesto equivalente a tiempo completo",
    "Productivity per hour worked": "Productividad por hora trabajada",
    "Compensation per employee": "Remuneración por asalariado",
    "Unit labour cost": "Coste laboral unitario",
    "Productivity and unit labour costs": "Productividad y costes laborales unitarios",
    "Productivity per hour, pay per employee and unit labour cost, % change on a year earlier":
        "Productividad por hora, remuneración por asalariado y coste laboral unitario, variación interanual, %",
    "Productivity": "Productividad",
    "Pay": "Remuneración",
    "IMF-style main indicators": "Principales indicadores al estilo del FMI",
    "Table 1 of the IMF's 2026 Article IV report for Spain, rebuilt from public data: actual years from INE, Eurostat and the ECB, projections from the IMF's World Economic Outlook database. That database publishes only some of the report's lines, so the others show … in the projection years.":
        "El cuadro 1 del informe del Artículo IV de 2026 del FMI sobre España, reconstruido con datos públicos: los años "
        "observados, del INE, Eurostat y el BCE; las proyecciones, de la base de datos del World Economic Outlook del FMI. "
        "Esa base publica solo algunas líneas del informe, así que las demás muestran … en los años de proyección.",
})

# ---------------------------------------------------------------- Wages
PAIRS.update({
    "Wages and prices": "Salarios y precios",
    "What employers pay per worker and per hour (INE's quarterly labour cost survey, ETCL), pay in the national accounts, and rises agreed in collective agreements.":
        "Lo que pagan las empresas por trabajador y por hora (la Encuesta Trimestral de Coste Laboral del INE, ETCL), la "
        "remuneración en la contabilidad nacional y las subidas pactadas en los convenios colectivos.",
    "Wage cost per worker": "Coste salarial por trabajador",
    "Wage cost per hour": "Coste salarial por hora",
    "Total labour cost per worker": "Coste laboral total por trabajador",
    "Regular pay only (no bonuses)": "Solo salario ordinario (sin pagas extraordinarias)",
    "Compensation per employee (national accounts)": "Remuneración por asalariado (contabilidad nacional)",
    "Labour cost index, wages (Eurostat)": "Índice de costes laborales, salarios (Eurostat)",
    "Rise agreed in collective agreements, this year": "Subida pactada en convenios colectivos, este año",
    "The labour cost survey (ETCL) is not seasonally adjusted and bonuses move between quarters, so pay is compared with a year earlier. The collective-agreements figure is the average rise agreed for the current year in agreements registered so far, not a change on a year earlier.":
        "La encuesta de coste laboral (ETCL) no está desestacionalizada y las pagas extraordinarias cambian de trimestre, "
        "así que los salarios se comparan con un año antes. La cifra de convenios es la subida media pactada para el año en "
        "curso en los convenios registrados hasta ahora, no una variación interanual.",
    "Real wage cost per worker": "Coste salarial real por trabajador",
    "Wage cost per worker deflated by the CPI, % change on a year earlier": "Coste salarial por trabajador deflactado por el IPC, variación interanual, %",
    "% change on a year earlier: wage cost per worker (quarterly) and CPI (monthly)":
        "Variación interanual, %: coste salarial por trabajador (trimestral) e IPC (mensual)",
    "CPI": "IPC",
    "Real wages": "Salarios reales",
    "After inflation": "Descontada la inflación",
    "Rises agreed in collective agreements": "Subidas pactadas en los convenios colectivos",
    "Average rise agreed for the year in agreements registered so far, %": "Subida media pactada para el año en los convenios registrados hasta ahora, %",
    "Agreed rise": "Subida pactada",
    "Monthly pay by activity": "Salario mensual por actividad",
    "Average wage cost per worker by activity, from INE's labour cost survey: gross pay including bonuses, before the worker's tax and contributions, for full-time and part-time employees together, a month and per hour actually worked, with the share that comes from bonuses and extra months' pay. Averages of four quarters, as bonuses make pay seasonal.":
        "El coste salarial medio por trabajador en cada actividad, de la encuesta de coste laboral del INE: salario bruto con "
        "pagas extraordinarias, antes de impuestos y cotizaciones del trabajador, para asalariados a tiempo completo y parcial "
        "juntos, al mes y por hora efectiva de trabajo, con la parte que procede de pagas extraordinarias y atrasos. Medias de "
        "cuatro trimestres, porque las pagas extraordinarias hacen estacional el salario.",
    "€ and % · averages of the past four quarters · through {period}": "€ y % · medias de los últimos cuatro trimestres · hasta {period}",
    "€ a month": "€ al mes",
    "€ an hour": "€ por hora",
    "Bonuses and extras %": "Pagas extra %",
    "y/y %": "a/a %",
    "Latest qtr y/y %": "Último trim. a/a %",
    "Since {year}, after inflation %": "Desde {year}, descontada la inflación %",
    "Wage cost per worker: gross pay before the worker's tax and contributions, for full-time and part-time employees together. Bonuses and extras are the share of pay from bonuses, extra months' pay and arrears. y/y compares the average of the past four quarters with the four before; the latest quarter alone can swing with the timing of bonuses. The change since 2019 compares the past four quarters with 2019, deflated by the CPI over the same quarters.":
        "Coste salarial por trabajador: salario bruto antes de impuestos y cotizaciones del trabajador, para asalariados a "
        "tiempo completo y parcial juntos. Pagas extra es la parte del salario que procede de pagas extraordinarias, pagos "
        "de vencimiento superior al mes y atrasos. a/a compara la media de los últimos cuatro trimestres con la de los cuatro "
        "anteriores; el último trimestre por sí solo puede oscilar según cuándo se cobren las pagas. La variación desde 2019 "
        "compara los últimos cuatro trimestres con 2019, deflactados por el IPC de los mismos trimestres.",
    "In the four quarters to {quarter}, pay per worker ranged from {low_pay} a month in {low} to {high_pay} in {high}, {times} times as much.":
        "En los cuatro trimestres hasta {quarter}, el coste salarial por trabajador fue desde {low_pay} al mes en {low} "
        "hasta {high_pay} en {high}, {times} veces más.",
    "Per hour worked the range is {low_pay} in {low} to {high_pay} in {high}, {times} times as much: part-time work, more common in the lower-paid activities, explains a little of the monthly gap.":
        "Por hora trabajada, va desde {low_pay} en {low} hasta {high_pay} en {high}, {times} veces más: el trabajo a tiempo "
        "parcial, más frecuente en las actividades peor pagadas, explica una pequeña parte de la diferencia mensual.",
    "Pay per hour by activity": "Salario por hora por actividad",
    "Wage cost per worker, € a month, average of the past four quarters": "Coste salarial por trabajador, € al mes, media de los últimos cuatro trimestres",
    "Wage cost per hour actually worked, €, average of the past four quarters": "Coste salarial por hora efectiva, €, media de los últimos cuatro trimestres",
    "How much of pay is bonuses and extras": "Cuánto del salario son pagas extraordinarias",
    "Bonuses, extra months' pay and arrears, % of pay over the past four quarters":
        "Pagas extraordinarias, pagos de vencimiento superior al mes y atrasos, % del salario en los últimos cuatro trimestres",
    "Pay growth by activity": "Crecimiento salarial por actividad",
    "How fast pay is rising in each activity, and how it has done against prices since 2019. Growth compares averages of four quarters: the latest quarter alone can jump or fall when bonuses come at a different time of the year, above all in the activities that pay large ones.":
        "A qué ritmo suben los salarios en cada actividad y cómo les ha ido frente a los precios desde 2019. El crecimiento "
        "compara medias de cuatro trimestres: el último trimestre por sí solo puede saltar o caer cuando las pagas "
        "extraordinarias llegan en otro momento del año, sobre todo en las actividades que las pagan grandes.",
    "Average of the past four quarters, % change on the four before": "Media de los últimos cuatro trimestres, variación sobre los cuatro anteriores, %",
    "Pay since 2019, after inflation": "Salarios desde 2019, descontada la inflación",
    "Pay since {year}, after inflation": "Salarios desde {year}, descontada la inflación",
    "Past four quarters against 2019, deflated by the CPI, % change": "Últimos cuatro trimestres frente a 2019, deflactados por el IPC, variación, %",
    "Past four quarters against {year}, deflated by the CPI, % change": "Últimos cuatro trimestres frente a {year}, deflactados por el IPC, variación, %",
    "Pay growth, all activities": "Crecimiento salarial, todas las actividades",
    "four quarters to {quarter} on the four before": "cuatro trimestres hasta {quarter} sobre los cuatro anteriores",
    "Since {year}, after inflation": "Desde {year}, descontada la inflación",
    "pay per worker against the CPI, all activities": "salario por trabajador frente al IPC, todas las actividades",
    "Fastest rise": "Mayor subida",
    "Slowest rise": "Menor subida",
    "{change} on a year": "{change} en un año",
    "{activity}: pay quarter by quarter": "{activity}: salario trimestre a trimestre",
    "Wage cost per worker, € a month; the gap between the lines is bonuses, extra months' pay and arrears":
        "Coste salarial por trabajador, € al mes; la distancia entre las líneas son pagas extraordinarias y atrasos",
    "All pay": "Salario total",
    "Regular pay": "Salario ordinario",
    "{change} higher": "{change} más alto",
    "{change} lower": "{change} más bajo",
    "{first} than a year earlier in {prev} and {second} in {quarter}": "{first} que un año antes en {prev} y {second} en {quarter}",
    "{first} than a year earlier in {quarter}": "{first} que un año antes en {quarter}",
    "{activity} swings most from quarter to quarter: pay per worker was {when}, but the average of the past four quarters grew {change}.":
        "{activity} es la actividad que más oscila de un trimestre a otro: el salario por trabajador fue {when}, pero la media "
        "de los últimos cuatro trimestres creció un {change}.",
    "{activity} swings most from quarter to quarter: pay per worker was {when}, but the average of the past four quarters fell {change}.":
        "{activity} es la actividad que más oscila de un trimestre a otro: el salario por trabajador fue {when}, pero la media "
        "de los últimos cuatro trimestres cayó un {change}.",
    "Most of the swing is in bonuses and other extra payments, which came at a different time of the year; the chart below shows them quarter by quarter.":
        "La mayor parte de la oscilación está en las pagas extraordinarias y otros pagos, que llegaron en otro momento del "
        "año; el gráfico de abajo los muestra trimestre a trimestre.",
})

# ---------------------------------------------------------------- ECB
PAIRS.update({
    "Rates and inflation": "Tipos e inflación",
    "The ECB sets three rates. The one that steers the economy is the deposit facility rate, what banks earn on money left at the central bank: it puts a floor under market rates, and €STR, the overnight rate banks charge each other, trades just below it.":
        "El BCE fija tres tipos. El que orienta la economía es el de la facilidad de depósito, lo que ganan los bancos por el "
        "dinero que dejan en el banco central: pone un suelo a los tipos de mercado, y el €STR, el tipo a un día que se "
        "cobran los bancos entre sí, cotiza justo por debajo.",
    "Deposit facility rate": "Tipo de la facilidad de depósito",
    "Last change": "Último cambio",
    "took effect {day}": "en vigor desde el {day}",
    "Next decision": "Próxima decisión",
    "today": "hoy",
    "in {n} day": "dentro de {n} día",
    "in {n} days": "dentro de {n} días",
    "See the ECB calendar": "Ver el calendario del BCE",
    "€STR, overnight": "€STR, a un día",
    "€STR": "€STR",
    "€STR, overnight market rate": "€STR, tipo de mercado a un día",
    "%; changes in basis points": "%; variaciones en puntos básicos",
    "Deposit facility": "Facilidad de depósito",
    "Main refinancing operations": "Operaciones principales de financiación",
    "Main refinancing": "Operaciones principales de financiación",
    "Marginal lending facility": "Facilidad marginal de crédito",
    "Date it took effect": "Fecha de entrada en vigor",
    "Recent changes in the deposit facility rate · through {day}": "Cambios recientes del tipo de la facilidad de depósito · hasta el {day}",
    "Deposit rate": "Tipo de depósito",
    "New rates take effect a few days after the decision is announced (on the Wednesday after it, since 2024).":
        "Los nuevos tipos entran en vigor unos días después de anunciarse la decisión (el miércoles siguiente, desde 2024).",
    "ECB rates since 2019": "Tipos del BCE desde 2019",
    "%, daily": "%, diario",
    "The deposit rate since 1999": "El tipo de depósito desde 1999",
    "%: the ECB deposit rate and euro-area inflation (HICP, headline and core)":
        "%: el tipo de depósito del BCE y la inflación de la zona del euro (IAPC, general y subyacente)",
    "Market-implied path": "La senda que descuenta el mercado",
    "There is no free feed of the swap rates traders use to price ECB decisions. As a rough stand-in, these are forward rates on AAA euro-area government bonds: the short-term rate the bond market implies for each future date. They include a term premium, so they tend to overstate the expected path, more so further out.":
        "No hay una fuente gratuita de los tipos swap que usan los operadores para anticipar las decisiones del BCE. Como "
        "aproximación, estos son los tipos a plazo de la deuda pública AAA de la zona del euro: el tipo a corto plazo que el "
        "mercado de bonos descuenta para cada fecha futura. Incluyen una prima por plazo, así que tienden a exagerar la senda "
        "esperada, más cuanto más lejos.",
    "%; the gap with today's deposit rate in basis points": "%; la diferencia con el tipo de depósito actual en puntos básicos",
    "Forward rate": "Tipo a plazo",
    "Over deposit rate": "Sobre el tipo de depósito",
    "3 months ahead": "A 3 meses",
    "6 months ahead": "A 6 meses",
    "9 months ahead": "A 9 meses",
    "1 year ahead": "A 1 año",
    "2 years ahead": "A 2 años",
    "3 years ahead": "A 3 años",
    "Euro-area AAA forward rates by horizon, %": "Tipos a plazo AAA de la zona del euro por horizonte, %",
    "The rate expected a year ahead": "El tipo esperado dentro de un año",
    "%: AAA forward rate one year ahead and the deposit rate": "%: tipo a plazo AAA a un año y tipo de depósito",
    "The Banco de España's balance sheet in the Eurosystem, bank lending and deposits, and interest rates, at the end of each year. The Article IV report for Spain has no monetary table, since the ECB sets policy for the euro area; this one follows the IMF's layout for other countries.":
        "El balance del Banco de España en el Eurosistema, el crédito y los depósitos bancarios y los tipos de interés, a "
        "final de cada año. El informe del Artículo IV sobre España no tiene cuadro monetario, porque el BCE fija la política "
        "de la zona del euro; este sigue el formato del FMI para otros países.",
})

# ---------------------------------------------------------------- Every industry (industry-detail.html)
PAIRS.update({
    "Registrations by industry": "Afiliación por actividad",
    "Thousands; average change per month, seasonally adjusted by Macroscope for 1 and 3 months":
        "Miles; variación media mensual, desestacionalizada por Macroscope para 1 y 3 meses",
    "The 12-month columns use the registrations as published; the 1- and 3-month columns are seasonally adjusted by Macroscope.":
        "Las columnas de 12 meses usan la afiliación tal como se publica; las de 1 y 3 meses están desestacionalizadas por Macroscope.",
    "Change on the month before, thousands, seasonally adjusted; line: 3-month average":
        "Variación sobre el mes anterior, miles, desestacionalizada; línea: media de 3 meses",
    "Monthly change": "Variación mensual",
    "3-month average": "Media de 3 meses",
    "about {n} thousand registrations of {what}": "unos {n} mil afiliados de {what}",
    "motor vehicle repair, from trade to other services": "reparación de vehículos de motor, del comercio a otros servicios",
    "real estate development, from construction to real estate": "promoción inmobiliaria, de la construcción a las actividades inmobiliarias",
    "All registrations": "Toda la afiliación",
    "All registrations (general scheme and self-employed)": "Toda la afiliación (régimen general y autónomos)",
    "Goods-producing": "Producción de bienes",
    "Service-providing": "Servicios",
    "Agriculture, forestry and fishing": "Agricultura, ganadería, silvicultura y pesca",
    "Mining and quarrying": "Industrias extractivas",
    "Food, beverages and tobacco": "Alimentación, bebidas y tabaco",
    "Textiles, clothing and leather": "Textil, confección, cuero y calzado",
    "Wood, paper and printing": "Madera, papel y artes gráficas",
    "Petroleum, chemicals and pharmaceuticals": "Refino, química y farmacia",
    "Rubber, plastics and other mineral products": "Caucho, plásticos y otros minerales no metálicos",
    "Metals and metal products": "Metalurgia y productos metálicos",
    "Electronics, electrical equipment and machinery": "Electrónica, material eléctrico y maquinaria",
    "Motor vehicles and other transport equipment": "Vehículos de motor y otro material de transporte",
    "Furniture, other manufacturing and repair": "Muebles, otras manufacturas y reparación",
    "Energy, water and waste": "Energía, agua y residuos",
    "Trade, transport and hospitality": "Comercio, transporte y hostelería",
    "Wholesale and retail trade": "Comercio al por mayor y al por menor",
    "Accommodation and food services": "Hostelería",
    "Accommodation": "Servicios de alojamiento",
    "Restaurants and bars": "Restaurantes y bares",
    "Information, finance and business services": "Información, finanzas y servicios a empresas",
    "Information and communication": "Información y comunicaciones",
    "Computer programming and information services": "Programación informática y servicios de información",
    "Professional, scientific and technical": "Actividades profesionales, científicas y técnicas",
    "Administrative and support services": "Actividades administrativas y servicios auxiliares",
    "Education, health and public administration": "Educación, sanidad y Administración pública",
    "Public administration and defence": "Administración pública y defensa",
    "Health": "Actividades sanitarias",
    "Residential care and social work": "Asistencia en establecimientos residenciales y servicios sociales",
    "Leisure and other services": "Ocio y otros servicios",
    "Arts, entertainment and recreation": "Actividades artísticas, recreativas y de entretenimiento",
    "Other services, incl. repairs": "Otros servicios, incluidas reparaciones",
    "Households as employers": "Hogares como empleadores",
})

# ---------------------------------------------------------------- Labour market
PAIRS.update({
    # jobs and job seekers
    "Jobs and job seekers": "Empleo y paro registrado",
    "Workers registered with the Social Security (afiliados), the earliest monthly read on jobs, and job seekers registered at public employment offices (paro registrado).":
        "Los afiliados a la Seguridad Social, el primer dato mensual sobre el empleo, y los demandantes de empleo inscritos "
        "en las oficinas públicas de empleo (paro registrado).",
    "Registrations": "Afiliación",
    "Registered unemployment": "Paro registrado",
    "Registered unemployed": "Parados registrados",
    "Thousands, as published": "Miles, tal como se publican",
    "Thousands, as published, and % change on a year earlier": "Miles, tal como se publican, y variación interanual, %",
    "Year to date": "En lo que va de año",
    "YTD y/y": "En el año, a/a",
    "Registrations: monthly change": "Afiliación: variación mensual",
    "Registered unemployment: monthly change": "Paro registrado: variación mensual",
    "Thousands, seasonally adjusted by Macroscope": "Miles, desestacionalizados por Macroscope",
    "% change in average registrations, as published": "Variación de la afiliación media, tal como se publica, %",
    "% change in registered unemployment, as published": "Variación del paro registrado, tal como se publica, %",
    "The 1- and 3-month columns are seasonally adjusted by Macroscope, so they can differ from the ministry's own adjusted figures. The 12-month column uses the published data.":
        "Las columnas de 1 y 3 meses están desestacionalizadas por Macroscope, así que pueden diferir de las cifras "
        "desestacionalizadas del ministerio. La columna de 12 meses usa los datos publicados.",
    "The 1- and 3-month columns are seasonally adjusted by Macroscope; the 12-month column uses the published data.":
        "Las columnas de 1 y 3 meses están desestacionalizadas por Macroscope; la de 12 meses usa los datos publicados.",
    "Average change per month, thousands": "Variación media mensual, miles",
    "Thousands": "Miles",
    "Level": "Nivel",
    # by sector
    "By sector": "Por sectores",
    "By type of work": "Por tipo de trabajo",
    "Average monthly Social Security registrations by sector and by type of work, from the ministry's monthly workbooks. The 1- and 3-month changes use the ministry's own seasonal adjustment; the 12-month change, the figures as published. From January 2026 the sectors follow the new classification of activities (CNAE-2025); Macroscope links construction and services across the change, which moved real estate development from one to the other. Every industry, month by month, is on its own page (Labour market menu, or the chart's More link).":
        "La afiliación media a la Seguridad Social por sectores y por tipo de trabajo, de los ficheros mensuales del "
        "ministerio. Las variaciones de 1 y 3 meses usan la desestacionalización del propio ministerio; la de 12 meses, las "
        "cifras publicadas. Desde enero de 2026 los sectores siguen la nueva clasificación de actividades (CNAE-2025); "
        "Macroscope enlaza la construcción y los servicios a través del cambio, que pasó la promoción inmobiliaria de uno a "
        "otro. Todas las actividades, mes a mes, tienen su propia página (menú Mercado laboral, o el enlace Más del gráfico).",
    "Agriculture, livestock and fishing": "Agricultura, ganadería y pesca",
    "Employees": "Asalariados",
    "Self-employed": "Autónomos",
    "The sectors add up to slightly less than the total: a few registrations have no activity recorded.":
        "Los sectores suman algo menos que el total: unos pocos afiliados no tienen actividad registrada.",
    "Jobs by sector: monthly change": "Empleo por sectores: variación mensual",
    "Thousands, seasonally adjusted by the Social Security; agriculture is in the table":
        "Miles, desestacionalizados por la Seguridad Social; la agricultura está en la tabla",
    "Jobs by sector: change on a year earlier": "Empleo por sectores: variación interanual",
    # unemployment by sector and benefits
    "Registered unemployment by the sector of the last job, from the public employment service (SEPE), and the number of people receiving unemployment benefits.":
        "El paro registrado por el sector del último empleo, del Servicio Público de Empleo Estatal (SEPE), y el número de "
        "beneficiarios de prestaciones por desempleo.",
    "By sector of the last job": "Por sector del último empleo",
    "No previous job": "Sin empleo anterior",
    "Unemployment benefit recipients": "Beneficiarios de prestaciones por desempleo",
    "Benefits": "Prestaciones",
    "Unemployment by sector: change on a year earlier": "Paro por sectores: variación interanual",
    # EPA
    "Unemployment (EPA)": "Paro (EPA)",
    "INE's quarterly household survey, the official measure of unemployment. It is not seasonally adjusted, so the comparison with a year earlier is the cleanest.":
        "La encuesta trimestral a hogares del INE, la medida oficial del paro. No está desestacionalizada, así que la "
        "comparación con un año antes es la más limpia.",
    "EPA": "EPA",
    "% unless stated": "% salvo indicación",
    "Unemployment rate": "Tasa de paro",
    "Unemployment rate (EPA)": "Tasa de paro (EPA)",
    "Activity rate": "Tasa de actividad",
    "Employment rate": "Tasa de empleo",
    "People employed, thousands": "Ocupados, miles",
    "Employment, thousands": "Ocupados, miles",
    "Long-term unemployment rate": "Tasa de paro de larga duración",
    "Under 25": "Menores de 25 años",
    "Under 25s": "Menores de 25 años",
    "Youth unemployment": "Paro juvenil",
    "Under 25s, % of the labour force, seasonally adjusted": "Menores de 25 años, % de la población activa, desestacionalizado",
    "Monthly estimates": "Estimaciones mensuales",
    "Monthly (SA)": "Mensual (desest.)",
    "% of the labour force: Eurostat's monthly estimate (adjusted) and the EPA (quarterly, unadjusted)":
        "% de la población activa: estimación mensual de Eurostat (desestacionalizada) y EPA (trimestral, sin desestacionalizar)",
    "Unemployment rate, %, seasonally adjusted (Eurostat)": "Tasa de paro, %, desestacionalizada (Eurostat)",
    # contracts
    "Contracts": "Contratos",
    "Contracts by type": "Contratos por tipo",
    "Employment contracts registered each month with the public employment service. The labour reform in force since 2022 restricted temporary contracts: permanent ones, including the seasonal fijo discontinuo kind, went from about one in ten new contracts in 2019–21 to about four in ten since.":
        "Los contratos de trabajo registrados cada mes en el servicio público de empleo. La reforma laboral en vigor desde "
        "2022 restringió los contratos temporales: los indefinidos, incluidos los fijos discontinuos, pasaron de cerca de uno "
        "de cada diez contratos nuevos en 2019–21 a cerca de cuatro de cada diez desde entonces.",
    "All contracts": "Todos los contratos",
    "Permanent": "Indefinidos",
    "o.w. fijo discontinuo": "de ellos, fijos discontinuos",
    "o.w. fijo discontinuo (seasonal permanent)": "de ellos, fijos discontinuos",
    "o.w. conversions from temporary": "de ellos, conversiones de temporales",
    "Temporary": "Temporales",
    "Full time": "Jornada completa",
    "Part time": "Jornada parcial",
    "By working time": "Por jornada",
    "By working time, the public employment service counts fijo discontinuo contracts separately.":
        "Por jornada, el servicio público de empleo cuenta aparte los contratos fijos discontinuos.",
    "Thousands registered over the past 12 months": "Miles registrados en los últimos 12 meses",
    "Permanent contracts and the 2022 reform": "Los contratos indefinidos y la reforma de 2022",
    "% of contracts registered, average of the past 12 months": "% de los contratos registrados, media de los últimos 12 meses",
    "% of all contracts, average of the past 12 months": "% del total de contratos, media de los últimos 12 meses",
    "Fijo discontinuo": "Fijos discontinuos",
    "Other permanent": "Otros indefinidos",
    "Shares": "Porcentajes",
    "Temporary contracts": "Contratos temporales",
    "Temporary contracts, % of employees": "Contratos temporales, % de los asalariados",
    "% of employees; the 2022 labour reform took effect that spring": "% de los asalariados; la reforma laboral de 2022 entró en vigor esa primavera",
    # who works
    "Employment and ageing": "Empleo y envejecimiento",
    "The labour force survey by group, from Eurostat. Employment rates have risen for every group since 2019, most for women and people aged 55–64, and prime-age employment (25–54) is closing in on the euro area's. Charts show averages of the past four quarters, as the figures are not seasonally adjusted.":
        "La encuesta de población activa por grupos, de Eurostat. Las tasas de empleo han subido en todos los grupos desde "
        "2019, sobre todo entre las mujeres y las personas de 55 a 64 años, y el empleo en edad central (25–54) se acerca al "
        "de la zona del euro. Los gráficos muestran medias de los últimos cuatro trimestres, porque las cifras no están "
        "desestacionalizadas.",
    "Group": "Grupo",
    "% of each group's population (participation, employment) or labour force (unemployment)":
        "% de la población de cada grupo (actividad, empleo) o de su población activa (paro)",
    "Participation": "Actividad",
    "Employment, 1-yr change": "Empleo, variación en 1 año",
    "Unemployment, 1-yr change": "Paro, variación en 1 año",
    "All, 15–64": "Total, 15–64",
    "By sex, 15–64": "Por sexo, 15–64",
    "By sex, 25–54": "Por sexo, 25–54",
    "Men": "Hombres",
    "Women": "Mujeres",
    "By age": "Por edad",
    "15–24": "15–24",
    "25–54": "25–54",
    "25–54 (prime age)": "25–54 (edad central)",
    "55–64": "55–64",
    "By citizenship, 15–64": "Por nacionalidad, 15–64",
    "Spanish": "Españoles",
    "Other EU": "Otros de la UE",
    "Other EU countries": "Otros países de la UE",
    "Non-EU": "De fuera de la UE",
    "Countries outside the EU": "Países de fuera de la UE",
    "By education, 25–64": "Por nivel educativo, 25–64",
    "Lower secondary": "Primera etapa de secundaria",
    "Lower secondary at most": "Primera etapa de secundaria como máximo",
    "Upper secondary": "Segunda etapa de secundaria",
    "Tertiary": "Educación superior",
    "Eurostat's labour force survey (INE's EPA, on Eurostat's age bands: INE's own figures start at 16). Changes are on the same quarter a year earlier, in percentage points, as the figures are not seasonally adjusted. Rates for small groups, such as citizens of other EU countries, move more from one quarter to the next because fewer people are surveyed.":
        "La encuesta de población activa de Eurostat (la EPA del INE, con los tramos de edad de Eurostat: las cifras propias "
        "del INE empiezan a los 16 años). Las variaciones son sobre el mismo trimestre del año anterior, en puntos "
        "porcentuales, porque las cifras no están desestacionalizadas. Las tasas de los grupos pequeños, como los ciudadanos "
        "de otros países de la UE, se mueven más de un trimestre a otro porque se encuesta a menos personas.",
    "Employment rate by age": "Tasa de empleo por edad",
    "Employment rate, ages 15 and over, %, average of the past four quarters": "Tasa de empleo, 15 años y más, %, media de los últimos cuatro trimestres",
    "Employment rate, ages 25–54, %, average of the past four quarters": "Tasa de empleo, 25–54 años, %, media de los últimos cuatro trimestres",
    "Women and men at prime age": "Mujeres y hombres en edad central",
    "Prime-age employment: Spain and the euro area": "Empleo en edad central: España y la zona del euro",
    "Euro area": "Zona del euro",
    "Participation by age": "Actividad por edad",
    "Participation rate, ages 15 and over, %, average of the past four quarters": "Tasa de actividad, 15 años y más, %, media de los últimos cuatro trimestres",
    "Unemployment by citizenship": "Paro por nacionalidad",
    "Ages 15–64, % of the labour force, average of the past four quarters": "15–64 años, % de la población activa, media de los últimos cuatro trimestres",
    "Unemployment by education": "Paro por nivel educativo",
    "Ages 25–64, % of the labour force, average of the past four quarters": "25–64 años, % de la población activa, media de los últimos cuatro trimestres",
    # an older population
    "An older population": "Una población más envejecida",
    "As the baby-boom generations reach retirement, a growing share of adults are past working age, which pulls down the participation and employment rates of everyone aged 15 and over even when each age group works as much as before. Macroscope holds the population's mix by sex and five-year age group at its 2008 shares, letting each group's own rate move, to show how much of the change comes from ageing.":
        "A medida que las generaciones del baby boom llegan a la jubilación, una parte creciente de los adultos ha pasado la "
        "edad de trabajar, lo que rebaja las tasas de actividad y de empleo del conjunto de mayores de 15 años aunque cada "
        "grupo de edad trabaje tanto como antes. Macroscope mantiene la composición de la población por sexo y grupos de "
        "cinco años de edad en sus pesos de 2008, dejando que se mueva la tasa de cada grupo, para mostrar cuánto del "
        "cambio se debe al envejecimiento.",
    "Participation, 15 and over": "Actividad, 15 años y más",
    "At the {year} age mix": "Con la estructura de edades de {year}",
    "At the 2008 age mix": "Con la estructura de edades de 2008",
    "each age group's rate today, weighted as in {year}": "la tasa actual de cada grupo de edad, ponderada como en {year}",
    "Effect of ageing since {year}": "Efecto del envejecimiento desde {year}",
    "on the participation rate": "sobre la tasa de actividad",
    "Aged 65 and over": "65 años y más",
    "of people 15 and over, from {then} in {year}": "de las personas de 15 años y más, desde el {then} de {year}",
    "Participation of everyone aged 15 and over peaked at {peak} in the four quarters to {quarter} and is {now} now. At the {year} age mix it would have gone from {then} to {today}":
        "La tasa de actividad de los mayores de 15 años tocó máximo en el {peak} en los cuatro trimestres hasta {quarter} y "
        "ahora es del {now}. Con la estructura de edades de {year} habría pasado del {then} al {today}",
    ": the fall comes from the population's ageing; within age groups, participation has risen on balance.":
        ": la caída se debe al envejecimiento de la población; dentro de cada grupo de edad, la actividad ha subido en conjunto.",
    ": participation within age groups has fallen too.": ": la actividad dentro de los grupos de edad también ha bajado.",
    "Participation and ageing": "Actividad y envejecimiento",
    "Participation rate": "Tasa de actividad",
    "Actual": "Observada",
    "% of the population aged 15 and over, average of the past four quarters": "% de la población de 15 años y más, media de los últimos cuatro trimestres",
    "All ages": "Todas las edades",
    "Ages 15 and over": "15 años y más",
    "Aged 65 and over, % of people 15 and over": "65 años y más, % de las personas de 15 años y más",
    "Aged 65 and over, % of people aged 15 and over, average of the past four quarters":
        "65 años y más, % de las personas de 15 años y más, media de los últimos cuatro trimestres",
    "Macroscope calculation from Eurostat's labour force survey: the rates of men and women in 13 age groups (15–19 to 70–74, and 75 and over), weighted by each group's share of the population, actual or as in 2008. People in private households only.":
        "Cálculo de Macroscope con la encuesta de población activa de Eurostat: las tasas de hombres y mujeres en 13 grupos "
        "de edad (de 15–19 a 70–74, y 75 y más), ponderadas por el peso de cada grupo en la población, el actual o el de "
        "2008. Solo personas en viviendas familiares.",
    "%, average of the past four quarters": "%, media de los últimos cuatro trimestres",
    # flows
    "Where the unemployed go": "Adónde van los parados",
    "Behind the unemployment rate, people move all the time: some of the unemployed find work or give up looking, and some of the employed lose their jobs or leave the labour force. Eurostat follows the same people from one quarter to the next in the labour force survey. More of the unemployed find a job each quarter than before the pandemic, and fewer workers lose theirs.":
        "Detrás de la tasa de paro, la gente se mueve todo el tiempo: algunos parados encuentran trabajo o dejan de buscarlo, "
        "y algunos ocupados pierden su empleo o salen de la población activa. Eurostat sigue a las mismas personas de un "
        "trimestre al siguiente en la encuesta de población activa. Cada trimestre encuentran empleo más parados que antes de "
        "la pandemia, y menos ocupados pierden el suyo.",
    "From one quarter to the next": "De un trimestre al siguiente",
    "The unemployed": "Los parados",
    "Find a job": "Encuentran empleo",
    "Stop looking": "Dejan de buscar",
    "Stop looking (leave the labour force)": "Dejan de buscar (salen de la población activa)",
    "The employed": "Los ocupados",
    "Lose their job": "Pierden el empleo",
    "Leave the labour force": "Salen de la población activa",
    "The inactive": "Los inactivos",
    "Start work": "Empiezan a trabajar",
    "Eurostat's labour market transitions, from the labour force survey's panel of households.":
        "Las transiciones en el mercado laboral de Eurostat, a partir del panel de hogares de la encuesta de población activa.",
    "% of the unemployed who, a quarter later, are employed or out of the labour force":
        "% de los parados que, un trimestre después, están ocupados o fuera de la población activa",
    "Losing or leaving a job": "Perder o dejar el empleo",
    "% of the employed who, a quarter later, are unemployed or out of the labour force":
        "% de los ocupados que, un trimestre después, están parados o fuera de la población activa",
    # hours
    "Hours": "Horas",
    "Hours show how much work gets done, not just how many people do it. Hours per person employed have drifted down since the early 2000s as part-time work and shorter schedules spread. INE's labour cost survey adds hours per employee by activity and the hours lost to sick leave.":
        "Las horas muestran cuánto trabajo se hace, no solo cuánta gente lo hace. Las horas por ocupado han bajado poco a "
        "poco desde principios de los 2000, a medida que se extendían la jornada parcial y los horarios más cortos. La "
        "encuesta de coste laboral del INE añade las horas por asalariado en cada actividad y las horas perdidas por "
        "incapacidad temporal.",
    "Hours, unless stated": "Horas, salvo indicación",
    "Hours a week per person employed": "Horas semanales por ocupado",
    "Hours worked, millions a quarter": "Horas trabajadas, millones por trimestre",
    "Per employee a month, average of the past four quarters": "Por asalariado al mes, media de los últimos cuatro trimestres",
    "Overtime": "Horas extraordinarias",
    "Sick leave": "Incapacidad temporal",
    "Hours a week are the quarter's hours per person employed divided by 13. Hours per employee come from INE's labour cost survey (ETCL), which covers employees in industry, construction and services, and are not seasonally adjusted.":
        "Las horas semanales son las horas del trimestre por ocupado divididas entre 13. Las horas por asalariado proceden de "
        "la encuesta de coste laboral del INE (ETCL), que cubre a los asalariados de la industria, la construcción y los "
        "servicios, y no están desestacionalizadas.",
    "Sick leave took {now} a month per employee in the four quarters to {quarter}, against {then} in 2019 ({change})":
        "La incapacidad temporal supuso {now} al mes por asalariado en los cuatro trimestres hasta {quarter}, frente a {then} "
        "en 2019 ({change})",
    ", the equivalent of {share} of the hours worked.": ", el equivalente al {share} de las horas trabajadas.",
    "Hours per person employed": "Horas por ocupado",
    "Hours worked a week, national accounts, seasonally adjusted": "Horas trabajadas a la semana, contabilidad nacional, desestacionalizadas",
    "Hours a week": "Horas semanales",
    "National accounts, seasonally adjusted": "Contabilidad nacional, desestacionalizada",
    "Hours worked by activity": "Horas trabajadas por actividad",
    "Hours per employee a month, average of the past four quarters": "Horas por asalariado al mes, media de los últimos cuatro trimestres",
    "Hours lost to sick leave": "Horas perdidas por incapacidad temporal",
    # slack and vacancies
    "Slack and unemployment": "Holgura y paro",
    "Unemployment understates how much spare labour there is. Eurostat's measure of slack adds part-timers who want more hours and people who could work but are not looking. Vacancies show the other side: the posts firms are trying to fill.":
        "El paro subestima cuánta mano de obra hay disponible. La medida de holgura de Eurostat añade a quienes trabajan a "
        "tiempo parcial y quieren más horas y a quienes podrían trabajar pero no buscan. Las vacantes muestran el otro lado: "
        "los puestos que las empresas intentan cubrir.",
    "% of the labour force; slack also counts the underemployed and people not looking":
        "% de la población activa; la holgura cuenta también a los subempleados y a quienes no buscan",
    "Slack (SA)": "Holgura (desest.)",
    "Labour market slack, % of the extended labour force": "Holgura del mercado laboral, % de la población activa ampliada",
    "Vacancies": "Vacantes",
    "Job vacancies, thousands": "Vacantes, miles",
    "Vacancies are not seasonally adjusted, so the four-quarter average shows the trend.":
        "Las vacantes no están desestacionalizadas, así que la media de cuatro trimestres muestra la tendencia.",
    "Beveridge curve": "Curva de Beveridge",
    "Each point is a quarter: unemployment against vacancies (four-quarter average)":
        "Cada punto es un trimestre: paro frente a vacantes (media de cuatro trimestres)",
    "Where the vacancies are": "Dónde están las vacantes",
    "The posts firms and public bodies are trying to fill, from INE's labour cost survey. Vacancies are few in Spain by European standards, and a large share of them are in public administration.":
        "Los puestos que las empresas y los organismos públicos intentan cubrir, de la encuesta de coste laboral del INE. En "
        "España hay pocas vacantes para lo habitual en Europa, y una gran parte está en la Administración pública.",
    "All vacancies": "Todas las vacantes",
    "Thousands, average of the past four quarters": "Miles, media de los últimos cuatro trimestres",
    "Not seasonally adjusted. Mining, energy, water and real estate are left out: INE does not publish their vacancies in many quarters.":
        "Sin desestacionalizar. Se dejan fuera las industrias extractivas, la energía, el agua y las actividades "
        "inmobiliarias: el INE no publica sus vacantes en muchos trimestres.",
    "Job vacancies, average of the past four quarters": "Vacantes, media de los últimos cuatro trimestres",
    "Vacancies in the largest private activities": "Vacantes en las mayores actividades privadas",
    # dismissals and ERTE
    "Dismissals": "Despidos",
    "Firms in difficulty can dismiss groups of workers (despidos colectivos, through an ERE) or, under an ERTE, suspend contracts or cut working hours for a time, keeping people on the payroll while unemployment benefits cover part of their pay. The Ministry of Labour counts the workers affected by the procedures of each month. Figures start in January 2023; December 2023 is missing, as the ministry published only that year's total.":
        "Las empresas en dificultades pueden despedir a grupos de trabajadores (despidos colectivos, mediante un ERE) o, con "
        "un ERTE, suspender contratos o reducir la jornada durante un tiempo, manteniendo a los trabajadores en plantilla "
        "mientras la prestación por desempleo cubre parte de su salario. El Ministerio de Trabajo cuenta los trabajadores "
        "afectados por los procedimientos de cada mes. Las cifras empiezan en enero de 2023; falta diciembre de 2023, porque "
        "el ministerio solo publicó el total de ese año.",
    "Workers affected": "Trabajadores afectados",
    "Collective dismissals": "Despidos colectivos",
    "Contract suspensions": "Suspensiones de contrato",
    "Contract suspensions (ERTE)": "Suspensiones de contrato (ERTE)",
    "Cuts in hours": "Reducciones de jornada",
    "Cuts in working hours (ERTE)": "Reducciones de jornada (ERTE)",
    "All procedures": "Todos los procedimientos",
    "Suspensions": "Suspensiones",
    "Thousands, by measure": "Miles, por medida",
    "Workers affected each month": "Trabajadores afectados cada mes",
    "Workers affected over the past 12 months": "Trabajadores afectados en los últimos 12 meses",
    "Provisional monthly figures (Estadística de Regulación de Empleo); each year's final figures differ slightly.":
        "Cifras mensuales provisionales (Estadística de Regulación de Empleo); las cifras definitivas de cada año difieren "
        "ligeramente.",
    "% of each group, seasonally adjusted": "% de cada grupo, desestacionalizado",
})

# ---------------------------------------------------------------- Inflation
PAIRS.update({
    "Consumer prices": "Precios de consumo",
    "Spain's own consumer price index. Core inflation leaves out energy and unprocessed food, the most volatile prices; INE splits the rest into services, goods and processed food.":
        "El índice de precios de consumo de España. La inflación subyacente deja fuera la energía y los alimentos no "
        "elaborados, los precios más volátiles; el INE divide el resto en servicios, bienes y alimentos elaborados.",
    "% change": "Variación, %",
    "Headline": "General",
    "Core": "Subyacente",
    "Components": "Componentes",
    "Energy": "Energía",
    "Unprocessed food": "Alimentos no elaborados",
    "Processed food": "Alimentos elaborados",
    "Processed food, drinks and tobacco": "Alimentos elaborados, bebidas y tabaco",
    "Non-energy industrial goods": "Bienes industriales sin energía",
    "Energy and fresh food": "Energía y alimentos frescos",
    "Selected items": "Partidas seleccionadas",
    "Rents": "Alquileres",
    "Horizons under 12 months are annualised and use Macroscope seasonal adjustment, because INE publishes these indices unadjusted. The 12-month column matches the published annual rates.":
        "Los horizontes de menos de 12 meses están anualizados y usan la desestacionalización de Macroscope, porque el INE "
        "publica estos índices sin desestacionalizar. La columna de 12 meses coincide con las tasas anuales publicadas.",
    "CPI inflation": "Inflación del IPC",
    "Annual inflation, % change on a year earlier": "Inflación anual, variación interanual, %",
    "Core CPI": "IPC subyacente",
    "core CPI": "IPC subyacente",
    "Core CPI momentum": "El impulso del IPC subyacente",
    "3-month annualised (seasonally adjusted by Macroscope) and 12-month % change":
        "Variación a 3 meses anualizada (desestacionalizada por Macroscope) y a 12 meses, %",
    "CPI rents, % change on a year earlier": "Alquileres en el IPC, variación interanual, %",
    "Latest reading and earlier values": "Último dato y valores anteriores",
    # HICP
    "Spain and the euro area": "España y la zona del euro",
    "The harmonised index is the measure the ECB targets, built the same way in every euro-area country.":
        "El índice armonizado es la medida que sigue el objetivo del BCE, elaborada igual en todos los países de la zona del euro.",
    "Headline HICP": "IAPC general",
    "Core HICP leaves out energy, food, alcohol and tobacco. Horizons under 12 months are annualised and use Macroscope seasonal adjustment, because Eurostat publishes these indices unadjusted. The 12-month column matches the published annual rates.":
        "El IAPC subyacente deja fuera la energía, los alimentos, el alcohol y el tabaco. Los horizontes de menos de 12 meses "
        "están anualizados y usan la desestacionalización de Macroscope, porque Eurostat publica estos índices sin "
        "desestacionalizar. La columna de 12 meses coincide con las tasas anuales publicadas.",
    "HICP inflation, % change on a year earlier": "Inflación del IAPC, variación interanual, %",
    "HICP, % change on a year earlier": "IAPC, variación interanual, %",
    "Core inflation: Spain and the euro area": "Inflación subyacente: España y la zona del euro",
    "Core HICP, % change on a year earlier": "IAPC subyacente, variación interanual, %",
    "Inside core inflation": "Dentro de la inflación subyacente",
    # underlying inflation
    "Headline and underlying inflation": "Inflación general y subyacente",
    "A few big price moves, like energy, can push headline inflation around. These measures look at the whole spread of price changes across about 180 detailed items of the harmonised basket: the weighted median is the rate half the basket is rising faster than, and the trimmed means average what is left after dropping the most extreme rises and falls. Macroscope calculation from Eurostat data, following the method the ECB uses for the euro area.":
        "Unos pocos movimientos grandes de precios, como los de la energía, pueden zarandear la inflación general. Estas "
        "medidas miran toda la distribución de las variaciones de precios en unas 180 partidas detalladas de la cesta "
        "armonizada: la mediana ponderada es la tasa por encima de la cual sube la mitad de la cesta, y las medias recortadas "
        "promedian lo que queda tras quitar las subidas y bajadas más extremas. Cálculo de Macroscope con datos de Eurostat, "
        "con el método que usa el BCE para la zona del euro.",
    "Headline HICP, {month}": "IAPC general, {month}",
    "Weighted median": "Mediana ponderada",
    "half the basket is rising faster than this": "la mitad de la cesta sube más que esto",
    "Trimmed mean, 30%": "Media recortada, 30%",
    "Trimmed mean 30%": "Media recortada 30%",
    "Trimmed mean, 10%": "Media recortada, 10%",
    "average without the 15% extremes at each end": "media sin el 15% de los extremos de cada lado",
    "Basket rising faster than 2%": "Cesta que sube más del 2%",
    "Basket rising faster than 5%": "Cesta que sube más del 5%",
    "share of spending, by weight": "parte del gasto, por ponderación",
    "Headline inflation ({headline}) is close to the weighted median ({median}): price rises are spread fairly evenly across the basket.":
        "La inflación general ({headline}) está cerca de la mediana ponderada ({median}): las subidas de precios se reparten "
        "de forma bastante uniforme en la cesta.",
    "Headline inflation ({headline}) is {gap} points above the weighted median ({median}): a few items rising very fast are moving the average more than the typical price change.":
        "La inflación general ({headline}) está {gap} puntos por encima de la mediana ponderada ({median}): unas pocas "
        "partidas que suben muy deprisa mueven la media más que la variación típica de los precios.",
    "Headline inflation ({headline}) is {gap} points below the weighted median ({median}): a few items falling sharply are moving the average more than the typical price change.":
        "La inflación general ({headline}) está {gap} puntos por debajo de la mediana ponderada ({median}): unas pocas "
        "partidas que caen con fuerza mueven la media más que la variación típica de los precios.",
    "Measure": "Medida",
    "Above 2%": "Por encima del 2%",
    "Above 5%": "Por encima del 5%",
    "Each item's annual rate is weighted by its share of household spending that year. The 10% trimmed mean drops 5% of the basket at each end of the distribution, the 30% one drops 15%. Run on euro-area data, the trimmed means match the ECB's own within about 0.05 points on average (2018–2025) and the median within about 0.15; the ECB's series stopped in December 2025. Detailed items start in 2015 for Spain and 2017 for the euro area.":
        "La tasa anual de cada partida se pondera por su peso en el gasto de los hogares de ese año. La media recortada al "
        "10% quita el 5% de la cesta en cada extremo de la distribución; la del 30%, el 15%. Con datos de la zona del euro, "
        "las medias recortadas coinciden con las del propio BCE con una diferencia media de unos 0.05 puntos (2018–2025) y "
        "la mediana, de unos 0.15; las series del BCE se interrumpieron en diciembre de 2025. Las partidas detalladas empiezan "
        "en 2015 para España y en 2017 para la zona del euro.",
    "How price rises are spread across the basket": "Cómo se reparten las subidas de precios en la cesta",
    "Share of the HICP basket, by weight, in each band of annual inflation (%)":
        "Parte de la cesta del IAPC, por ponderación, en cada tramo de inflación anual (%)",
    "Annual inflation, %": "Inflación anual, %",
    "Share of the basket": "Parte de la cesta",
    "How widespread are price rises?": "¿Cuán extendidas están las subidas de precios?",
    "How widespread": "Cuán extendidas",
    "Share of the HICP basket, by weight, with annual inflation above 2% and above 5%":
        "Parte de la cesta del IAPC, por ponderación, con inflación anual por encima del 2% y del 5%",
    "Weighted median: Spain and the euro area": "Mediana ponderada: España y la zona del euro",
    "Rising fastest and slowest · {month}": "Las que más y menos suben · {month}",
    "Annual rate": "Tasa anual",
    "Share of basket": "Peso en la cesta",
    "Rising fastest": "Las que más suben",
    "Rising slowest or falling": "Las que menos suben o bajan",
    "Among the {items} detailed items with data, those with at least 0.2% of the basket. Eurostat's item names.":
        "Entre las {items} partidas detalladas con datos, las que pesan al menos un 0.2% de la cesta. Nombres de las "
        "partidas traducidos de los de Eurostat.",
    # Eurostat's detailed items (the ones shown change from month to month; the build lists new ones)
    "Liquid fuels": "Combustibles líquidos",
    "Diesel": "Gasóleo",
    "Petrol": "Gasolina",
    "Purchase of jewellery and watches": "Compra de joyería y relojería",
    "Fruit-bearing vegetables, fresh or chilled": "Hortalizas de fruto, frescas o refrigeradas",
    "Passenger transport by train": "Transporte de pasajeros por ferrocarril",
    "Coffee and coffee substitutes": "Café y sucedáneos",
    "Equipment for the reception, recording and reproduction of sound and vision": "Equipos de recepción, grabación y reproducción de imagen y sonido",
    "Passenger transport by air, international": "Transporte aéreo internacional de pasajeros",
    "Chocolate, cocoa and cocoa-based food products": "Chocolate, cacao y productos a base de cacao",
    # producer prices, energy and expectations
    "Producer and consumer prices": "Precios de producción y de consumo",
    "Energy costs reach consumer prices quickly, and households' expectations feed into wage bargaining. Petrol and diesel are each Monday's average pump price, from the European Commission's Weekly Oil Bulletin; before taxes means before the hydrocarbons duty and VAT.":
        "Los costes de la energía llegan pronto a los precios de consumo, y las expectativas de los hogares influyen en la "
        "negociación salarial. La gasolina y el gasóleo son el precio medio en surtidor de cada lunes, del Boletín "
        "Petrolero semanal de la Comisión Europea; antes de impuestos quiere decir antes del impuesto sobre hidrocarburos y "
        "el IVA.",
    "Producer prices, domestic market": "Precios industriales, mercado interior",
    "Wholesale": "Mayoristas",
    "Electricity, day-ahead market": "Electricidad, mercado diario",
    "Electricity price": "Precio de la electricidad",
    "Day-ahead market, daily average, €/MWh": "Mercado diario, media del día, €/MWh",
    "Day-ahead price": "Precio del mercado diario",
    "European natural gas": "Gas natural europeo",
    "Brent crude in euros": "Petróleo Brent en euros",
    "At the pump, € a litre": "En surtidor, € por litro",
    "Petrol (Euro-super 95)": "Gasolina (Eurosúper 95)",
    "Petrol before taxes": "Gasolina antes de impuestos",
    "Diesel before taxes": "Gasóleo antes de impuestos",
    "Petrol, euro area": "Gasolina, zona del euro",
    "Diesel, euro area": "Gasóleo, zona del euro",
    "Petrol, Spain": "Gasolina, España",
    "Diesel, Spain": "Gasóleo, España",
    "Petrol pre-tax": "Gasolina sin impuestos",
    "Diesel pre-tax": "Gasóleo sin impuestos",
    "Expectations": "Expectativas",
    "Consumers' price expectations (balance)": "Expectativas de precios de los consumidores (saldo)",
    "Balance": "Saldo",
    "{change}% on a year earlier": "{change}% interanual",
    "€{price} a litre": "{price} € el litro",
    "Taxes in the pump price": "Impuestos en el precio del surtidor",
    "of petrol's": "del de la gasolina",
    "; {share}% of diesel's": "; {share}% del del gasóleo",
    "Against the euro area": "Frente a la zona del euro",
    "petrol in Spain against the euro-area average": "la gasolina en España frente a la media de la zona del euro",
    "; diesel {gap}%": "; gasóleo {gap}%",
    "Petrol and diesel at the pump": "Gasolina y gasóleo en el surtidor",
    "Spain, average price on Mondays, € a litre; dashed, before taxes": "España, precio medio de los lunes, € por litro; a trazos, antes de impuestos",
    "Pump prices: Spain and the euro area": "Precios en surtidor: España y la zona del euro",
    "Average price on Mondays, taxes included, € a litre; dotted, the euro area":
        "Precio medio de los lunes, impuestos incluidos, € por litro; en punteado, la zona del euro",
    "Price expectations": "Expectativas de precios",
    "Households expecting faster price rises over the next 12 months, net balance":
        "Hogares que esperan subidas de precios más rápidas en los próximos 12 meses, saldo neto",
})

# ---------------------------------------------------------------- Financial
PAIRS.update({
    "%": "%",
    "{date}": "{date}",
    "A month earlier": "Un mes antes",
    "End-{prev_year}": "Final de {prev_year}",
    "Market": "Mercado",
    "Latest close; rates move in basis points (bp), prices in %": "Último cierre; los tipos se mueven en puntos básicos (pb), los precios en %",
    "The latest close and how far each market has moved. Yields come from Banco de España, exchange rates are the ECB's daily reference rates and Brent is the US EIA spot price (via FRED).":
        "El último cierre y cuánto se ha movido cada mercado. Las rentabilidades proceden del Banco de España, los tipos de "
        "cambio son los tipos de referencia diarios del BCE y el Brent es el precio al contado de la EIA estadounidense (a "
        "través de FRED).",
    "Each row is the latest close its source has published; a date next to a row means it differs from the rest. Monthly rows are monthly averages. For the euro, a rise means a stronger euro.":
        "Cada fila es el último cierre que ha publicado su fuente; una fecha junto a una fila indica que difiere del resto. "
        "Las filas mensuales son medias mensuales. Para el euro, una subida significa un euro más fuerte.",
    "Bonds and rates": "Bonos y tipos",
    "Spain 10-year yield": "Rentabilidad del bono a 10 años de España",
    "Germany 10-year yield": "Rentabilidad del bono a 10 años de Alemania",
    "Prima de riesgo, 10-year": "Prima de riesgo, 10 años",
    "Prima de riesgo": "Prima de riesgo",
    "12-month Euribor": "Euríbor a 12 meses",
    "3-month Euribor": "Euríbor a 3 meses",
    "ECB deposit rate": "Tipo de depósito del BCE",
    "IBEX 35": "IBEX 35",
    "Euro Stoxx 50 (monthly average)": "Euro Stoxx 50 (media mensual)",
    "The euro, per euro": "El euro, por euro",
    "US dollars": "Dólares estadounidenses",
    "British pounds": "Libras esterlinas",
    "Swiss francs": "Francos suizos",
    "Japanese yen": "Yenes japoneses",
    "Energy and metals": "Energía y metales",
    "Brent crude": "Petróleo Brent",
    "Electricity, day-ahead": "Electricidad, mercado diario",
    "European natural gas (monthly)": "Gas natural europeo (mensual)",
    "Gold (monthly)": "Oro (mensual)",
    "Copper (monthly)": "Cobre (mensual)",
    "Index, daily close": "Índice, cierre diario",
    "The euro against the dollar": "El euro frente al dólar",
    "US dollars per euro, daily": "Dólares por euro, diario",
    "EUR/USD": "EUR/USD",
    "Brent crude, dollars": "Petróleo Brent, dólares",
    "Brent crude, euros": "Petróleo Brent, euros",
    "Price per barrel, in dollars and in euros, daily": "Precio por barril, en dólares y en euros, diario",
    "Dollars": "Dólares",
    "Euros": "Euros",
    # government bonds
    "Spanish government bonds": "Deuda pública española",
    "What the Spanish state pays to borrow at each maturity, and the extra it pays over the safest euro-area governments. The prima de riesgo is the gap with Germany at 10 years.":
        "Lo que paga el Estado español por endeudarse a cada plazo, y lo que paga de más frente a los gobiernos más seguros "
        "de la zona del euro. La prima de riesgo es la diferencia con Alemania a 10 años.",
    "Yield, %; changes and the spread over AAA euro-area bonds in basis points":
        "Rentabilidad, %; variaciones y diferencial sobre la deuda AAA de la zona del euro en puntos básicos",
    "Maturity": "Plazo",
    "Over AAA": "Sobre AAA",
    "Over Germany": "Sobre Alemania",
    "12-month Treasury bill": "Letra del Tesoro a 12 meses",
    "12-month bill": "Letra a 12 meses",
    "3-year": "3 años",
    "5-year": "5 años",
    "10-year": "10 años",
    "15-year": "15 años",
    "30-year": "30 años",
    "AAA yields are the ECB's estimate of the curve for AAA-rated euro-area governments, the closest thing to a risk-free euro rate. Banco de España's prima de riesgo uses benchmark bonds, so it differs a little from Spain's 10-year yield minus Germany's.":
        "Las rentabilidades AAA son la estimación del BCE de la curva de los gobiernos de la zona del euro con calificación "
        "AAA, lo más parecido a un tipo del euro sin riesgo. La prima de riesgo del Banco de España usa bonos de referencia, "
        "así que difiere algo de la rentabilidad a 10 años de España menos la de Alemania.",
    "Spanish yield curve": "Curva de tipos española",
    "Yield by maturity, %": "Rentabilidad por plazo, %",
    "Spain and the safest euro-area bonds": "España y los bonos más seguros de la zona del euro",
    "Yield by maturity, %: Spain against the AAA euro-area curve": "Rentabilidad por plazo, %: España frente a la curva AAA de la zona del euro",
    "Euro area AAA": "Zona del euro AAA",
    "10-year yields: Spain and Germany": "Rentabilidades a 10 años: España y Alemania",
    "Prima de riesgo since 2008": "La prima de riesgo desde 2008",
    "Spain's 10-year yield over Germany's, basis points, daily; it peaked at 636 bp in July 2012":
        "Rentabilidad a 10 años de España sobre la de Alemania, puntos básicos, diario; tocó máximo en 636 pb en julio de 2012",
    # Euribor and mortgages
    "Euribor and mortgage rates": "Euríbor y tipos hipotecarios",
    "Most Spanish mortgages are variable-rate: once or twice a year the payment resets to the 12-month Euribor plus a fixed margin, so ECB decisions reach households quickly.":
        "La mayoría de las hipotecas españolas son a tipo variable: una o dos veces al año la cuota se revisa al euríbor a 12 "
        "meses más un diferencial fijo, así que las decisiones del BCE llegan pronto a los hogares.",
    "New mortgages, average rate": "Hipotecas nuevas, tipo medio",
    "New mortgages": "Hipotecas nuevas",
    "The mortgage rate is the ECB's average for new house-purchase loans to Spanish households.":
        "El tipo hipotecario es la media del BCE para los préstamos nuevos para compra de vivienda a hogares españoles.",
    "%: 12-month Euribor (daily) and the average rate on new mortgages (monthly)":
        "%: euríbor a 12 meses (diario) y tipo medio de las hipotecas nuevas (mensual)",
    "Euribor and the ECB": "El euríbor y el BCE",
    "%: Euribor follows the ECB's deposit rate and where markets expect it to go":
        "%: el euríbor sigue al tipo de depósito del BCE y a dónde esperan los mercados que vaya",
    "Mortgage check: a €{principal}, {years}-year variable-rate mortgage at Euribor + {margin} pp, reset at {month}'s average 12-month Euribor ({now}%{so_far}), costs €{payment} a month: {change} a reset at the rate a year earlier ({then}%).":
        "Prueba hipotecaria: una hipoteca de {principal} € a {years} años a tipo variable, euríbor + {margin} pp, revisada "
        "al euríbor a 12 meses medio de {month} ({now}%{so_far}), cuesta {payment} € al mes: {change} una revisión al tipo "
        "de hace un año ({then}%).",
    " so far, to {day}": " por ahora, hasta el {day}",
    "the same as": "lo mismo que",
    "€{amount} more than": "{amount} € más que",
    "€{amount} less than": "{amount} € menos que",
    # financial stress
    "Financial stress": "Tensión financiera",
    "The ECB's composite indicator of systemic stress (CISS) combines tension in money, bond, share and currency markets and among banks into one number, from 0 (calm) to 1 (crisis). The bad-loan ratio shows how much bank lending is not being repaid.":
        "El indicador compuesto de tensión sistémica del BCE (CISS) combina la tensión en los mercados monetario, de bonos, "
        "de acciones y de divisas y entre los bancos en un solo número, de 0 (calma) a 1 (crisis). La tasa de morosidad "
        "muestra cuánto del crédito bancario no se está devolviendo.",
    "Index (0 to 1) or %": "Índice (de 0 a 1) o %",
    "Financial stress, Spain": "Tensión financiera, España",
    "Financial stress, euro area": "Tensión financiera, zona del euro",
    "Bad-loan ratio": "Tasa de morosidad",
    "ECB composite indicator of systemic stress, 0 to 1, daily": "Indicador compuesto de tensión sistémica del BCE, de 0 a 1, diario",
    "Bad loans": "Morosidad",
    "Bad-loan ratio, %": "Tasa de morosidad, %",
    "Doubtful loans, % of lending to households and firms": "Créditos dudosos, % del crédito a hogares y empresas",
    "Table 3 of the IMF's 2026 Article IV report for Spain: bank capital, asset quality and profitability from the IMF's own Financial Soundness Indicators database, banks' domestic exposures from the Banco de España, and corporate, household and housing indicators.":
        "El cuadro 3 del informe del Artículo IV de 2026 del FMI sobre España: capital, calidad de los activos y rentabilidad "
        "de los bancos de la base de datos de indicadores de solidez financiera del propio FMI, las exposiciones domésticas "
        "de los bancos del Banco de España, e indicadores de empresas, hogares y vivienda.",
})
