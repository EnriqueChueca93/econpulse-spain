"""Spanish for the Analysis page (Batch 33c-1): the economy against its history, data surprises, the GDP nowcast,
what forecasters expect, the 10-year yield in two parts and Taylor rules (econpulse/pages.py "analysis", and the
tables, facts and charts written by econpulse/analytics.py, surprises.py and forecasts.py). Read by
scripts/write_catalogue.py; the keys are the English exactly as the code writes it.
"""

PAIRS: dict[str, str] = {}

# ---------------------------------------------------------------- the blocks' introductions and charts (pages.py)
PAIRS.update({
    "Two summary readings. Each indicator is compared with its own record since 2013 (a z-score: 0 is normal, +1 is one typical deviation above), then the scores are averaged, giving the newest data the most weight. Macroscope calculation, not an official statistic.":
        "Dos lecturas de síntesis. Cada indicador se compara con su propio historial desde 2013 (una puntuación z: 0 es "
        "lo normal, +1 es una desviación típica por encima) y después se promedian las puntuaciones, dando más peso a "
        "los datos más recientes. Cálculo de Macroscope, no una estadística oficial.",
    "Did the latest figures beat or miss expectations? Analysts' forecasts for Spanish data are not freely available, so each figure is compared with a simple statistical forecast: what the indicator's own past predicted. Above zero, the data came in stronger (or inflation hotter) than that forecast. Macroscope calculation, not a survey of forecasters.":
        "¿Superaron o defraudaron las expectativas los últimos datos? Las previsiones de los analistas para los datos "
        "españoles no son de libre acceso, así que cada dato se compara con una previsión estadística sencilla: lo que "
        "predecía el propio pasado del indicador. Por encima de cero, el dato fue más fuerte (o la inflación más alta) "
        "que esa previsión. Cálculo de Macroscope, no una encuesta a analistas.",
    "An estimate of this quarter's GDP growth before INE publishes it, from Social Security registrations, industrial production and last quarter's growth (a bridge equation fitted on 2013 onwards, leaving out 2020-21). A placeholder: the model is still being worked on.":
        "Una estimación del crecimiento del PIB de este trimestre antes de que lo publique el INE, a partir de la "
        "afiliación a la Seguridad Social, la producción industrial y el crecimiento del trimestre anterior (una "
        "ecuación puente estimada desde 2013, sin 2020-21). Es provisional: el modelo aún está en desarrollo.",
    "The latest forecasts for Spain this year and next, with Macroscope's own figure for this year's GDP. Each forecaster's row shows when it was published: forecasts made months apart saw different data, so differences are partly about timing.":
        "Las últimas previsiones para España de este año y el próximo, con la cifra propia de Macroscope para el PIB de "
        "este año. La fila de cada institución indica cuándo se publicó: las previsiones hechas con meses de diferencia "
        "partían de datos distintos, así que las diferencias se deben en parte al momento en que se hicieron.",
    "Spain's 10-year yield is the German yield plus the prima de riesgo. Splitting a move into the two shows whether it is about euro-area rates or about Spain.":
        "La rentabilidad del bono español a 10 años es la alemana más la prima de riesgo. Dividir un movimiento en esas "
        "dos partes muestra si tiene que ver con los tipos de la zona del euro o con España.",
    "A Taylor rule turns inflation and slack into a suggested policy rate. Run on euro-area data it is a yardstick for the ECB; run on Spanish data it shows the rate Spain would get if it set its own, the cost of one rate for all.":
        "Una regla de Taylor convierte la inflación y la holgura de la economía en un tipo oficial sugerido. Aplicada a "
        "los datos de la zona del euro, es una vara de medir para el BCE; aplicada a los datos españoles, muestra el tipo "
        "que tendría España si fijara el suyo propio: el coste de un tipo único para todos.",
    "Spain's 10-year yield, in two parts": "La rentabilidad a 10 años de España, en dos partes",
    "%, monthly averages: the German yield plus the prima de riesgo":
        "%, medias mensuales: la rentabilidad alemana más la prima de riesgo",
    "German yield": "Rentabilidad alemana",
})

# ---------------------------------------------------------------- the economy against its history (analytics.py)
PAIRS.update({
    # The composites' components (analytics.ACTIVITY, analytics.INFLATION)
    "Registrations, monthly change, SA (3-mo avg.)": "Afiliados, variación mensual, desest. (media 3 meses)",
    "Unemployment rate, change over 3 months": "Tasa de paro, variación en 3 meses",
    "Industrial production, y/y": "Producción industrial, a/a",
    "Retail sales, y/y": "Ventas minoristas, a/a",
    "Car sales, y/y (3-mo avg.)": "Matriculaciones de turismos, a/a (media 3 meses)",
    "Electricity demand, y/y (3-mo avg.)": "Demanda eléctrica, a/a (media 3 meses)",
    "Tourists, y/y (3-mo avg.)": "Turistas, a/a (media 3 meses)",
    "Real GDP, q/q": "PIB real, t/t",
    "HICP inflation": "Inflación del IPCA",
    "Core HICP inflation": "Inflación subyacente del IPCA",
    "Services inflation": "Inflación de los servicios",
    "Core CPI, 3-mo annualised, SA": "IPC subyacente, 3 meses anualizado, desest.",
    "Producer prices, y/y": "Precios industriales, a/a",
    "Consumers' price expectations": "Expectativas de precios de los consumidores",
    "Wage cost per worker, y/y": "Coste salarial por trabajador, a/a",
    # Table and chart
    "Latest readings and their z-scores · composite for {month}":
        "Últimos datos y sus puntuaciones z · indicador compuesto de {month}",
    "z-score": "Puntuación z",
    "Weight": "Peso",
    "A z-score of +1 means one typical deviation above the 2013–present norm (Covid years left out). Weights fall by a quarter for each month a reading is older than the newest data.":
        "Una puntuación z de +1 significa una desviación típica por encima de la norma de 2013 hasta hoy (sin los años "
        "de la COVID). Los pesos bajan una cuarta parte por cada mes que un dato es más antiguo que el más reciente.",
    "Activity and inflation against their history": "Actividad e inflación frente a su historia",
    "Weighted average of z-scores, monthly; 0 = the 2013–present norm":
        "Media ponderada de las puntuaciones z, mensual; 0 = la norma de 2013 hasta hoy",
    "Macroscope calculation from INE, Eurostat, Seguridad Social, Red Eléctrica":
        "cálculo de Macroscope con datos del INE, Eurostat, la Seguridad Social y Red Eléctrica",
})

# ---------------------------------------------------------------- data surprises (surprises.py)
PAIRS.update({
    # Each period's own figure (the composites' labels without their smoothing)
    "Registrations, monthly change, SA": "Afiliados, variación mensual, desest.",
    "Unemployment rate, monthly change": "Tasa de paro, variación mensual",
    "Car sales, y/y": "Matriculaciones de turismos, a/a",
    "Electricity demand, y/y": "Demanda eléctrica, a/a",
    "Tourists, y/y": "Turistas, a/a",
    "Latest figures against the statistical forecast · index for {month}":
        "Últimos datos frente a la previsión estadística · índice de {month}",
    "Forecast": "Previsión",
    "Surprise": "Sorpresa",
    "Forecast: what an AR(1) model fitted on the earlier figures expected. Surprise: the gap in units of the model's typical error since 2013 (Covid years left out); positive means hotter inflation.":
        "Previsión: lo que esperaba un modelo AR(1) estimado con los datos anteriores. Sorpresa: la diferencia en "
        "unidades del error típico del modelo desde 2013 (sin los años de la COVID); un valor positivo indica una "
        "inflación más alta.",
    "Forecast: what an AR(1) model fitted on the earlier figures expected. Surprise: the gap in units of the model's typical error since 2013 (Covid years left out); positive means a stronger economy (for unemployment, a smaller rise than expected).":
        "Previsión: lo que esperaba un modelo AR(1) estimado con los datos anteriores. Sorpresa: la diferencia en "
        "unidades del error típico del modelo desde 2013 (sin los años de la COVID); un valor positivo indica una "
        "economía más fuerte (en el paro, una subida menor de lo esperado).",
    "Surprise indexes": "Índices de sorpresas",
    "Average surprise over the past four months, newest weighted most; above 0 = above forecast":
        "Sorpresa media de los últimos cuatro meses, con más peso para las más recientes; por encima de 0 = por encima "
        "de la previsión",
})

# ---------------------------------------------------------------- GDP nowcast (analytics.py)
PAIRS.update({
    "Social Security registrations (SA)": "Afiliados a la Seguridad Social (desest.)",
    "Input": "Variable",
    "What the {q} nowcast is built on": "En qué se basa la estimación adelantada de {q}",
    "Latest month": "Último mes",
    "Months of {q}": "Meses de {q}",
    "The model also uses the previous quarter's GDP growth. Months not yet published are projected from each series' recent momentum (an AR(1) model), so early in a quarter the nowcast leans on those projections.":
        "El modelo usa también el crecimiento del PIB del trimestre anterior. Los meses aún no publicados se proyectan "
        "a partir de la inercia reciente de cada serie (un modelo AR(1)), así que al principio de un trimestre la "
        "estimación adelantada se apoya en esas proyecciones.",
    "Quarter": "Trimestre",
    "Track record: each quarter predicted from a model fitted on earlier data":
        "Historial: cada trimestre, previsto con un modelo estimado con datos anteriores",
    "Model": "Modelo",
    "Official": "Oficial",
    "Error": "Error",
    "Since 2023 the model's typical (root mean square) error is {rmse} pp, against {naive} pp for repeating the previous quarter and {mean} pp for the post-2013 average. The inputs were chosen with this same test, and it uses complete quarters of data, so real-time errors, with months still missing, will be larger.":
        "Desde 2023, el error típico del modelo (la raíz del error cuadrático medio) es de {rmse} pp, frente a {naive} pp "
        "si se repite el trimestre anterior y {mean} pp con la media desde 2013. Las variables se eligieron con esta "
        "misma prueba, que usa trimestres de datos completos, así que los errores en tiempo real, con meses aún por "
        "publicar, serán mayores.",
    "GDP growth: model and official figures": "Crecimiento del PIB: modelo y datos oficiales",
    "% change on the previous quarter; the last point is the nowcast for {q}":
        "Variación intertrimestral, %; el último punto es la estimación adelantada de {q}",
    "Official (INE)": "Oficial (INE)",
    "Macroscope calculation from INE and Seguridad Social": "cálculo de Macroscope con datos del INE y la Seguridad Social",
})

# ---------------------------------------------------------------- what forecasters expect (forecasts.py)
PAIRS.update({
    # The forecasters, in full and as the chart shortens them (BdE, FUNCAS, IMF and OECD are in the catalogue already)
    "FUNCAS Panel (consensus)": "Panel de FUNCAS (consenso)",
    "FUNCAS Panel": "Panel de FUNCAS",
    "AIReF": "AIReF",
    "Government": "Gobierno",
    "IMF World Economic Outlook": "Perspectivas de la economía mundial del FMI",
    "OECD Economic Outlook": "Perspectivas económicas de la OCDE",
    "European Commission": "Comisión Europea",
    "Commission": "Comisión",
    # Table
    "Forecaster": "Institución",
    "Forecasts for {year}": "Previsiones para {year}",
    "GDP growth": "Crecimiento del PIB",
    "Unemployment": "Paro",
    "real, %": "real, %",
    "annual avg., %": "media anual, %",
    "% of labour force": "% de la población activa",
    "In Spain": "En España",
    "International organisations": "Organismos internacionales",
    "via {source}": "vía {source}",
    "awaiting AI check": "pendiente de verificación por IA",
    "Range of the panel": "Horquilla del panel",
    "lowest to highest": "de la más baja a la más alta",
    "{low} to {high}": "{low} a {high}",
    "Summary": "Resumen",
    "Average of the forecasts above": "Media de las previsiones anteriores",
    "AI-checked rows only": "solo filas verificadas por IA",
    "Macroscope: INE's quarters + nowcast": "Macroscope: trimestres del INE + estimación adelantada",
    "Q4 {growth}": "T4 {growth}",
    "{names} and {last}": "{names} y {last}",
    "Inflation is the HICP for {hicp} and the CPI for {cpi}.": "La inflación es la del IPCA para {hicp}, y la del IPC para {cpi}.",
    "Inflation is the HICP for {names}.": "La inflación es la del IPCA para {names}.",
    "Inflation is the CPI for {names}.": "La inflación es la del IPC para {names}.",
    "A budget balance below zero is a deficit.": "Un saldo presupuestario negativo es un déficit.",
    "Figures are read automatically from each publisher's data service, web page or PDF, and count in the average and the chart only after an AI check against the publisher's own document.":
        "Las cifras se leen automáticamente del servicio de datos, la página web o el PDF de cada institución, y solo "
        "cuentan en la media y en el gráfico después de que una IA las verifique con el documento de la propia "
        "institución.",
    "Rows marked “awaiting AI check” are newly read and not yet checked.":
        "Las filas marcadas como «pendiente de verificación por IA» se han leído hace poco y aún no se han verificado.",
    "{names} figures are taken from the FUNCAS Panel's reference table, which lists each with the month it was published.":
        "Las cifras de {names} proceden de la tabla de referencia del Panel de FUNCAS, que indica el mes en que se "
        "publicó cada una.",
    "The FUNCAS Panel is the average of about 19 forecasters (banks, research institutes, consultancies).":
        "El Panel de FUNCAS es la media de unas 19 instituciones (bancos, institutos de análisis y consultoras).",
    # Notes recorded with an AI check (data/forecast_checks.json)
    "The government's deficit figures leave out the extraordinary spending after the DANA floods.":
        "Las cifras de déficit del Gobierno no incluyen el gasto extraordinario tras las inundaciones de la DANA.",
    # Facts, callout and chart
    "GDP growth forecast, {year}": "Previsión de crecimiento del PIB, {year}",
    "average of {n}; range {low} to {high}": "media de {n}; entre {low} y {high}",
    "Macroscope, {year} GDP": "Macroscope, PIB de {year}",
    "INE to {quarter}, then the Q4 nowcast": "INE hasta {quarter}, después la estimación adelantada del T4",
    "Inflation forecast, {year}": "Previsión de inflación, {year}",
    "With three quarters published, {year} is largely decided: even with no growth at all in the fourth quarter, GDP would grow {flat} on {previous}. The forecasts differ mainly in what they expect for {following}.":
        "Con tres trimestres publicados, {year} está en gran parte decidido: aunque el PIB no creciera nada en el cuarto "
        "trimestre, aumentaría un {flat} respecto a {previous}. Las previsiones difieren sobre todo en lo que esperan "
        "para {following}.",
    "GDP growth forecasts": "Previsiones de crecimiento del PIB",
    "Real GDP, % change on a year earlier, {year} and {following}": "PIB real, variación interanual, %, {year} y {following}",
    "Forecasters' publications (see table), AI-checked; Macroscope nowcast":
        "publicaciones de cada institución (véase la tabla), verificadas por IA; estimación adelantada de Macroscope",
})

# ---------------------------------------------------------------- the 10-year yield in two parts (analytics.py)
PAIRS.update({
    "German Bund: euro-wide rates": "Bund alemán: tipos de toda la zona del euro",
    "Prima de riesgo: Spain-specific": "Prima de riesgo: factores propios de España",
    "Basis points, to {day}, the latest day with both yields":
        "Puntos básicos, hasta el {day}, último día con ambas rentabilidades",
    "Spain's yield is the German yield plus the prima de riesgo, so the two parts add up to the total. A rising Bund means rates are rising across the euro area; a rising prima de riesgo is about Spain.":
        "La rentabilidad española es la alemana más la prima de riesgo, así que las dos partes suman el total. Si sube "
        "el Bund, suben los tipos en toda la zona del euro; si sube la prima de riesgo, la causa está en España.",
})

# ---------------------------------------------------------------- Taylor rules (analytics.py)
PAIRS.update({
    "{month} average": "media de {month}",
    "Taylor rule, euro area": "Regla de Taylor, zona del euro",
    "Taylor rule, Spain": "Regla de Taylor, España",
    "Spain minus euro area": "España menos zona del euro",
    "the one-size-fits-all gap": "la brecha del tipo único para todos",
    "Inflation (HICP)": "Inflación (IPCA)",
    "Gap with the 2% target": "Diferencia con el objetivo del 2%",
    "Trend unemployment": "Paro tendencial",
    "Unemployment gap": "Brecha de paro",
    "Rate the rule suggests": "Tipo que sugiere la regla",
    "Latest month with every input · {month}": "Último mes con todos los datos · {month}",
    "Rule: {r_star}% neutral real rate + inflation + 0.5 × (inflation − 2%) − unemployment gap (Taylor's 1993 rule, with an output gap of twice the unemployment gap). Trend unemployment is a statistical trend (Hodrick–Prescott filter), so the latest gap is uncertain. A rule is a yardstick, not a forecast of what the ECB will do.":
        "Regla: {r_star}% de tipo real neutral + inflación + 0.5 × (inflación − 2%) − brecha de paro (la regla de Taylor "
        "de 1993, con una brecha de producción igual al doble de la brecha de paro). El paro tendencial es una tendencia "
        "estadística (filtro de Hodrick–Prescott), así que la última brecha es incierta. Una regla es una vara de medir, "
        "no una previsión de lo que hará el BCE.",
    "The ECB rate and what a Taylor rule suggests": "El tipo del BCE y lo que sugiere una regla de Taylor",
    "%, monthly": "%, mensual",
    "Rule, euro area": "Regla, zona del euro",
    "Rule, Spain": "Regla, España",
    "Macroscope calculation from Eurostat and the ECB": "cálculo de Macroscope con datos de Eurostat y el BCE",
})
