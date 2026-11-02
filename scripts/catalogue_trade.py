"""Spanish for the Trade page (Batch 33c-1): econpulse/trade.py, goods by product group and partner, services by type,
and export and import prices. The page's prose is in templates/es/trade.html; its section titles (trade.PAGE) are in
scripts/write_catalogue.py already. Read by scripts/write_catalogue.py; the keys are the English exactly as the code
writes it.
"""

PAIRS: dict[str, str] = {}

# ---------------------------------------------------------------- goods: the facts, the table and the charts
PAIRS.update({
    "Exports of goods": "Exportaciones de bienes",
    "Imports of goods": "Importaciones de bienes",
    "Trade balance": "Saldo comercial",
    "Balance without energy": "Saldo sin energía",
    "energy alone: {amount}": "solo la energía: {amount}",
    "12 months to {month}, {change} on a year earlier": "12 meses hasta {month}, {change} interanual",
    "€ billion over the past 12 months · through {period}": "Miles de millones de € en los últimos 12 meses · hasta {period}",
    "€ billion over the past four quarters · through {period}":
        "Miles de millones de € en los últimos cuatro trimestres · hasta {period}",
    "Share of exports %": "% de las exportaciones",
    "Product group": "Grupo de productos",
    "All goods": "Todos los bienes",
    "Changes compare the past 12 months with the 12 months before. Product groups gather chapters of the Harmonised System (see About the data).":
        "Las variaciones comparan los últimos 12 meses con los 12 anteriores. Los grupos de productos reúnen capítulos "
        "del Sistema Armonizado (véase Sobre los datos).",
    "Exports and imports of goods": "Exportaciones e importaciones de bienes",
    "€ billion over the past 12 months": "Miles de millones de € en los últimos 12 meses",
    "The trade balance and energy": "El saldo comercial y la energía",
    "Balance over the past 12 months, € billion": "Saldo de los últimos 12 meses, miles de millones de €",
    "Everything else": "Todo lo demás",
    "Exports by product group": "Exportaciones por grupo de productos",
    "Trade balance by product group": "Saldo comercial por grupo de productos",
    "Exports less imports, € billion, past 12 months":
        "Exportaciones menos importaciones, miles de millones de €, últimos 12 meses",
    "Export growth by product group": "Crecimiento de las exportaciones por grupo de productos",
    "Past 12 months, % change on the 12 months before": "Últimos 12 meses, variación sobre los 12 anteriores, %",
    "€ bn": "mm €",
    "Eurostat (balance of payments)": "Eurostat (balanza de pagos)",
    "Eurostat (national accounts)": "Eurostat (contabilidad nacional)",
})

# The product groups (trade.SECTIONS), also the names of the Harmonised System chapters' groups in About the data
PAIRS.update({
    "Meat, fish and dairy": "Carne, pescado y lácteos",
    "Fruit and vegetables": "Frutas y hortalizas",
    "Olive oil and fats": "Aceite de oliva y grasas",
    "Drinks and tobacco": "Bebidas y tabaco",
    "Other food and feed": "Otros alimentos y piensos",
    "Stone, ceramics and glass": "Piedra, cerámica y vidrio",
    "Metals and ores": "Metales y minerales",
    "Leather, wood and paper": "Cuero, madera y papel",
    "Chemicals": "Productos químicos",
    "Pharmaceuticals": "Productos farmacéuticos",
    "Plastics and rubber": "Plástico y caucho",
    "Textiles and clothing": "Textil y confección",
    "Machinery": "Maquinaria",
    "Electrical equipment": "Material eléctrico",
    "Vehicles and parts": "Vehículos y componentes",
    "Aircraft, ships and trains": "Aviones, barcos y trenes",
    "Other goods": "Otros bienes",
})

# ---------------------------------------------------------------- partners (trade.PARTNERS)
PAIRS.update({
    "All partners": "Todos los socios",
    "European Union": "Unión Europea",
    "France": "Francia",
    "Portugal": "Portugal",
    "Italy": "Italia",
    "Netherlands": "Países Bajos",
    "Belgium": "Bélgica",
    "Poland": "Polonia",
    "Outside the EU": "Fuera de la UE",
    "United Kingdom": "Reino Unido",
    "Switzerland": "Suiza",
    "Türkiye": "Turquía",
    "United States": "Estados Unidos",
    "Mexico": "México",
    "Brazil": "Brasil",
    "China": "China",
    "Japan": "Japón",
    "India": "India",
    "Morocco": "Marruecos",
    "Algeria": "Argelia",
    "Nigeria": "Nigeria",
    "Partner": "Socio",
    "Exports sold in the EU": "Exportaciones destinadas a la UE",
    "{amount} over the 12 months to {month}": "{amount} en los 12 meses hasta {month}",
    "Largest market": "Principal mercado",
    "Largest supplier": "Principal proveedor",
    "Largest deficit": "Mayor déficit",
    "{amount} of exports, {share}% of the total": "{amount} de exportaciones, el {share}% del total",
    "{amount} of imports, {share}% of the total": "{amount} de importaciones, el {share}% del total",
    "{amount} over the 12 months": "{amount} en los 12 meses",
    "The EU's share of Spain's goods trade": "El peso de la UE en el comercio de bienes de España",
    "% of exports and imports over the past 12 months": "% de las exportaciones y las importaciones de los últimos 12 meses",
    "Trade balance with selected partners": "Saldo comercial con algunos socios",
    "Exports less imports over the past 12 months, € billion":
        "Exportaciones menos importaciones en los últimos 12 meses, miles de millones de €",
    "Exports by partner": "Exportaciones por socio",
    "Trade balance by partner": "Saldo comercial por socio",
    "Where Spain's goods go and where they come from: the EU and the largest partners, over the past 12 months. Most exports go to the EU; imports lean more on China and on energy suppliers.":
        "Adónde van los bienes de España y de dónde vienen: la UE y los principales socios, en los últimos 12 meses. La "
        "mayor parte de las exportaciones va a la UE; las importaciones dependen más de China y de los proveedores de "
        "energía.",
    "Changes compare the past 12 months with the 12 months before. All goods, by country of destination for exports and of origin for imports.":
        "Las variaciones comparan los últimos 12 meses con los 12 anteriores. Todos los bienes, por país de destino de "
        "las exportaciones y de origen de las importaciones.",
})

# ---------------------------------------------------------------- services (trade.SERVICES, trade.BUSINESS)
PAIRS.update({
    "All services": "Todos los servicios",
    "Tourism and travel": "Turismo y viajes",
    "Transport": "Transporte",
    "Other business services": "Otros servicios empresariales",
    "Telecoms and IT": "Telecomunicaciones e informática",
    "Financial services": "Servicios financieros",
    "Insurance and pensions": "Seguros y pensiones",
    "Intellectual property": "Propiedad intelectual",
    "Research and development": "Investigación y desarrollo",
    "Consulting and professional": "Consultoría y servicios profesionales",
    "Technical and trade-related": "Servicios técnicos y relacionados con el comercio",
    "Business services": "Servicios empresariales",
    "Type of service": "Tipo de servicio",
    "Exports of services": "Exportaciones de servicios",
    "Imports of services": "Importaciones de servicios",
    "Services surplus": "Superávit de servicios",
    "Exports other than tourism": "Exportaciones distintas del turismo",
    "four quarters to {quarter}": "cuatro trimestres hasta {quarter}",
    "four quarters to {quarter}, {change} on a year earlier": "cuatro trimestres hasta {quarter}, {change} interanual",
    "{share}% of services exports": "el {share}% de las exportaciones de servicios",
    "{share}% of services exports, {change} on a year earlier":
        "el {share}% de las exportaciones de servicios, {change} interanual",
    "Exports and imports of services": "Exportaciones e importaciones de servicios",
    "€ billion over the past four quarters": "Miles de millones de € en los últimos cuatro trimestres",
    "Tourism and other services exports": "Exportaciones de turismo y de otros servicios",
    "Exports, € billion over the past four quarters": "Exportaciones, miles de millones de € en los últimos cuatro trimestres",
    "Business, IT and transport exports": "Exportaciones de servicios empresariales, informática y transporte",
    "Services exports by type": "Exportaciones de servicios por tipo",
    "Services balance by type": "Saldo de servicios por tipo",
    "Exports less imports, € billion, past four quarters":
        "Exportaciones menos importaciones, miles de millones de €, últimos cuatro trimestres",
    "Spain's exports and imports of services by type, from the balance of payments. Tourism is the largest single item, but the other services together bring in more than half of exports.":
        "Las exportaciones e importaciones de servicios de España por tipo, según la balanza de pagos. El turismo es la "
        "mayor partida, pero los demás servicios juntos aportan más de la mitad de las exportaciones.",
    "Changes compare the past four quarters with the four before. Other services are the total less the types shown: manufacturing and repair services, personal, cultural and government services, for which Eurostat publishes no separate Spanish figures.":
        "Las variaciones comparan los últimos cuatro trimestres con los cuatro anteriores. Otros servicios es el total "
        "menos los tipos que se muestran: servicios de transformación y de reparación, servicios personales, culturales "
        "y recreativos y servicios de las Administraciones públicas, de los que Eurostat no publica cifras separadas "
        "para España.",
})

# ---------------------------------------------------------------- export and import prices (trade.PRICES)
PAIRS.update({
    "Industrial goods": "Bienes industriales",
    "Intermediate goods": "Bienes intermedios",
    "Capital goods": "Bienes de equipo",
    "Consumer goods": "Bienes de consumo",
    "Industrial goods except energy": "Bienes industriales sin energía",
    "Export prices": "Precios de exportación",
    "Import prices": "Precios de importación",
    "Export ÷ import prices": "Precios de exportación ÷ de importación",
    "Index, 2021 = 100": "Índice, 2021 = 100",
    "Index, 2021 = 100 · {month}": "Índice, 2021 = 100 · {month}",
    "industrial goods, {month} on a year earlier": "bienes industriales, {month}, variación interanual",
    "Terms of trade": "Relación real de intercambio",
    "export prices relative to import prices, on a year earlier":
        "precios de exportación en relación con los de importación, variación interanual",
    "Export prices without energy": "Precios de exportación sin energía",
    "import prices without energy: {change}": "precios de importación sin energía: {change}",
    "Industrial goods, % change on a year earlier": "Bienes industriales, variación interanual, %",
    "Export deflator ÷ import deflator, 2015 = 100 (national accounts)":
        "Deflactor de las exportaciones ÷ deflactor de las importaciones, 2015 = 100 (contabilidad nacional)",
    "Goods and services": "Bienes y servicios",
    "Export prices by type of good": "Precios de exportación por tipo de bien",
    "Import prices by type of good": "Precios de importación por tipo de bien",
    "What Spanish industry charges abroad and what it pays for industrial goods bought from abroad. When export prices rise faster than import prices, the terms of trade improve and the same exports pay for more imports.":
        "Lo que cobra la industria española en el extranjero y lo que paga por los bienes industriales que compra "
        "fuera. Cuando los precios de exportación suben más deprisa que los de importación, la relación real de "
        "intercambio mejora y las mismas exportaciones pagan más importaciones.",
    "Export prices are the prices Spanish industry charges for products sold abroad; import prices are those of industrial products bought from abroad. Not seasonally adjusted.":
        "Los precios de exportación son los que cobra la industria española por los productos que vende en el "
        "extranjero; los de importación, los de los productos industriales comprados en el extranjero. Sin "
        "desestacionalizar.",
})
