"""Spanish for the deeper GDP page (Batch 34d): contributions to growth, the income side, productivity in detail
and living standards. Read by scripts/write_catalogue.py; keys are the English exactly as econpulse/gdpdetail.py and
pages.py write it.
"""

PAIRS: dict[str, str] = {}

PAIRS.update({
    # what drives growth
    "What drives growth": "Qué impulsa el crecimiento",
    "GDP growth split into what each part of spending and each branch of activity adds, in percentage points. INE publishes only the domestic and external totals; the parts are a Macroscope calculation from its accounts, each part's volume growth weighted by its share of nominal GDP.":
        "El crecimiento del PIB dividido en lo que aporta cada componente del gasto y cada rama de actividad, en puntos "
        "porcentuales. El INE solo publica los totales de la demanda nacional y la externa; los componentes son un cálculo "
        "de Macroscope a partir de sus cuentas, el crecimiento en volumen de cada componente ponderado por su peso en el "
        "PIB nominal.",
    "Contribution": "Aportación",
    "Percentage points of GDP growth · {quarter}": "Puntos porcentuales del crecimiento del PIB · {quarter}",
    "GDP growth, %": "Crecimiento del PIB, %",
    "Inventories": "Existencias",
    "Branches of activity": "Ramas de actividad",
    "Professional and administrative services": "Actividades profesionales y administrativas",
    "Public administration, education and health": "Administración pública, educación y sanidad",
    "Arts and other services": "Actividades artísticas y otros servicios",
    "Taxes less subsidies on products": "Impuestos netos sobre los productos",
    "A Macroscope calculation from INE's accounts: each part's volume growth times its share of nominal GDP at the start of the period. INE publishes only the domestic and external totals; inventories are what is left of INE's domestic-demand contribution after consumption and investment. Since 2015 the parts add up to GDP growth within 0.03 points on average (a quarter of a point at most).":
        "Cálculo de Macroscope a partir de las cuentas del INE: el crecimiento en volumen de cada componente por su peso en "
        "el PIB nominal al inicio del periodo. El INE solo publica los totales de la demanda nacional y la externa; las "
        "existencias son lo que queda de la aportación de la demanda nacional del INE tras el consumo y la inversión. "
        "Desde 2015 los componentes suman el crecimiento del PIB con una diferencia media de 0.03 puntos (un cuarto de "
        "punto como máximo).",
    "Contributions to growth: demand": "Aportaciones al crecimiento: demanda",
    "Percentage points of GDP growth on a year earlier; imports subtract": "Puntos porcentuales del crecimiento interanual del PIB; las importaciones restan",
    "Contributions to quarterly growth: demand": "Aportaciones al crecimiento trimestral: demanda",
    "Percentage points of GDP growth on the previous quarter; imports subtract": "Puntos porcentuales del crecimiento intertrimestral del PIB; las importaciones restan",
    "Contributions to growth: branches": "Aportaciones al crecimiento: ramas de actividad",
    "Percentage points of GDP growth on a year earlier, by branch of activity": "Puntos porcentuales del crecimiento interanual del PIB, por rama de actividad",
    "Other branches and net taxes": "Otras ramas e impuestos netos",
    "INE; Macroscope calculation": "INE; cálculo de Macroscope",
    # who earns the income
    "Who earns the income": "Quién recibe la renta",
    "GDP measured by the incomes it pays: compensation of employees, the gross operating surplus and mixed income of firms and the self-employed, and taxes on production. The labour share is employees' compensation as a share of GDP at factor cost, that is, before those taxes.":
        "El PIB medido por las rentas que genera: la remuneración de los asalariados, el excedente bruto de explotación y "
        "la renta mixta de empresas y autónomos, y los impuestos sobre la producción. La participación del trabajo es la "
        "remuneración de los asalariados en porcentaje del PIB al coste de los factores, es decir, antes de esos impuestos.",
    "Labour share of income": "Participación del trabajo en la renta",
    "{quarter}; {then} on average in 2019": "{quarter}; {then} de media en 2019",
    "past four quarters, {change} on a year earlier": "últimos cuatro trimestres, {change} interanual",
    "Who earns the income: labour and capital": "Quién recibe la renta: trabajo y capital",
    "% of GDP at factor cost (GDP less taxes net of subsidies on production and imports)":
        "% del PIB al coste de los factores (el PIB menos los impuestos netos de subvenciones sobre la producción y las importaciones)",
    "Labour (compensation of employees)": "Trabajo (remuneración de los asalariados)",
    "Capital and the self-employed (operating surplus and mixed income)": "Capital y autónomos (excedente de explotación y renta mixta)",
    # productivity in detail
    "Productivity in detail": "La productividad en detalle",
    "How much is produced per hour worked and per job, whether growth comes from working more hours or from producing more in each, which branches have become more productive since 2019, and how Spain compares with the euro area. Output per hour by branch is gross value added in volume over hours worked, from INE's accounts; the comparisons are Eurostat's.":
        "Cuánto se produce por hora trabajada y por puesto de trabajo, si el crecimiento viene de trabajar más horas o de "
        "producir más en cada una, qué ramas son más productivas que en 2019 y cómo se compara España con la zona del "
        "euro. La producción por hora de cada rama es su valor añadido bruto en volumen entre las horas trabajadas, de las "
        "cuentas del INE; las comparaciones son de Eurostat.",
    "Output per hour worked": "Producción por hora trabajada",
    "2019 = 100 · {quarter}": "2019 = 100 · {quarter}",
    "On a year earlier": "Interanual",
    "output per hour worked": "producción por hora trabajada",
    "A year, since 2000": "Al año, desde 2000",
    "average growth of output per hour": "crecimiento medio de la producción por hora",
    "Output per hour and per job": "Producción por hora y por puesto de trabajo",
    "Real GDP per hour worked and per full-time equivalent job, and hours worked; 2019 = 100":
        "PIB real por hora trabajada y por puesto de trabajo equivalente a tiempo completo, y horas trabajadas; 2019 = 100",
    "Output per full-time equivalent job": "Producción por puesto equivalente a tiempo completo",
    "2019": "2019",
    "Growth from more hours or from more output per hour": "Crecimiento por más horas o por más producción por hora",
    "Real GDP growth on a year earlier, split in two (log points)": "Crecimiento interanual del PIB real, dividido en dos (puntos logarítmicos)",
    "Output per hour": "Producción por hora",
    "Output per hour by branch since 2019": "Producción por hora por rama desde 2019",
    "Real gross value added per hour worked, past four quarters against 2019, % change":
        "Valor añadido bruto real por hora trabajada, últimos cuatro trimestres frente a 2019, variación, %",
    "Branch": "Rama",
    "Output per hour: Spain and its neighbours": "Producción por hora: España y sus vecinos",
    "Real labour productivity per hour worked, fourth quarter of 2019 = 100": "Productividad real del trabajo por hora trabajada, cuarto trimestre de 2019 = 100",
    "Unit labour costs: Spain and its neighbours": "Costes laborales unitarios: España y sus vecinos",
    "Nominal unit labour cost per hour worked, fourth quarter of 2019 = 100": "Coste laboral unitario nominal por hora trabajada, cuarto trimestre de 2019 = 100",
    # living standards
    "Living standards": "Nivel de vida",
    "GDP per head in purchasing power, which corrects for price levels across countries, against the euro area; and the real disposable income of households per head, what families have to spend after taxes and benefits and after inflation, against the EU (Eurostat publishes no euro-area figure).":
        "El PIB per cápita en paridad de poder de compra, que corrige las diferencias de precios entre países, frente a la "
        "zona del euro; y la renta disponible real de los hogares per cápita, lo que las familias tienen para gastar "
        "después de impuestos y prestaciones y descontada la inflación, frente a la UE (Eurostat no publica la cifra de la "
        "zona del euro).",
    "GDP per head in purchasing power": "PIB per cápita en paridad de poder de compra",
    "EU = 100, purchasing power standards": "UE = 100, estándares de poder de compra",
    "Household income per head, after inflation": "Renta de los hogares per cápita, descontada la inflación",
    "Real gross disposable income of households per head, 2008 = 100": "Renta disponible bruta real de los hogares per cápita, 2008 = 100",
    "2008": "2008",
    "thousand hours": "miles de horas",
})
