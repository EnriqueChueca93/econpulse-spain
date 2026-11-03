"""Spanish for the site-wide pieces finished in Batch 33d: the search index and the RSS feed.
Read by scripts/write_catalogue.py; the keys are the English exactly as econpulse/search.py and feed.py write it.
"""

PAIRS: dict[str, str] = {}

PAIRS.update({
    # the search index
    "Page": "Página",
    "sources methodology": "fuentes metodología",
    # the RSS feed (site/es/feed.xml)
    "Macroscope Spain: what changed": "Macroscope España: qué ha cambiado",
    "New releases, revisions and big market moves in Spain's economic data, one item per change, as found by each Macroscope Spain update.":
        "Nuevas publicaciones, revisiones y grandes movimientos de mercado en los datos económicos de España, una "
        "entrada por cambio, tal como los detecta cada actualización de Macroscope España.",
    "New data": "Nuevos datos",
    "Revision": "Revisión",
    "Market move": "Movimiento de mercado",
    "Update": "Actualización",
})
