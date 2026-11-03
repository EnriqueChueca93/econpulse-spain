"""Spanish for money and credit on the Financial page (Batch 35): the monetary survey, in the IMF's Spanish terms
(its "panorama monetario"). Read by scripts/write_catalogue.py; keys are the English exactly as econpulse/monetary.py
and pages.py write it.
"""

PAIRS: dict[str, str] = {}

PAIRS.update({
    "Money and credit: the monetary survey": "Dinero y crédito: el panorama monetario",
    "The IMF's monetary survey for Spain: the consolidated balance sheet of the Banco de España and the banks, which sets the money they create (broad money) against what backs it: claims on the rest of the world, on the government and on the private sector. The IMF's own figures end in February 2025; Macroscope rebuilds every line monthly from the ECB's and the Banco de España's statistics, within 0.2% of the IMF's on average where both exist (2015 to 2025). As a euro-area member, Spain counts the whole euro area as domestic.":
        "El panorama monetario de España del FMI: el balance consolidado del Banco de España y de los bancos, que enfrenta "
        "el dinero que crean (el dinero en sentido amplio) con lo que lo respalda: activos frente al resto del mundo, "
        "frente a las Administraciones públicas y frente al sector privado. Las cifras del propio FMI terminan en febrero "
        "de 2025; Macroscope reconstruye cada línea mes a mes con las estadísticas del BCE y del Banco de España, con una "
        "diferencia media del 0.2% respecto a las del FMI donde existen ambas (de 2015 a 2025). Como miembro de la zona "
        "del euro, España considera interna toda la zona del euro.",
    # facts
    "Broad money": "Dinero en sentido amplio",
    "{change} on a year earlier · {month}": "{change} interanual · {month}",
    "Claims on the private sector": "Activos frente al sector privado",
    "Net claims on general government": "Activos netos frente a las Administraciones públicas",
    "on a year earlier · {month}": "interanual · {month}",
    "Net foreign assets": "Activos exteriores netos",
    "claims on the rest of the world less liabilities to it · {month}": "activos frente al resto del mundo menos pasivos frente a él · {month}",
    # the survey table
    "Monetary survey": "Panorama monetario",
    "€ billion, end of month; change on a year earlier in %": "Miles de millones de €, fin de mes; variación interanual en %",
    "Domestic claims": "Activos internos",
    "Claims on general government": "Activos frente a las Administraciones públicas",
    "Less: central government deposits": "Menos: depósitos de la Administración central",
    "Claims on the private sector and other financial corporations": "Activos frente al sector privado y otras sociedades financieras",
    "of which loans to non-financial corporations": "de los cuales, préstamos a sociedades no financieras",
    "of which loans to households": "de los cuales, préstamos a hogares",
    "Broad money liabilities": "Pasivos incluidos en el dinero en sentido amplio",
    "Currency in circulation": "Efectivo en circulación",
    "Transferable deposits": "Depósitos transferibles",
    "Other deposits": "Otros depósitos",
    "Other liabilities and items": "Otros pasivos y partidas",
    "Deposits excluded from broad money": "Depósitos excluidos del dinero en sentido amplio",
    "Debt securities excluded from broad money": "Valores de deuda excluidos del dinero en sentido amplio",
    "Shares and other equity": "Acciones y otras participaciones de capital",
    "Other items (net)": "Otras partidas (neto)",
    "In the IMF's layout for euro-area members (euro-area-wide residency). Net claims on general government stand in for the IMF's net claims on central government, which public data can't split out. Claims on the private sector include banks' financial derivatives, as the IMF's do; the loans below them are a memo. Other items (net) balance the survey and hold, among others, the Banco de España's TARGET liability to the Eurosystem. Changes compare end-of-month stocks, so they include revaluations and reclassifications.":
        "Con el formato del FMI para los miembros de la zona del euro (residencia en toda la zona del euro). Los activos "
        "netos frente a las Administraciones públicas sustituyen a los activos netos frente a la Administración central del "
        "FMI, que los datos públicos no permiten separar. Los activos frente al sector privado incluyen los derivados "
        "financieros de los bancos, como los del FMI; los préstamos que figuran debajo son una partida informativa. Las "
        "otras partidas (neto) cuadran el panorama e incluyen, entre otras, la deuda TARGET del Banco de España con el "
        "Eurosistema. Las variaciones comparan saldos de fin de mes, así que incluyen revalorizaciones y reclasificaciones.",
    # charts
    "Where broad money growth comes from": "De dónde viene el crecimiento del dinero en sentido amplio",
    "Contributions to broad money growth on a year earlier, percentage points": "Aportaciones al crecimiento interanual del dinero en sentido amplio, puntos porcentuales",
    "Longer-term liabilities and other items": "Pasivos a más largo plazo y otras partidas",
    "Broad money and lending": "Dinero en sentido amplio y crédito",
    "% change on a year earlier, end-of-month stocks": "Variación interanual, %, saldos de fin de mes",
    "ECB; Banco de España; Macroscope calculation": "BCE; Banco de España; cálculo de Macroscope",
    "ECB; Banco de España": "BCE; Banco de España",
    "ECB and Banco de España (Macroscope calculation)": "BCE y Banco de España (cálculo de Macroscope)",
})
