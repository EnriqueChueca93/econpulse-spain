"""Spanish for the equities block on the Financial page (Batch 34c): the IBEX 35 and the Madrid exchange's sectors.
Read by scripts/write_catalogue.py; the keys are the English exactly as econpulse/equities.py and pages.py write it.
The sector names are the Bolsa de Madrid's own.
"""

PAIRS: dict[str, str] = {}

PAIRS.update({
    "Equities: the IBEX 35 and the Madrid sectors": "Renta variable: el IBEX 35 y los sectores de la Bolsa de Madrid",
    "Spain's main share index and the Madrid exchange's six sector indices, as the Banco de España publishes them: daily closes, one or two trading days later. Not a live feed: the page is rebuilt once a day. Prices for individual companies are not shown, as no free source allows them to be republished.":
        "El principal índice bursátil de España y los seis índices sectoriales de la Bolsa de Madrid, tal como los "
        "publica el Banco de España: cierres diarios, con uno o dos días hábiles de retraso. No es un servicio en tiempo "
        "real: la página se actualiza una vez al día. No se muestran las cotizaciones de cada empresa, porque ninguna "
        "fuente gratuita permite volver a publicarlas.",
    # facts
    "close of {day}": "cierre del {day}",
    "On the day": "En el día",
    "Over a week": "En una semana",
    "Over a year": "En un año",
    # the table
    "Close; changes in %": "Cierre; variaciones en %",
    "Madrid general index": "Índice General de Madrid",
    "Sectors": "Sectores",
    "Financial services and real estate": "Servicios financieros e inmobiliarios",
    "Oil and energy": "Petróleo y energía",
    "Basic materials, industry and construction": "Materiales básicos, industria y construcción",
    "Consumer services": "Servicios de consumo",
    "Technology and telecommunications": "Tecnología y telecomunicaciones",
    # the charts
    "The Madrid exchange by sector": "La Bolsa de Madrid por sectores",
    "% change to the close of {day}: rises in blue, falls in red": "Variación hasta el cierre del {day}, %: subidas en azul, caídas en rojo",
    "Last trading day": "Última sesión",
    "Past week": "Última semana",
    "Bolsa de Madrid and CNMV, via the Banco de España": "Bolsa de Madrid y CNMV, a través del Banco de España",
    "The IBEX 35 since 2007": "El IBEX 35 desde 2007",
    "The sectors since the end of 2019": "Los sectores desde finales de 2019",
    "End of 2019": "Final de 2019",
    "Madrid exchange sector indices, last close of 2019 = 100": "Índices sectoriales de la Bolsa de Madrid, último cierre de 2019 = 100",
})
