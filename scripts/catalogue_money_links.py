"""Spanish for how money, credit and the economy move together on the Financial page (Batch 35b): money and prices,
credit and growth, monetary transmission and what has led growth and inflation. Read by scripts/write_catalogue.py;
keys are the English exactly as econpulse/monetary.py and pages.py write it. The countercyclical capital buffer is the
Banco de España's "colchón de capital anticíclico"; rates on new business are "nuevas operaciones".
"""

PAIRS: dict[str, str] = {}

PAIRS.update({
    # correlation words
    "weak and positive": "débil y positiva",
    "weak and negative": "débil y negativa",
    "moderate and positive": "moderada y positiva",
    "moderate and negative": "moderada y negativa",
    "strong and positive": "fuerte y positiva",
    "strong and negative": "fuerte y negativa",
    "same quarter": "mismo trimestre",
    "{n} quarter ahead": "{n} trimestre después",
    "{n} quarters ahead": "{n} trimestres después",
    # sources
    "Banco de España; Eurostat; Macroscope calculation": "Banco de España; Eurostat; cálculo de Macroscope",
    "INE; Banco de España; Macroscope calculation": "INE; Banco de España; cálculo de Macroscope",
    "ECB; INE; Macroscope calculation": "BCE; INE; cálculo de Macroscope",
    "ECB; Banco de España; INE; Eurostat; Macroscope calculation": "BCE; Banco de España; INE; Eurostat; cálculo de Macroscope",
})

PAIRS.update({
    # block: how money, credit and the economy move together
    "How money, credit and the economy move together": "Cómo se mueven juntos el dinero, el crédito y la economía",
    "How money and credit have moved with prices, spending and growth in Spain, and how those links have changed. Each chart says what it measures and over which years; the readings under them describe correlations, which show what moves together, not what causes what.":
        "Cómo se han movido el dinero y el crédito con los precios, el gasto y el crecimiento en España, y cómo han "
        "cambiado esas relaciones. Cada gráfico dice qué mide y en qué años; las lecturas que lo acompañan describen "
        "correlaciones, que muestran qué se mueve a la vez, no qué causa qué.",
    "Velocity of money": "Velocidad del dinero",
    "nominal GDP per euro of broad money · {q}": "PIB nominal por cada euro de dinero en sentido amplio · {q}",
    "Credit impulse": "Impulso crediticio",
    "change in a year's net new lending · {q}": "variación del crédito nuevo neto de un año · {q}",
    "Credit-to-GDP gap": "Brecha de crédito sobre PIB",
    "BIS; above 2 points calls for a capital buffer · {q}": "BPI; por encima de 2 puntos pide un colchón de capital · {q}",
    # money and prices
    "Broad money growth and inflation two years later": "Crecimiento del dinero en sentido amplio e inflación dos años después",
    "% change on a year earlier; broad money growth is drawn two years after the month it was measured":
        "Variación interanual, %; el crecimiento del dinero en sentido amplio se dibuja dos años después del mes en "
        "que se midió",
    "Faster money growth is meant to show up in prices a year or two later. Here broad money is drawn two years after it was measured, so the lines would move together if it did.":
        "Se supone que un crecimiento más rápido del dinero acaba en los precios uno o dos años después. Aquí el dinero "
        "en sentido amplio se dibuja dos años después de medirse, así que, si fuera así, las líneas irían juntas.",
    "Quarter by quarter since 2000, leaving out 2020 and 2021, the correlation two years on is {r}: {link}.":
        "Trimestre a trimestre desde 2000, sin 2020 ni 2021, la correlación a dos años vista es de {r}: {link}.",
    "Money growth peaked at {peak} in {month}; two years later inflation was {later}.":
        "El crecimiento del dinero alcanzó su máximo, un {peak}, en {month}; dos años después la inflación era del {later}.",
    "As a member of the euro area, Spain's prices follow the euro area's money and energy costs as much as its own money.":
        "Como miembro de la zona del euro, los precios de España siguen tanto al dinero de toda la zona y al coste de "
        "la energía como a su propio dinero.",
    "The velocity of money": "La velocidad del dinero",
    "Nominal GDP over the past four quarters divided by broad money at the end of the quarter":
        "PIB nominal de los cuatro últimos trimestres dividido por el dinero en sentido amplio al final del trimestre",
    "Velocity": "Velocidad",
    "How many times a year each euro of broad money pays for the economy's output: nominal GDP over the money stock. It was {first} in {first_q}, peaked at {peak} in {peak_q} and is {last} in {last_q}.":
        "Cuántas veces al año paga cada euro de dinero en sentido amplio la producción de la economía: el PIB nominal "
        "sobre el saldo de dinero. Era de {first} en el {first_q}, alcanzó su máximo, {peak}, en el {peak_q} y es de {last} en el {last_q}.",
    "Money has grown faster than nominal GDP since then: households and firms hold more money for each euro of output, so money growth alone is a poor guide to spending.":
        "Desde entonces el dinero ha crecido más que el PIB nominal: hogares y empresas mantienen más dinero por cada "
        "euro de producción, así que el crecimiento del dinero, por sí solo, orienta mal sobre el gasto.",
    # credit and growth
    "Credit and nominal growth": "Crédito y crecimiento nominal",
    "% change on a year earlier: bank loans to the private sector (adjusted for sales and write-offs) and nominal GDP":
        "Variación interanual, %: préstamos bancarios al sector privado (corregidos de ventas y saneamientos) y PIB nominal",
    "Bank credit": "Crédito bancario",
    "From 2005 to 2007 bank credit grew {c} a year on average, {times} times as fast as nominal GDP ({g}).":
        "De 2005 a 2007 el crédito bancario creció un {c} al año de media, {times} veces más deprisa que el PIB nominal ({g}).",
    "It then shrank in {n} of the {total} quarters from {first} to {last}, as households and firms paid down debt.":
        "Después se contrajo en {n} de los {total} trimestres entre el {first} y el {last}, mientras hogares y empresas "
        "reducían su deuda.",
    "Since 2000 the two have a correlation of {r}: {link}.": "Desde 2000 los dos tienen una correlación de {r}: {link}.",
    "Credit to GDP and its long-run trend": "Crédito sobre PIB y su tendencia a largo plazo",
    "Credit to the private non-financial sector, % of GDP, and the Basel Committee's trend":
        "Crédito al sector privado no financiero, % del PIB, y la tendencia del Comité de Basilea",
    "Credit to GDP": "Crédito sobre PIB",
    "Long-run trend": "Tendencia a largo plazo",
    "Credit from all lenders to firms and households rose to {peak} of GDP in {peak_q}, the debt left by the housing boom, and was {last} in {last_q}. The long-run trend follows slowly, so after a bust it stays above the ratio for years.":
        "El crédito de todos los prestamistas a empresas y hogares subió hasta el {peak} del PIB en el {peak_q}, la deuda "
        "que dejó el auge inmobiliario, y era del {last} en el {last_q}. La tendencia a largo plazo lo sigue despacio, así "
        "que tras una crisis se queda por encima de la ratio durante años.",
    "The credit-to-GDP gap": "La brecha de crédito sobre PIB",
    "Credit to GDP less its long-run trend, percentage points": "Crédito sobre PIB menos su tendencia a largo plazo, puntos porcentuales",
    "Buffer starts": "Empieza el colchón",
    "Buffer at its maximum": "Colchón al máximo",
    "The Basel Committee's early-warning gauge: when the gap passes 2 points, banks may be asked to build a countercyclical capital buffer, which reaches its maximum at 10. Spain's peaked at {peak} points in {peak_q}, before the banking crisis, and is {last} in {last_q}.":
        "El indicador de alerta temprana del Comité de Basilea: cuando la brecha supera los 2 puntos, se puede pedir a "
        "los bancos que acumulen un colchón de capital anticíclico, que llega a su máximo en 10. La de España alcanzó su "
        "máximo, {peak} puntos, en el {peak_q}, antes de la crisis bancaria, y es de {last} en el {last_q}.",
    "It was last above 2 in {q}. A negative gap after a long deleveraging partly reflects the boom still held in the trend, so it overstates how tight credit is.":
        "Estuvo por encima de 2 por última vez en el {q}. Una brecha negativa tras un largo desapalancamiento refleja en "
        "parte el auge que aún arrastra la tendencia, así que exagera lo restringido que está el crédito.",
    "The credit impulse and domestic demand": "El impulso crediticio y la demanda nacional",
    "Change in the past year's net new lending to firms and households, % of GDP (bars); real domestic demand, % change on a year earlier (line)":
        "Variación del crédito nuevo neto a empresas y hogares del último año, % del PIB (barras); demanda nacional real, "
        "variación interanual, % (línea)",
    "Spending depends on the flow of new credit rather than its stock, so it is the change in that flow, the credit impulse, that moves with demand. Since {start}, leaving out 2020 and 2021, the correlation is {r}: {link}. In 2020 the state-guaranteed ICO loans pushed the impulse up while demand collapsed.":
        "El gasto depende del flujo de crédito nuevo más que de su saldo, así que es la variación de ese flujo, el "
        "impulso crediticio, la que se mueve con la demanda. Desde {start}, sin 2020 ni 2021, la correlación es de {r}: "
        "{link}. En 2020 los préstamos avalados por el ICO elevaron el impulso mientras la demanda se hundía.",
})

PAIRS.update({
    # block: monetary transmission
    "Monetary transmission: from the ECB to bank rates": "Transmisión monetaria: del BCE a los tipos bancarios",
    "How the ECB's interest rate reaches what Spanish banks charge borrowers and pay savers. The banks' rates are on new business, so they show where pricing is now, not what existing loans and deposits pay.":
        "Cómo llega el tipo de interés del BCE a lo que los bancos españoles cobran a quienes piden prestado y pagan a "
        "quienes ahorran. Los tipos de los bancos son de nuevas operaciones, así que muestran los precios de ahora, no "
        "lo que pagan los préstamos y depósitos ya existentes.",
    "since {day}": "desde el {day}",
    "New loans to firms": "Préstamos nuevos a empresas",
    "{spread} points over the ECB's rate · {month}": "{spread} puntos sobre el tipo del BCE · {month}",
    "Passed on to loans to firms": "Trasladado a los préstamos a empresas",
    "Passed on to overnight deposits": "Trasladado a los depósitos a la vista",
    "of the ECB's 2022–23 rises, by {month}": "de las subidas del BCE de 2022–23, hasta {month}",
    "From the ECB's rate to banks' rates": "Del tipo del BCE a los tipos de los bancos",
    "% a year, monthly averages; banks' rates on new loans and on new deposits of households":
        "% anual, medias mensuales; tipos de los bancos en préstamos nuevos y en depósitos nuevos de hogares",
    "Loans to firms": "Préstamos a empresas",
    "Time deposits": "Depósitos a plazo",
    "Overnight deposits": "Depósitos a la vista",
    "The ECB sets the deposit rate; 12-month Euribor, what banks charge each other, moves ahead of it on expected decisions, and Spain's variable-rate mortgages are mostly priced off it. Banks' rates on new loans follow within months; what they pay on deposits moves less, and on overnight deposits barely at all.":
        "El BCE fija el tipo de la facilidad de depósito; el Euríbor a 12 meses, lo que se cobran los bancos entre sí, se "
        "adelanta a él con las decisiones esperadas, y la mayoría de las hipotecas a tipo variable de España se fijan "
        "sobre él. Los tipos de los préstamos nuevos lo siguen en pocos meses; lo que pagan por los depósitos se mueve "
        "menos, y en los depósitos a la vista apenas nada.",
    "What banks charge and pay over the ECB's rate": "Lo que cobran y pagan los bancos sobre el tipo del BCE",
    "Rates on new business less the ECB deposit rate, percentage points":
        "Tipos de nuevas operaciones menos el tipo de depósito del BCE, puntos porcentuales",
    "What banks charge on new loans above the ECB's rate, and what they pay on deposits below it. The spread on new loans to firms was {nfc} points in {month}, against {avg} on average since 2003. Overnight deposits paid {low} points less than the ECB's rate at the widest, in {low_month}.":
        "Lo que cobran los bancos por los préstamos nuevos por encima del tipo del BCE, y lo que pagan por los depósitos "
        "por debajo de él. El diferencial de los préstamos nuevos a empresas era de {nfc} puntos en {month}, frente a "
        "{avg} de media desde 2003. Los depósitos a la vista llegaron a pagar {low} puntos menos que el tipo del BCE, "
        "en {low_month}.",
    "How much of the 2022–23 rises reached each rate": "Cuánto de las subidas de 2022–23 llegó a cada tipo",
    "Change from the month before the ECB's first rise to the month its deposit rate peaked, percentage points":
        "Variación entre el mes anterior a la primera subida del BCE y el mes en que su tipo de depósito tocó máximo, "
        "puntos porcentuales",
    "The ECB raised its deposit rate by {dfr} points between {start} and {peak}. Over the same months the rate on new loans to firms rose {nfc} points ({nfc_share} of the rise), new mortgages {mort} ({mort_share}), new time deposits {td} ({td_share}) and overnight deposits {on} ({on_share}).":
        "El BCE subió su tipo de depósito {dfr} puntos entre {start} y {peak}. En esos mismos meses el tipo de los "
        "préstamos nuevos a empresas subió {nfc} puntos (el {nfc_share} de la subida), el de las hipotecas nuevas {mort} "
        "({mort_share}), el de los depósitos a plazo nuevos {td} ({td_share}) y el de los depósitos a la vista {on} "
        "({on_share}).",
})

PAIRS.update({
    # block: what matters most
    "What matters most: what has led growth and inflation": "Qué importa más: qué se ha adelantado al crecimiento y a la inflación",
    "Which of money, credit, interest rates and spreads has moved most closely with GDP growth and inflation in the quarters that followed, from 2000 on. The pandemic years 2020 and 2021 are left out, as the lockdowns and the rebound swamped every relationship. A correlation measures how closely two series move together, from −1 to 1; it doesn't show that one causes the other.":
        "Cuál de estas variables (el dinero, el crédito, los tipos de interés y los diferenciales) se ha movido más a la par del crecimiento "
        "del PIB y de la inflación en los trimestres siguientes, desde 2000. Se dejan fuera los años de la pandemia, 2020 "
        "y 2021, porque los confinamientos y el rebote anularon cualquier relación. Una correlación mide hasta qué punto "
        "dos series se mueven juntas, de −1 a 1; no demuestra que una cause la otra.",
    "Moves most with growth": "La que más va con el crecimiento",
    "Moves most against growth": "La que más va contra el crecimiento",
    "Moves most with inflation": "La que más va con la inflación",
    "Moves most against inflation": "La que más va contra la inflación",
    "Broad money growth": "Crecimiento del dinero en sentido amplio",
    "Credit growth": "Crecimiento del crédito",
    "ECB rate change": "Variación del tipo del BCE",
    "Loan spread": "Diferencial de los préstamos",
    "Risk premium": "Prima de riesgo",
    "Leader": "Variable",
    "The strongest correlation at 0 to 8 quarters ahead, since 2000, leaving out 2020 and 2021":
        "La correlación más fuerte a entre 0 y 8 trimestres vista, desde 2000, sin 2020 ni 2021",
    "With real GDP growth": "Con el crecimiento del PIB real",
    "Quarters ahead": "Trimestres después",
    "With inflation": "Con la inflación",
    "Broad money growth: on a year earlier, end of quarter. Credit growth: bank loans to the private sector on a year earlier, adjusted for sales and write-offs. Credit impulse: the change in a year's net new lending to firms and households, % of GDP (from 2005). ECB rate change: the deposit rate on a year earlier. Loan spread: the rate on new loans to firms less the ECB deposit rate. Risk premium: Spain's 10-year yield less Germany's. Growth and inflation are on a year earlier, quarterly. Overlapping yearly changes make neighbouring quarters alike, so small correlations are not reliable.":
        "Crecimiento del dinero en sentido amplio: interanual, a final de trimestre. Crecimiento del crédito: préstamos "
        "bancarios al sector privado, interanual, corregido de ventas y saneamientos. Impulso crediticio: la variación "
        "del crédito nuevo neto de un año a empresas y hogares, % del PIB (desde 2005). Variación del tipo del BCE: el "
        "tipo de depósito frente a un año antes. Diferencial de los préstamos: el tipo de los préstamos nuevos a "
        "empresas menos el tipo de depósito del BCE. Prima de riesgo: el rendimiento a 10 años de España menos el de "
        "Alemania. El crecimiento y la inflación son interanuales, trimestrales. Las variaciones anuales se solapan y "
        "hacen parecidos los trimestres vecinos, así que las correlaciones pequeñas no son fiables.",
    "What has moved with growth": "Qué se ha movido con el crecimiento",
    "Correlation with real GDP growth 0 to 8 quarters later, since 2000, leaving out 2020 and 2021":
        "Correlación con el crecimiento del PIB real entre 0 y 8 trimestres después, desde 2000, sin 2020 ni 2021",
    "What has moved with inflation": "Qué se ha movido con la inflación",
    "Correlation with inflation 0 to 8 quarters later, since 2000, leaving out 2020 and 2021":
        "Correlación con la inflación entre 0 y 8 trimestres después, desde 2000, sin 2020 ni 2021",
    "Correlations, not causes: a variable can lead because it moves first or because it reacts to the same news faster.":
        "Correlaciones, no causas: una variable puede adelantarse porque se mueve antes o porque reacciona más deprisa a "
        "las mismas noticias.",
    "Moving most closely with growth: {name} ({r}, {ahead}).": "La que más va con el crecimiento: {name} ({r}, {ahead}).",
    "Moving most closely with inflation: {name} ({r}, {ahead}).": "La que más va con la inflación: {name} ({r}, {ahead}).",
    "Moving most closely against it: {name} ({r}, {ahead}).": "La que más va en contra: {name} ({r}, {ahead}).",
    "Rate rises go with strong growth at first, as the ECB raises rates in good times; the link fades within two years.":
        "Las subidas de tipos van al principio con un crecimiento fuerte, porque el BCE sube los tipos en los buenos "
        "tiempos; la relación se desvanece en dos años.",
    "Do the links hold? Correlations over eight-year windows": "¿Se mantienen las relaciones? Correlaciones en ventanas de ocho años",
    "Correlation over the previous 32 quarters, leaving out 2020 and 2021: broad money growth with inflation two years later, the credit impulse with real GDP growth a quarter later, credit growth and the risk premium with growth in the same quarter":
        "Correlación en los 32 trimestres anteriores, sin 2020 ni 2021: el crecimiento del dinero en sentido amplio con "
        "la inflación dos años después, el impulso crediticio con el crecimiento del PIB real un trimestre después, y el "
        "crecimiento del crédito y la prima de riesgo con el crecimiento del mismo trimestre",
    "Money, inflation": "Dinero, inflación",
    "Impulse, growth": "Impulso, crecimiento",
    "Credit, growth": "Crédito, crecimiento",
    "Premium, growth": "Prima, crecimiento",
    "Broad money growth with inflation two years later": "El crecimiento del dinero en sentido amplio con la inflación dos años después",
    "The credit impulse with growth a quarter later": "El impulso crediticio con el crecimiento un trimestre después",
    "Credit growth with growth in the same quarter": "El crecimiento del crédito con el crecimiento del mismo trimestre",
    "The risk premium with growth in the same quarter": "La prima de riesgo con el crecimiento del mismo trimestre",
    "Each point is the correlation over the 32 quarters (8 years) up to it, skipping 2020 and 2021. The links are far from fixed. {name}: from {lo} to {hi}, and {last} in the latest window.":
        "Cada punto es la correlación en los 32 trimestres (8 años) hasta él, sin contar 2020 ni 2021. Las relaciones "
        "distan de ser fijas. {name}: de {lo} a {hi}, y {last} en la última ventana.",
})
