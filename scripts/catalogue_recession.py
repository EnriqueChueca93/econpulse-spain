"""Spanish for the recession signals on the Analysis page (Batch 36): the Sahm rule and the Michez rule ("regla de
Sahm", "regla de Michez"). Read by scripts/write_catalogue.py; keys are the English exactly as econpulse/recession.py
and pages.py write it. The AEE's committee is the "Comité de Fechado del Ciclo Económico Español" of the Asociación
Española de Economía.
"""

PAIRS: dict[str, str] = {}

PAIRS.update({
    # the block
    "Recession signals: the Sahm and Michez rules": "Señales de recesión: las reglas de Sahm y de Michez",
    "Two simple rules that say when a recession has probably started, from the job market alone. The Sahm rule watches unemployment rise above its recent low; the Michez rule, by Pascal Michaillat and Emmanuel Saez, also needs vacancies to fall from their recent high, which makes it less prone to false alarms. Both were built on US data: here they run on Spain's, checked against the recessions dated by the Spanish Economic Association's committee. Spain publishes vacancies quarterly, so the Michez rule runs on quarters, with thresholds set for Spain the way its authors set theirs. Macroscope calculation.":
        "Dos reglas sencillas que dicen cuándo ha empezado probablemente una recesión, solo con el mercado de trabajo. "
        "La regla de Sahm vigila que el paro suba por encima de su mínimo reciente; la de Michez, de Pascal Michaillat "
        "y Emmanuel Saez, exige además que las vacantes caigan desde su máximo reciente, lo que la hace menos propensa "
        "a las falsas alarmas. Ambas se crearon con datos de EE. UU.: aquí se aplican a los de España y se contrastan "
        "con las recesiones fechadas por el comité de la Asociación Española de Economía. España publica las vacantes "
        "cada trimestre, así que la regla de Michez se calcula por trimestres, con umbrales fijados para España como "
        "fijaron los suyos sus autores. Cálculo de Macroscope.",
    # facts
    "Sahm indicator": "Indicador de Sahm",
    "recession signal at 0.5 · {month}": "señal de recesión en 0.5 · {month}",
    "Michez indicator": "Indicador de Michez",
    "recession possible at {low}, certain at {high} (Spain) · {q}": "recesión posible desde {low}, segura desde {high} (España) · {q}",
    "Recession probability (Michez)": "Probabilidad de recesión (Michez)",
    "with Spain's thresholds · {q}": "con los umbrales de España · {q}",
    "Vacancy rate": "Tasa de vacantes",
    "job vacancies over the labour force · {q}": "puestos vacantes sobre la población activa · {q}",
    # the track-record table
    "Recession (AEE dating)": "Recesión (fechas de la AEE)",
    "When each rule first signalled Spain's recessions since 1987, and how long after the start":
        "Cuándo dio cada regla la primera señal de las recesiones de España desde 1987, y cuánto después de su inicio",
    "Sahm rule": "Regla de Sahm",
    "Months from the start": "Meses desde el inicio",
    "Michez rule (Spain)": "Regla de Michez (España)",
    "Quarters from the start": "Trimestres desde el inicio",
    "still on from {date}": "seguía activa desde {date}",
    "missed": "no la detectó",
    "False alarms": "Falsas alarmas",
    "none": "ninguna",
    "Signals in the past year, too soon to judge": "Señales del último año, demasiado pronto para juzgarlas",
    "Recessions as dated by the Spanish Economic Association's dating committee, from the quarter after the peak to the trough. A signal is the first month (or quarter) a rule reaches its threshold after a year below it; a negative number means before the recession began. A signal up to a year early counts as detecting the recession; one that no recession followed within a year is a false alarm. The Michez rule needs vacancy data, which start in 2001, and its Spanish thresholds are set so that it gives no false alarm over 2003-2021; from 2022 it is out of sample.":
        "Recesiones fechadas por el comité de fechado de la Asociación Española de Economía, del trimestre siguiente "
        "al pico hasta el valle. Una señal es el primer mes (o trimestre) en que una regla alcanza su umbral tras un año "
        "por debajo; un número negativo indica que fue antes de que empezara la recesión. Una señal hasta un año antes "
        "cuenta como detección de la recesión; una que no va seguida de una recesión en el plazo de un año es una "
        "falsa alarma. La regla de Michez necesita datos de vacantes, que empiezan en 2001, y sus umbrales para España "
        "se fijan para que no dé ninguna falsa alarma en 2003-2021; desde 2022 está fuera de la muestra.",
    # the Sahm chart
    "The Sahm rule for Spain": "La regla de Sahm para España",
    "3-month average unemployment rate less its low of the previous 12 months, percentage points; shaded: recessions":
        "Media de 3 meses de la tasa de paro menos su mínimo de los 12 meses anteriores, puntos porcentuales; "
        "sombreado: recesiones",
    "Sahm threshold": "Umbral de Sahm",
    "The 3-month average unemployment rate was {v} points above its lowest of the previous 12 months in {month}":
        "La media de 3 meses de la tasa de paro estaba {v} puntos por encima de su mínimo de los 12 meses anteriores en {month}",
    "The 3-month average unemployment rate was {v} points below its lowest of the previous 12 months in {month}":
        "La media de 3 meses de la tasa de paro estaba {v} puntos por debajo de su mínimo de los 12 meses anteriores en {month}",
    "the rule says a recession has likely started at 0.5. Of Spain's {n} recessions since 1987 it signalled {k} within a year before or during them.":
        "la regla dice que probablemente ha empezado una recesión en 0.5. De las {n} recesiones de España desde 1987, "
        "señaló {k} en el año previo o durante ellas.",
    "In {year} it was still on from the previous recession, as unemployment kept rising between the two.":
        "En {year} seguía activa desde la recesión anterior, porque el paro siguió subiendo entre ambas.",
    "It gave {n} false alarm: {dates}.": "Dio {n} falsa alarma: {dates}.",
    "It gave {n} false alarms: {dates}.": "Dio {n} falsas alarmas: {dates}.",
    "It gave no false alarms.": "No dio ninguna falsa alarma.",
    "Eurostat; AEE; Macroscope calculation": "Eurostat; AEE; cálculo de Macroscope",
    # the Michez chart
    "The Michez rule for Spain": "La regla de Michez para España",
    "The smaller of the unemployment and vacancy indicators, quarterly, percentage points; shaded: recessions":
        "El menor de los indicadores de paro y de vacantes, trimestral, puntos porcentuales; sombreado: recesiones",
    "Recession possible": "Recesión posible",
    "Recession certain": "Recesión segura",
    "The smaller of two signals: unemployment's rise above its low of the past year ({u} points) and vacancies' fall below their high ({v} points), in {q}. Set the way Michaillat and Saez set theirs, Spain's thresholds say a recession is possible from {low} points and certain from {high}.":
        "La menor de dos señales: la subida del paro sobre su mínimo del último año ({u} puntos) y la caída de las "
        "vacantes bajo su máximo ({v} puntos), en el {q}. Fijados como Michaillat y Saez fijaron los suyos, los umbrales "
        "de España dicen que una recesión es posible desde {low} puntos y segura desde {high}.",
    "At {x}, the rule says a recession may have started, with a probability of {p}. Both moves are small, a few hundredths of a point.":
        "Con {x}, la regla dice que puede haber empezado una recesión, con una probabilidad del {p}. Los dos "
        "movimientos son pequeños, de unas centésimas de punto.",
    "The Sahm rule isn't signalling.": "La regla de Sahm no da señal.",
    "At {x}, below the lower threshold, it signals no recession.":
        "Con {x}, por debajo del umbral inferior, no señala ninguna recesión.",
    "With three recessions to learn from, these thresholds are rough. The US ones, 0.29 and 0.81, can't be reached in Spain, where vacancies are a far smaller share of the labour force.":
        "Con solo tres recesiones de las que aprender, estos umbrales son aproximados. Los de EE. UU., 0.29 y 0.81, no "
        "se pueden alcanzar en España, donde las vacantes son una parte mucho menor de la población activa.",
    "Eurostat; INE; AEE; Macroscope calculation": "Eurostat; INE; AEE; cálculo de Macroscope",
    # the vacancy chart
    "Spain's vacancy rate": "La tasa de vacantes de España",
    "Job vacancies, % of the labour force, seasonally adjusted by Macroscope; shaded: recessions":
        "Puestos vacantes, % de la población activa, desestacionalizados por Macroscope; sombreado: recesiones",
    "The Michez rule's second input. Job vacancies were {v} of the labour force in {q}, against {low} at the lowest, in {low_q}. In the United States it was between about 4% and 7% from 2021 to 2024, so a fall in vacancies there moves the indicator by points and here by hundredths.":
        "El segundo ingrediente de la regla de Michez. Los puestos vacantes eran el {v} de la población activa en el "
        "{q}, frente al {low} en su mínimo, en el {low_q}. En EE. UU. la tasa estuvo entre el 4% y el 7% de 2021 a 2024, "
        "así que una caída de las vacantes allí mueve el indicador en puntos y aquí en centésimas.",
    "Eurostat; INE; Macroscope calculation": "Eurostat; INE; cálculo de Macroscope",
    "INE's figures more than double from the end of 2009 to the start of 2010, a break in the survey: the line stops there, and the rule never compares quarters across it.":
        "Las cifras del INE se duplican con creces entre finales de 2009 y principios de 2010, una ruptura en la "
        "encuesta: la línea se corta ahí y la regla nunca compara trimestres a ambos lados.",
})
