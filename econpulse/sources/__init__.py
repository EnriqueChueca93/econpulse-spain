"""Source clients.

Each module exposes fetch(key, params, *, since=None, freq=None) and source_url(key, params).
Clients with INCREMENTAL = True can't serve full history in one request; when given
`since` they return only recent observations, which fetch.py merges into the store.
"""

from . import bde, ecb, eurostat, fred, ine, ree, segsocial

CLIENTS = {
    "ine": ine,
    "eurostat": eurostat,
    "ecb": ecb,
    "bde": bde,
    "segsocial": segsocial,
    "fred": fred,
    "ree": ree,
}

# Computed from other indicators after fetching; see derived.py.
DERIVED = "derived"

SOURCE_NAMES = {
    "ine": "INE",
    "eurostat": "Eurostat",
    "ecb": "ECB",
    "bde": "Banco de España",
    "segsocial": "Seguridad Social",
    "fred": "FRED",
    "ree": "Red Eléctrica",
    DERIVED: "EconPulse calculation",
}
