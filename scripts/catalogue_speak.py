"""Spanish for ECB-speak and the global central bank stance page (Batch 33d): econpulse/ecbspeak.py (with the word-list
groups of econpulse/speechscore.py) and econpulse/stance.py. The pages' prose is in templates/es/ecb-speak.html and
templates/es/stance.html. Read by scripts/write_catalogue.py; the keys are the English exactly as the code writes it.

Hawkish and dovish are "restrictivo" and "acomodaticio" throughout (the ECB's own Spanish for a policy stance), with
"halcón" and "paloma" mentioned once on the page. Speech titles, quotations, Econvitals' decision summaries and desk notes
stay in English, as published.
"""

PAIRS: dict[str, str] = {}

# ---------------------------------------------------------------- ECB-speak: the members
PAIRS.update({
    # The euro-area national central banks (ecbspeak.NCBS): names in their own language stay as they are.
    "National Bank of Belgium": "Banco Nacional de Bélgica",
    "Deutsche Bundesbank": "Deutsche Bundesbank",
    "Eesti Pank": "Eesti Pank",
    "Central Bank of Ireland": "Banco Central de Irlanda",
    "Bank of Greece": "Banco de Grecia",
    "Banque de France": "Banque de France",
    "Croatian National Bank": "Banco Nacional de Croacia",
    "Banca d'Italia": "Banca d'Italia",
    "Central Bank of Cyprus": "Banco Central de Chipre",
    "Latvijas Banka": "Latvijas Banka",
    "Bank of Lithuania": "Banco de Lituania",
    "Banque centrale du Luxembourg": "Banque centrale du Luxembourg",
    "Central Bank of Malta": "Banco Central de Malta",
    "De Nederlandsche Bank": "De Nederlandsche Bank",
    "Oesterreichische Nationalbank": "Oesterreichische Nationalbank",
    "Banco de Portugal": "Banco de Portugal",
    "Banka Slovenije": "Banka Slovenije",
    "Národná banka Slovenska": "Národná banka Slovenska",
    "Bank of Finland": "Banco de Finlandia",
    "Bulgarian National Bank": "Banco Nacional de Bulgaria",
    # Roles ("BCE · Presidenta", "Banco de Finlandia · Gobernador"); "(woman)" marks the feminine (ecbspeak.WOMEN).
    "President": "Presidente",
    "President (woman)": "Presidenta",
    "Vice-President": "Vicepresidente",
    "Vice-President (woman)": "Vicepresidenta",
    "Executive Board": "Comité Ejecutivo",
    "Governor": "Gobernador",
    "Governor (woman)": "Gobernadora",
    "quiet lately": "sin intervenciones recientes",
})

# ---------------------------------------------------------------- ECB-speak: the charts and the callout
PAIRS.update({
    "dovish": "acomodaticio",
    "hawkish": "restrictivo",
    "Current standings": "Posiciones actuales",
    "Score, −100 dovish to +100 hawkish": "Puntuación, de −100 (acomodaticio) a +100 (restrictivo)",
    "Committee tone": "Tono del Consejo",
    "Each meeting cycle, −100 dovish to +100 hawkish": "Cada ciclo de reuniones, de −100 (acomodaticio) a +100 (restrictivo)",
    "Committee": "Consejo de Gobierno",
    "Most hawkish quarter of members": "Cuarto más restrictivo de los miembros",
    "Most dovish quarter": "Cuarto más acomodaticio",
    "ECB and BIS speeches; Macroscope word-list scores":
        "Discursos del BCE y del BPI; puntuaciones de Macroscope con listas de palabras",
    "{tone} in the {n} cycle that ended in a rate rise": "{tone} en {n} ciclo que terminó con una subida de tipos",
    "{tone} in the {n} cycles that ended in a rate rise": "{tone} en los {n} ciclos que terminaron con una subida de tipos",
    "{tone} in the {n} cycle that ended in a cut": "{tone} en {n} ciclo que terminó con una bajada de tipos",
    "{tone} in the {n} cycles that ended in a cut": "{tone} en los {n} ciclos que terminaron con una bajada de tipos",
    "{tone} in the {n} cycle that ended with rates on hold": "{tone} en {n} ciclo que terminó con los tipos sin cambios",
    "{tone} in the {n} cycles that ended with rates on hold":
        "{tone} en los {n} ciclos que terminaron con los tipos sin cambios",
    "Does it track what the ECB did? The committee's tone averaged {listed}.":
        "¿Sigue lo que hizo el BCE? El tono medio del Consejo fue de {listed}.",
})

# ---------------------------------------------------------------- ECB-speak: the word lists (speechscore.py)
# The lists match English, the language of the speeches; the page says so and shows the exact patterns.
PAIRS.update({
    "Price pressures rising": "Presiones de precios al alza",
    "Upside risks to inflation": "Riesgos al alza para la inflación",
    "Rates up or staying restrictive": "Tipos al alza o todavía restrictivos",
    "Strong economy or tight labour market": "Economía fuerte o mercado laboral tensionado",
    "Price pressures easing": "Presiones de precios que se moderan",
    "Downside risks to inflation": "Riesgos a la baja para la inflación",
    "Rates down or less restrictive": "Tipos a la baja o menos restrictivos",
    "Weak economy or rising unemployment": "Economía débil o paro en aumento",
    "rising, higher, elevated, persistent, sticky, accelerating or upward near inflation, prices, wages, inflation "
    "expectations or second-round effects; and inflation “remaining high”, “picking up” or “above target”":
        "al alza, más alta, elevada, persistente, rígida, acelerándose o ascendente junto a inflación, precios, salarios, "
        "expectativas de inflación o efectos de segunda ronda; e inflación que «sigue alta», «repunta» o «está por encima "
        "del objetivo»",
    "“upside risks to inflation”, “risks to the inflation outlook … to the upside”":
        "«riesgos al alza para la inflación», «riesgos para las perspectivas de inflación … al alza»",
    "raising, hiking or tightening rates; rate hikes; further tightening; restrictive stance; higher for longer; too "
    "early to cut; wage-price spiral":
        "subir o endurecer los tipos; subidas de tipos; más endurecimiento; orientación restrictiva; tipos más altos durante "
        "más tiempo; demasiado pronto para bajar; espiral de precios y salarios",
    "strong, robust, resilient or solid growth, demand or labour market; tight labour markets; low unemployment; labour "
    "shortages":
        "crecimiento, demanda o mercado laboral fuerte, robusto, resiliente o sólido; mercados laborales tensionados; paro "
        "bajo; escasez de mano de obra",
    "lower, falling, declining, easing, moderating, subdued or downward near inflation, prices or wages; and inflation "
    "“coming down”, “below target” or “on track to return”":
        "más baja, en descenso, a la baja, moderándose, contenida o descendente junto a inflación, precios o salarios; e "
        "inflación que «baja», «está por debajo del objetivo» o «va camino de volver» a él",
    "“downside risks to inflation”, undershooting":
        "«riesgos a la baja para la inflación», quedarse por debajo del objetivo",
    "cutting, lowering or easing rates; rate cuts; less restrictive; more accommodative; stimulus; dialling back; "
    "supporting the economy":
        "bajar o relajar los tipos; bajadas de tipos; menos restrictiva; más acomodaticia; estímulo; reducir la "
        "restricción; apoyar la economía",
    "weak, sluggish, subdued or fragile growth or demand; recession; contraction; downturn; downside risks to growth; "
    "rising unemployment":
        "crecimiento o demanda débil, lento, contenido o frágil; recesión; contracción; desaceleración; riesgos a la baja "
        "para el crecimiento; paro en aumento",
})

# ---------------------------------------------------------------- central bank stance: the banks
# The twelve in the matrix, and the others in the diffusion lists (Econvitals' BIS names). Bank of Japan, Bank of
# England, Bank of Canada and National Bank of Poland are in scripts/write_catalogue.py already.
PAIRS.update({
    "Federal Reserve": "Reserva Federal",
    "US Federal Reserve System": "Reserva Federal",
    "European Central Bank": "Banco Central Europeo",
    "Reserve Bank of Australia": "Banco de la Reserva de Australia",
    "Swiss National Bank": "Banco Nacional Suizo",
    "Sveriges Riksbank": "Sveriges Riksbank",
    "Norges Bank": "Norges Bank",
    "Reserve Bank of New Zealand": "Banco de la Reserva de Nueva Zelanda",
    "People's Bank of China": "Banco Popular de China",
    "Reserve Bank of India": "Banco de la Reserva de la India",
    "Bangko Sentral ng Pilipinas": "Bangko Sentral ng Pilipinas",
    "Bank Indonesia": "Bank Indonesia",
    "Bank Negara Malaysia": "Bank Negara Malaysia",
    "Bank of Israel": "Banco de Israel",
    "Bank of Korea": "Banco de Corea",
    "Bank of Mexico": "Banco de México",
    "Bank of Russia": "Banco de Rusia",
    "Bank of Thailand": "Banco de Tailandia",
    "Central Bank of Brazil": "Banco Central de Brasil",
    "Central Bank of Chile": "Banco Central de Chile",
    "Central Bank of Colombia": "Banco de la República (Colombia)",
    "Central Bank of Iceland": "Banco Central de Islandia",
    "Central Bank of Kuwait": "Banco Central de Kuwait",
    "Central Bank of the Republic of Turkey": "Banco Central de la República de Turquía",
    "Central Reserve Bank of Peru": "Banco Central de Reserva del Perú",
    "Czech National Bank": "Banco Nacional Checo",
    "Danmarks Nationalbank": "Danmarks Nationalbank",
    "Hong Kong Monetary Authority": "Autoridad Monetaria de Hong Kong",
    "Hungarian National Bank": "Banco Nacional de Hungría",
    "National Bank of Romania": "Banco Nacional de Rumanía",
    "National Bank of Serbia": "Banco Nacional de Serbia",
    "National Bank of the Republic of Macedonia": "Banco Nacional de la República de Macedonia del Norte",
    "Saudi Arabian Monetary Authority": "Autoridad Monetaria de Arabia Saudí",
    "South African Reserve Bank": "Banco de la Reserva de Sudáfrica",
    "SNB": "BNS",   # the ranked charts' short names; ECB -> BCE is in write_catalogue.py, the others stay
    # Countries not in the catalogue yet
    "Australia": "Australia",
    "Sweden": "Suecia",
    "Norway": "Noruega",
    "New Zealand": "Nueva Zelanda",
    # Each bank's policy rate
    "Federal Funds Rate (target range)": "Tipo de los fondos federales (horquilla objetivo)",
    "Deposit Facility Rate": "Tipo de la facilidad de depósito",
    "Overnight Call Rate": "Tipo de interés a un día (call rate)",
    "Bank Rate": "Tipo oficial (Bank Rate)",
    "Overnight Rate": "Tipo a un día (overnight rate)",
    "Cash Rate": "Tipo oficial (cash rate)",
    "SNB Policy Rate": "Tipo oficial del BNS",
    "Policy Rate": "Tipo oficial",
    "Official Cash Rate": "Tipo oficial (OCR)",
    "1-Year Loan Prime Rate (LPR)": "Tipo preferencial de los préstamos a un año (LPR)",
    "Policy Repo Rate": "Tipo repo oficial",
})

# ---------------------------------------------------------------- central bank stance: the cycle, the desks, the markets
PAIRS.update({
    # Cycle phases (Econvitals' rule) and the automatic lean that follows from them
    "Hiking": "Subiendo",
    "Cutting": "Bajando",
    "On Hold": "Sin cambios",
    "Paused": "Pausa prolongada",
    "In a hiking cycle (rule)": "En un ciclo de subidas (regla)",
    "In a cutting cycle (rule)": "En un ciclo de bajadas (regla)",
    "On hold (rule)": "Sin cambios (regla)",
    "Long pause (rule)": "Pausa prolongada (regla)",
    # Moves: a desk's call, the market's most likely outcome
    "hike": "subida",
    "hold": "sin cambios",
    "cut": "bajada",
    "{cut} cut · {hold} hold · {hike} hike": "{cut} bajada · {hold} sin cambios · {hike} subida",
    # The desks' tally ("subida: 10 · sin cambios: 2 · 12 casas de análisis") and consensus
    "{n} hike": "subida: {n}",
    "{n} hold": "sin cambios: {n}",
    "{n} cut": "bajada: {n}",
    "{n} house": "{n} casa de análisis",
    "{n} houses": "{n} casas de análisis",
    "Hike": "Subida",
    "Hold": "Sin cambios",
    "Cut": "Bajada",
    "Split": "Opiniones divididas",
    "unanimous": "por unanimidad",
    # Market sources (Kalshi and Polymarket stay as they are)
    "ASX futures": "Futuros de la ASX",
    "Bank of England OIS curve": "Curva OIS del Banco de Inglaterra",
    "CME futures (chartbook)": "Futuros del CME (chartbook)",
})

# ---------------------------------------------------------------- central bank stance: the charts
PAIRS.update({
    "Global policy diffusion index": "Índice global de difusión de la política monetaria",
    "Share of {n} central banks hiking minus share cutting, %, monthly":
        "Porcentaje de los {n} bancos centrales que suben tipos menos el de los que los bajan, %, mensual",
    "Share hiking": "Suben tipos",
    "Share cutting": "Bajan tipos",
    "Econvitals, from BIS central bank policy rates (CC0)":
        "Econvitals, a partir de los tipos oficiales de los bancos centrales que recopila el BPI (CC0)",
    "Policy rates, nominal": "Tipos oficiales, nominales",
    "%, highest to lowest": "%, de mayor a menor",
    "Policy rates, real": "Tipos oficiales, reales",
    "%, after core inflation over the last 12 months": "%, descontada la inflación subyacente de los últimos 12 meses",
    "Central bank": "Banco central",
    "Econvitals (CC0): BIS and central banks; core inflation from national agencies":
        "Econvitals (CC0): BPI y bancos centrales; inflación subyacente de los institutos de estadística nacionales",
})
