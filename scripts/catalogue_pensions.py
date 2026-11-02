"""Spanish for the Pensions page (Batch 33c-2): the blocks, tables and charts of econpulse/pages.py "pensions", and
the facts, charts, comparison table and document cards written by econpulse/pensions.py. The Social Security's own
terms: pensiones contributivas, jubilación, incapacidad permanente, viudedad, orfandad, Régimen General, altas y
bajas, revalorización, cotización de solidaridad, Mecanismo de Equidad Intergeneracional (MEI), tasa de sustitución.
Country names (and "EU") are in scripts/catalogue_international.py. Read by scripts/write_catalogue.py; the keys
are the English exactly as the code writes it.
"""

PAIRS: dict[str, str] = {}

# ---------------------------------------------------------------- Pensions today (pages.py, pensions.py)
PAIRS.update({
    "The Social Security's contributory pensions: paid for by contributions and earned by working, for retirement, widowhood, permanent disability, orphans and family members. Non-contributory pensions, for people who paid in too little, and civil servants' pensions (Clases Pasivas) are not included.":
        "Las pensiones contributivas de la Seguridad Social: se financian con cotizaciones y se generan trabajando, "
        "por jubilación, viudedad, incapacidad permanente, orfandad y en favor de familiares. No se incluyen las "
        "pensiones no contributivas, para quienes cotizaron demasiado poco, ni las de los funcionarios (Clases Pasivas).",
    # the classes (pensions.CLASSES) and the class table
    "All pensions": "Todas las pensiones",
    "Retirement": "Jubilación",
    "Widowhood": "Viudedad",
    "Permanent disability": "Incapacidad permanente",
    "Disability": "Incapacidad permanente",
    "Orphans": "Orfandad",
    "Class": "Clase",
    "Pensions in force on the first of the month": "Pensiones en vigor el día 1 de cada mes",
    "Pensions, thousands": "Pensiones, miles",
    "Average, € a month": "Media, € al mes",
    "Widowhood pensions go mostly to women; family-support pensions, under 50,000, are counted in the total but not shown. Source: Ministry of Labour, Boletín de Estadísticas Laborales (table PEN-1), from Social Security records.":
        "Las pensiones de viudedad las cobran sobre todo mujeres; las pensiones en favor de familiares, menos de "
        "50,000, se cuentan en el total pero no se muestran. Fuente: Ministerio de Trabajo, Boletín de Estadísticas "
        "Laborales (cuadro PEN-1), a partir de los registros de la Seguridad Social.",
    # the facts
    "Contributory pensions": "Pensiones contributivas",
    "{n} million": "{n} millones",
    "on the 1st of {month}": "a 1 de {month}",
    "Average pension": "Pensión media",
    "a month, {month}": "al mes, {month}",
    "; retirement {amount}": "; jubilación {amount}",
    "What they cost": "Lo que cuestan",
    "in {year}, an estimate: pensions × the average pension × {payments} payments":
        "en {year}, estimación: número de pensiones × pensión media × {payments} pagas",
    "Workers per pension": "Afiliados por pensión",
    "registered with the Social Security, {period}": "trabajadores en alta en la Seguridad Social, {period}",
    "; {ratio} in {year}": "; {ratio} en {year}",
    # the charts
    "Average pension by class": "Pensión media por clase",
    "€ a month, annual averages": "€ al mes, medias anuales",
    "The average pension and prices": "La pensión media y los precios",
    "Average pension, annual average, {year} = 100: as paid, and after consumer prices":
        "Pensión media, media anual, {year} = 100: nominal y descontados los precios de consumo",
    "As paid": "Nominal",
    "{source}, INE; Macroscope calculation": "{source}, INE; cálculo de Macroscope",
    "What contributory pensions cost": "Lo que cuestan las pensiones contributivas",
    "% of GDP, an estimate: pensions × the average pension × {payments} payments":
        "% del PIB, estimación: número de pensiones × pensión media × {payments} pagas",
    "{source}, Eurostat; Macroscope calculation": "{source}, Eurostat; cálculo de Macroscope",
    "Registered workers per contributory pension, annual averages":
        "Afiliados a la Seguridad Social por pensión contributiva, medias anuales",
    "Seguridad Social, {source}; Macroscope calculation": "Seguridad Social, {source}; cálculo de Macroscope",
})

# ---------------------------------------------------------------- new and ended pensions (altas y bajas)
PAIRS.update({
    "Each month new pensions are granted and others end, mostly on the pensioner's death. New retirement pensions, earned on higher pay, are larger than those that end, so the average pension rises faster than pensions are revalued.":
        "Cada mes se reconocen pensiones nuevas y otras causan baja, sobre todo por fallecimiento del pensionista. Las "
        "nuevas pensiones de jubilación, generadas con salarios más altos, son mayores que las que causan baja, por lo "
        "que la pensión media sube más deprisa que la revalorización de las pensiones.",
    "A new retirement pension": "Una pensión de jubilación nueva",
    "a month, granted in {month}": "al mes, reconocida en {month}",
    "a month, granted in {month} · {change} on the average retirement pension":
        "al mes, reconocida en {month} · {change} sobre la pensión media de jubilación",
    "A retirement pension that ends": "Una pensión de jubilación que causa baja",
    "a month, {month}: newer pensions replace smaller ones":
        "al mes, {month}: las pensiones nuevas sustituyen a otras más bajas",
    "Pensions granted": "Altas de pensiones",
    "Pensions ended": "Bajas de pensiones",
    "past 12 months, to {month}": "últimos 12 meses, hasta {month}",
    "Latest month; changes in %": "Último mes; variaciones en %",
    "Pensions granted, thousands": "Altas de pensiones, miles",
    "Pensions ended, thousands": "Bajas de pensiones, miles",
    "Average amount, € a month": "Importe medio, € al mes",
    "New pensions": "Pensiones nuevas",
    "New retirement pensions": "Pensiones de jubilación nuevas",
    "Retirement pensions that ended": "Pensiones de jubilación que causaron baja",
    "All retirement pensions in force": "Todas las pensiones de jubilación en vigor",
    "Granted and ended in the month (tables PEN-10 and PEN-11); the monthly figures start in March and April 2025, so year-to-date changes appear from 2027.":
        "Altas y bajas del mes (cuadros PEN-10 y PEN-11); las cifras mensuales empiezan en marzo y abril de 2025, así "
        "que las variaciones en lo que va de año aparecen a partir de 2027.",
    "New, ended and all retirement pensions": "Pensiones de jubilación: nuevas, bajas y todas las vigentes",
    "Average amount, € a month, annual": "Importe medio, € al mes, anual",
    "New": "Nuevas",
    "All in force": "Todas las vigentes",
    "Ended": "Bajas",
    "Pensions granted and ended": "Altas y bajas de pensiones",
    "Thousands a year": "Miles al año",
    "Granted": "Altas",
})

# ---------------------------------------------------------------- by scheme (régimen) and by region
PAIRS.update({
    "Pensions by the Social Security scheme the pensioner paid into: employees in the General scheme, the self-employed, and the smaller special schemes.":
        "Las pensiones según el régimen de la Seguridad Social en el que cotizó el pensionista: los asalariados del "
        "Régimen General, los autónomos y los regímenes especiales más pequeños.",
    "General scheme": "Régimen General",
    "Sea workers": "Trabajadores del Mar",
    "Coal mining": "Minería del Carbón",
    "Work accidents": "Accidentes de trabajo",
    "Occupational diseases": "Enfermedades profesionales",
    "SOVI (pre-1967 old-age insurance)": "SOVI (seguro de vejez anterior a 1967)",
    "Scheme": "Régimen",
    "Schemes (regímenes) group workers by how they paid in. Farm workers and domestic employees joined the General scheme in 2012. Pensions for work accidents and occupational diseases are counted apart from the scheme the worker belonged to. SOVI pays the old-age insurance in force before 1967 (table PEN-2).":
        "Los regímenes agrupan a los trabajadores según cómo cotizaron. Los trabajadores agrarios y los empleados de "
        "hogar se integraron en el Régimen General en 2012. Las pensiones por accidentes de trabajo y enfermedades "
        "profesionales se cuentan aparte del régimen al que pertenecía el trabajador. El SOVI (Seguro Obligatorio de "
        "Vejez e Invalidez) paga el seguro de vejez vigente antes de 1967 (cuadro PEN-2).",
    "Average pension by scheme": "Pensión media por régimen",
    "Pensions and average pensions in each autonomous community, where the pensioner lives.":
        "Número de pensiones y pensión media en cada comunidad autónoma, según dónde vive el pensionista.",
    "Ceuta y Melilla": "Ceuta y Melilla",
    "Average retirement, € a month": "Pensión media de jubilación, € al mes",
    "Where the pensioner lives. Average pensions follow past pay: highest in the País Vasco, Asturias and Madrid, lowest in Extremadura and Galicia (tables PEN-19, PEN-20 and PEN-24).":
        "Según dónde vive el pensionista. Las pensiones medias siguen a los salarios del pasado: son más altas en el "
        "País Vasco, Asturias y Madrid y más bajas en Extremadura y Galicia (cuadros PEN-19, PEN-20 y PEN-24).",
    "Average pension by region": "Pensión media por comunidades",
    "Average retirement pension by region": "Pensión media de jubilación por comunidades",
})

# ---------------------------------------------------------------- maximum and minimum pensions
PAIRS.update({
    "No contributory pension can exceed the maximum, whatever was paid in; pensioners with little other income are topped up to the minimum. Both are set every year in the budget.":
        "Ninguna pensión contributiva puede superar la pensión máxima, se haya cotizado lo que se haya cotizado; a los "
        "pensionistas con pocos ingresos más se les complementa la pensión hasta la mínima. Ambas cuantías se fijan "
        "cada año en los Presupuestos Generales del Estado.",
    "Maximum pension": "Pensión máxima",
    "Minimum, with a dependent spouse": "Mínima, con cónyuge a cargo",
    "Minimum, living alone": "Mínima, sin cónyuge",
    "a month": "al mes",
    "a month, retirement at 65": "al mes, jubilación a los 65 años",
    "Amount": "Cuantía",
    "€ a month, of 14 payments a year": "€ al mes, en 14 pagas al año",
    "This year": "Este año",
    "A year earlier": "Un año antes",
    "Change, %": "Variación, %",
    "Minimum retirement pension at 65: with a dependent spouse":
        "Pensión mínima de jubilación a los 65 años: con cónyuge a cargo",
    "Living alone": "Sin cónyuge (unidad económica unipersonal)",
    "With a spouse who is not dependent": "Con cónyuge no a cargo",
    "Set each year in the budget and published a year (table PEN-31); shown here over the 14 payments. Pensions below the minimum are topped up (complemento a mínimos) for pensioners whose other income is low.":
        "Se fijan cada año en los Presupuestos y se publican en cómputo anual (cuadro PEN-31); aquí se muestran "
        "divididas entre las 14 pagas. Las pensiones por debajo de la mínima se completan (complemento a mínimos) "
        "cuando el pensionista tiene pocos ingresos más.",
    "Maximum": "Máxima",
    "Minimum, dependent spouse": "Mínima, con cónyuge a cargo",
})

# ---------------------------------------------------------------- against other countries
PAIRS.update({
    "What Spain spends on pensions and how generous they are, next to its comparators: spending from Eurostat (EU countries, all pensions) and the OECD (every comparator, public old-age and survivors' pensions), and the OECD's replacement rates. The chips choose the countries drawn beside Spain.":
        "Lo que España gasta en pensiones y lo generosas que son, junto a sus comparables: el gasto según Eurostat "
        "(países de la UE, todas las pensiones) y la OCDE (todos los comparables, pensiones públicas de jubilación y "
        "supervivencia), y las tasas de sustitución de la OCDE. Los botones eligen los países que se dibujan junto a "
        "España.",
    # the facts
    "Pension spending": "Gasto en pensiones",
    "all pensions, {year}; EU {eu} (Eurostat)": "todas las pensiones, {year}; UE {eu} (Eurostat)",
    "all pensions, {year} (Eurostat)": "todas las pensiones, {year} (Eurostat)",
    "Replacement rate": "Tasa de sustitución",
    "of net pay, for an average earner (OECD, {year}); {rank}":
        "del salario neto, para un trabajador con el salario medio (OCDE, {year}); {rank}",
    "the highest of the {n} countries": "la más alta de los {n} países",
    "the second highest of the {n} countries": "la segunda más alta de los {n} países",
    "the third highest of the {n} countries": "la tercera más alta de los {n} países",
    "the fourth highest of the {n} countries": "la cuarta más alta de los {n} países",
    "the fifth highest of the {n} countries": "la quinta más alta de los {n} países",
    "the {rank}th highest of the {n} countries": "la {rank}.ª más alta de los {n} países",
    "Social security funds' balance": "Saldo de las Administraciones de Seguridad Social",
    "{year}; EU {eu} (Eurostat)": "{year}; UE {eu} (Eurostat)",
    # the table
    "Country": "País",
    "Pensions and ageing": "Pensiones y envejecimiento",
    "Pension spending, % of GDP": "Gasto en pensiones, % del PIB",
    "Public pensions, % of GDP": "Pensiones públicas, % del PIB",
    "Replacement rate, %": "Tasa de sustitución, %",
    "65+ per 100 aged 15-64": "65+ por cada 100 de 15-64 años",
    "Same, 2050": "Ídem, 2050",
    "OECD, {year}": "OCDE, {year}",
    "OECD, net": "OCDE, neta",
    "projected": "proyección",
    "Pension spending (Eurostat) covers all pensions, public and private, including disability; public pensions (OECD) cover public old-age and survivors' pensions only, and come a few years late. The replacement rate is what a man on the average wage who starts work at 22 would get from mandatory schemes, as % of his net pay before retiring. Eurostat covers EU countries only.":
        "El gasto en pensiones (Eurostat) abarca todas las pensiones, públicas y privadas, incluidas las de "
        "incapacidad; las pensiones públicas (OCDE) solo cubren las pensiones públicas de jubilación y supervivencia, y "
        "llegan con unos años de retraso. La tasa de sustitución es lo que cobraría de los sistemas obligatorios un "
        "hombre con el salario medio que empieza a trabajar a los 22 años, en % de su salario neto antes de jubilarse. "
        "Eurostat solo cubre los países de la UE.",
    # the charts
    "Pension replacement rates": "Tasas de sustitución de las pensiones",
    "Net, for an average earner, % of net pay": "Neta, para un trabajador con el salario medio, % del salario neto",
    "OECD, Pensions at a Glance": "OCDE, Pensions at a Glance",
    "Public spending on pensions": "Gasto público en pensiones",
    "Old-age and survivors' pensions, % of GDP": "Pensiones de jubilación y supervivencia, % del PIB",
    "Old-age and survivors' pensions, % of GDP, latest year ({first}-{last})":
        "Pensiones de jubilación y supervivencia, % del PIB, último año disponible ({first}-{last})",
    "OECD, Social Expenditure Database": "OCDE, base de datos de gasto social (SOCX)",
    "Old-age and survivors' pensions, % of GDP (OECD)": "Pensiones de jubilación y supervivencia, % del PIB (OCDE)",
    "Pension spending in Spain and the EU": "Gasto en pensiones en España y la UE",
    "All pensions, % of GDP (Eurostat)": "Todas las pensiones, % del PIB (Eurostat)",
})

# ---------------------------------------------------------------- an ageing population (tasa de dependencia)
PAIRS.update({
    "Pensions are paid from the contributions of those at work, so the balance between older people and people of working age weighs on them. Spain's will shift faster than most of Europe's as the large generations born in the 1960s and 1970s retire.":
        "Las pensiones se pagan con las cotizaciones de quienes trabajan, así que el equilibrio entre las personas "
        "mayores y las que están en edad de trabajar pesa sobre ellas. En España cambiará más deprisa que en la mayor "
        "parte de Europa a medida que se jubilen las numerosas generaciones nacidas en los años sesenta y setenta.",
    "People 65+ per 100 aged 15-64": "Personas de 65 años o más por cada 100 de 15-64",
    "{year}; EU {eu}": "{year}; UE {eu}",
    "In 2050, projected": "En 2050, proyección",
    "Eurostat's baseline": "escenario central de Eurostat",
    "Eurostat's baseline; EU {eu}": "escenario central de Eurostat; UE {eu}",
    "Old-age dependency ratio": "Tasa de dependencia de las personas mayores",
    "People aged 65 and over per 100 aged 15-64; dotted, Eurostat's projection":
        "Personas de 65 años o más por cada 100 de 15 a 64 años; en punteado, la proyección de Eurostat",
    "{name}, projected": "{name}, proyección",
    "Eurostat (EUROPOP2023 projections)": "Eurostat (proyecciones EUROPOP2023)",
    "Old-age dependency in 2050": "Tasa de dependencia en 2050",
    "65+ per 100 aged 15-64, projected": "65+ por cada 100 de 15-64 años, proyección",
})

# ---------------------------------------------------------------- the 2023 reform and the official assessments
PAIRS.update({
    "The reform of March 2023 added revenue rather than cutting pensions: a growing earmarked contribution (the MEI) that feeds the reserve fund, a higher maximum contribution base, a new solidarity contribution on pay above it, and a spending rule that AIReF checks every three years. Its figures are entered by hand from the decree in the Boletín Oficial del Estado.":
        "La reforma de marzo de 2023 añadió ingresos en lugar de recortar pensiones: una cotización finalista "
        "creciente (el MEI) que nutre el Fondo de Reserva, una base máxima de cotización más alta, una nueva "
        "cotización de solidaridad sobre el salario que la supera y una regla de gasto que la AIReF evalúa cada tres "
        "años. Sus cifras se introducen a mano a partir del decreto publicado en el Boletín Oficial del Estado.",
    "The intergenerational equity contribution (MEI)": "El Mecanismo de Equidad Intergeneracional (MEI)",
    "Points of pay, employer and worker together; 1.2 from 2029 to 2050":
        "Puntos porcentuales de cotización, empresa y trabajador juntos; 1.2 de 2029 a 2050",
    "MEI": "MEI",
    "Real Decreto-ley 2/2023, entered by hand": "Real Decreto-ley 2/2023, datos introducidos a mano",
    "The solidarity contribution": "La cotización de solidaridad",
    "% of pay above the maximum contribution base, by band":
        "% del salario que supera la base máxima de cotización, por tramos",
    "Up to 10% above the base": "Hasta un 10% por encima de la base",
    "10-50% above": "Entre un 10% y un 50% por encima",
    "Over 50% above": "Más de un 50% por encima",
    "The European Commission's Ageing Report projects pension spending for every EU country; AIReF, Spain's fiscal watchdog, checks the spending rule; the Banco de España weighs in its annual report. Their figures are entered by hand from each document, linked, and marked until an AI has checked them against the publisher's own text.":
        "El Ageing Report de la Comisión Europea proyecta el gasto en pensiones de cada país de la UE; la AIReF, la "
        "autoridad fiscal independiente de España, evalúa la regla de gasto; el Banco de España opina en su informe "
        "anual. Sus cifras se introducen a mano a partir de cada documento, que se enlaza, y quedan marcadas hasta que "
        "una IA las ha cotejado con el texto de la propia institución.",
    "Projected pension spending": "Proyección del gasto en pensiones",
    "Gross public pension spending, % of GDP, European Commission 2024 Ageing Report":
        "Gasto público bruto en pensiones, % del PIB, Ageing Report 2024 de la Comisión Europea",
    "European Commission, 2024 Ageing Report (Table II.1.64), entered by hand":
        "Comisión Europea, Ageing Report 2024 (cuadro II.1.64), datos introducidos a mano",
    "Net lending (+) or borrowing (−), % of GDP": "Capacidad (+) o necesidad (−) de financiación, % del PIB",
})

# ---------------------------------------------------------------- the document cards (pension_assessments.yaml,
# data/pension_checks.json): the site's own words. The documents' titles stay as published; the one title the site
# added words to is translated in those words only (pensions._card uses i18n.maybe for titles).
PAIRS.update({
    "AI-checked": "verificado por IA",
    "Checked by {by} on {date} against {against}.": "Verificado el {date} por {by}, cotejado con {against}.",
    "Checked by {by} on {date}.": "Verificado el {date} por {by}.",
    "AI check (Claude)": "una IA (Claude)",
    "the BOE text of Real Decreto-ley 2/2023 (BOE-A-2023-6967), read independently":
        "el texto del Real Decreto-ley 2/2023 en el BOE (BOE-A-2023-6967), leído de forma independiente",
    "the Commission's PDF (Institutional Paper 279, April 2024): Tables 1, I.1.6, I.1.9, II.1.64 and the country table for Spain":
        "el PDF de la Comisión (Institutional Paper 279, abril de 2024): cuadros 1, I.1.6, I.1.9 y II.1.64 y el "
        "cuadro de España",
    "AIReF's PDF of 31 March 2025 (Informe 2/25)": "el PDF de la AIReF del 31 de marzo de 2025 (Informe 2/25)",
    "AIReF's PDF of 29 May 2026 (Estudio 1/2026)": "el PDF de la AIReF del 29 de mayo de 2026 (Estudio 1/2026)",
    "the Banco de España's PDF of chapter 2 of its 2023 Annual Report":
        "el PDF del capítulo 2 del Informe Anual 2023 del Banco de España",
    "The chapter prints no date; 2024 comes from the PDF's creation date (30 April 2024) and its latest references.":
        "El capítulo no lleva fecha; 2024 sale de la fecha de creación del PDF (30 de abril de 2024) y de sus "
        "referencias más recientes.",
    # publishers and short titles
    "Government of Spain": "Gobierno de España",
    "The 2023 pension reform": "La reforma de las pensiones de 2023",
    "The 2024 Ageing Report": "El Ageing Report de 2024",
    "AIReF's first check of the spending rule": "Primera evaluación de la regla de gasto por la AIReF",
    "AIReF's follow-up check": "La evaluación de seguimiento de la AIReF",
    "The Banco de España's annual report": "El informe anual del Banco de España",
    "Informe Anual 2023, capítulo 2: Retos estructurales de la economía española (section 9.2, the public pension system)":
        "Informe Anual 2023, capítulo 2: Retos estructurales de la economía española (apartado 9.2, el sistema público "
        "de pensiones)",
})

# The figures, as the site describes them: labels, values (the numbers exactly as in English) and where in the
# document each one is.
PAIRS.update({
    # the 2023 reform (Real Decreto-ley 2/2023)
    "Intergenerational equity contribution (MEI), 2023": "Mecanismo de Equidad Intergeneracional (MEI), 2023",
    "0.6 points of pay (employer 0.5, worker 0.1)": "0.6 puntos de cotización (empresa 0.5, trabajador 0.1)",
    "General Social Security Law, transitional provision 43 (article 1.43 of the decree)":
        "Ley General de la Seguridad Social, disposición transitoria 43.ª (artículo 1.43 del decreto)",
    "MEI from 2029 to 2050": "MEI de 2029 a 2050",
    "1.2 points of pay (employer 1.0, worker 0.2), rising by 0.1 a year from 2023":
        "1.2 puntos de cotización (empresa 1.0, trabajador 0.2), tras subir 0.1 al año desde 2023",
    "transitional provision 43": "disposición transitoria 43.ª",
    "Maximum contribution base, 2024-2050": "Base máxima de cotización, 2024-2050",
    "rises each year by inflation plus 1.2 points": "sube cada año con la inflación más 1.2 puntos",
    "transitional provision 38": "disposición transitoria 38.ª",
    "Solidarity contribution on pay above the maximum base, 2025":
        "Cotización de solidaridad sobre el salario que supera la base máxima, 2025",
    "0.92%, 1% and 1.17% in three bands (up to 10%, 10-50% and over 50% above the base)":
        "0.92%, 1% y 1.17% en tres tramos (hasta un 10%, entre un 10% y un 50% y más de un 50% por encima de la base)",
    "transitional provision 42": "disposición transitoria 42.ª",
    "Solidarity contribution, 2045": "Cotización de solidaridad, 2045",
    "5.5%, 6% and 7% in the same bands": "5.5%, 6% y 7% en los mismos tramos",
    "Maximum pension, 2025-2050": "Pensión máxima, 2025-2050",
    "rises each year by the pensions' revaluation plus 0.115 points":
        "sube cada año con la revalorización de las pensiones más 0.115 puntos",
    "transitional provision 39": "disposición transitoria 39.ª",
    "Minimum retirement pension with a dependent spouse": "Pensión mínima de jubilación con cónyuge a cargo",
    "from 2027 no lower than the poverty threshold for a two-adult household":
        "desde 2027, no inferior al umbral de la pobreza de un hogar de dos adultos",
    "additional provision 53": "disposición adicional 53.ª",
    "Spending rule, checked by AIReF every three years from March 2025":
        "Regla de gasto, evaluada por la AIReF cada tres años desde marzo de 2025",
    "average gross pension spending in 2022-2050 (Ageing Report) at most 15% of GDP, adjusted by the gap between the revenue measures' yield and 1.7% of GDP":
        "gasto bruto medio en pensiones en 2022-2050 (Ageing Report) de como máximo el 15% del PIB, ajustado por la "
        "diferencia entre lo que recauden las medidas de ingresos y el 1.7% del PIB",
    "additional provision 2 of the decree": "disposición adicional 2.ª del decreto",
    # the 2024 Ageing Report
    "Spain's gross public pension spending, 2022": "Gasto público bruto en pensiones de España, 2022",
    "13.1% of GDP": "13.1% del PIB",
    "Table II.1.64; Statistical Annex, country table for Spain": "cuadro II.1.64; anexo estadístico, cuadro de España",
    "Peak, in 2050": "Máximo, en 2050",
    "17.3% of GDP": "17.3% del PIB",
    "16.7% of GDP (EU 11.8%)": "16.7% del PIB (UE 11.8%)",
    "Table I.1.6": "cuadro I.1.6",
    "Balance of the pension system at its lowest, in 2053": "Saldo del sistema de pensiones en su punto más bajo, en 2053",
    "−3.1% of GDP (contributions less spending)": "−3.1% del PIB (cotizaciones menos gasto)",
    "Table I.1.9": "cuadro I.1.9",
    "Age-related spending (pensions, health, long-term care, education)":
        "Gasto ligado al envejecimiento (pensiones, sanidad, cuidados de larga duración, educación)",
    "23.9% of GDP in 2022, 29.0% in 2070": "23.9% del PIB en 2022, 29.0% en 2070",
    "Table 1": "cuadro 1",
    "Contributors per 100 pensioners": "Cotizantes por cada 100 pensionistas",
    "237 in 2022, 146 in 2050, 137 in 2070": "237 en 2022, 146 en 2050, 137 en 2070",
    "Statistical Annex, country table for Spain": "anexo estadístico, cuadro de España",
    "Benefit ratio (average pension against average wage)": "Tasa de beneficio (pensión media sobre el salario medio)",
    "64.1% in 2022, 51.4% in 2070": "64.1% en 2022, 51.4% en 2070",
    # AIReF, 2025 and 2026
    "Yield of the revenue measures adopted since 2020": "Recaudación de las medidas de ingresos adoptadas desde 2020",
    "1.4% of GDP a year on average in 2022-2050": "1.4% del PIB al año de media en 2022-2050",
    "summary and section on the revenue measures": "resumen y apartado sobre las medidas de ingresos",
    "Average gross pension spending in 2022-2050": "Gasto bruto medio en pensiones en 2022-2050",
    "14.6% of GDP (the Ageing Report updated with actual data; 15.4% as published)":
        "14.6% del PIB (el Ageing Report actualizado con datos observados; 15.4% en la versión publicada)",
    "summary": "resumen",
    "Spending net of the revenue measures, against the limit": "Gasto neto de las medidas de ingresos, frente al límite",
    "13.2% of GDP, under the 13.3% limit, so the rule is met":
        "13.2% del PIB, por debajo del límite del 13.3%, así que se cumple la regla",
    "AIReF's own projection": "Proyección propia de la AIReF",
    "pension spending from 12.7% of GDP in 2022 to 16.1% in 2050":
        "gasto en pensiones del 12.7% del PIB en 2022 al 16.1% en 2050",
    "summary and conclusions": "resumen y conclusiones",
    "Yield of the revenue measures": "Recaudación de las medidas de ingresos",
    "1.6% of GDP a year on average in 2022-2050 (1.4% in 2025)": "1.6% del PIB al año de media en 2022-2050 (1.4% en 2025)",
    "13.0% of GDP, under the 13.3% limit, so the rule is met":
        "13.0% del PIB, por debajo del límite del 13.3%, así que se cumple la regla",
    "pension spending from 13% of GDP in 2025 to 16.4% in 2050": "gasto en pensiones del 13% del PIB en 2025 al 16.4% en 2050",
    "section on the pension spending projections": "apartado sobre las proyecciones del gasto en pensiones",
    "Public debt in 2050 with policies unchanged": "Deuda pública en 2050 con las políticas actuales",
    "about 123% of GDP; ageing adds about 52 points, 33.9 of them from pensions":
        "en torno al 123% del PIB; el envejecimiento añade unos 52 puntos, 33.9 de ellos por las pensiones",
    "section on the sustainability of public finances": "apartado sobre la sostenibilidad de las finanzas públicas",
    "AIReF's view of the rule": "La opinión de la AIReF sobre la regla",
    "met formally, but no guarantee of sustainability; AIReF proposes redesigning it":
        "se cumple formalmente, pero no garantiza la sostenibilidad; la AIReF propone rediseñarla",
    "summary and recommendations": "resumen y recomendaciones",
    # the Banco de España, Informe Anual 2023
    "Pension spending in 2023 (contributory, non-contributory and civil servants')":
        "Gasto en pensiones en 2023 (contributivas, no contributivas y de Clases Pasivas)",
    "13.1% of GDP, 28.3% of public non-financial spending": "13.1% del PIB, 28.3% del gasto público no financiero",
    "section 9.2": "apartado 9.2",
    "Over the past decade": "En la última década",
    "up 1.1 points of GDP, with over a million more pensions":
        "1.1 puntos de PIB más, con más de un millón de pensiones adicionales",
    "Projections it cites for 2050": "Proyecciones que cita para 2050",
    "17.3% of GDP (Ageing Report), 16.2% (AIReF); pensions from 11.1 million to 16.7 million":
        "17.3% del PIB (Ageing Report), 16.2% (AIReF); las pensiones, de 11.1 millones a 16.7 millones",
    "Its conclusion": "Su conclusión",
    "additional measures will very probably be needed; relying only on higher contributions could harm jobs and competitiveness":
        "muy probablemente harán falta medidas adicionales; confiar solo en cotizaciones más altas podría dañar el "
        "empleo y la competitividad",
})
