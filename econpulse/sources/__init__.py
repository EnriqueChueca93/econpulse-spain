"""Source clients.

Each module exposes fetch(key, params, *, since=None, freq=None) and source_url(key, params).
Clients with INCREMENTAL = True can't serve full history in one request; when given
`since` they return only recent observations, which fetch.py merges into the store.
"""

from . import bde, bis, bls, dbnomics, ecb, eia, eurostat, fred, ine, oecd, ree, segsocial, worldbank

CLIENTS = {
    "ine": ine,
    "eurostat": eurostat,
    "ecb": ecb,
    "bde": bde,
    "segsocial": segsocial,
    "fred": fred,
    "ree": ree,
    "oecd": oecd,
    "bis": bis,
    "bls": bls,
    "dbnomics": dbnomics,
    "eia": eia,
    "worldbank": worldbank,
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
    "oecd": "OECD",
    "bis": "BIS",
    "bls": "US BLS",
    "dbnomics": "US BEA (via DBnomics)",
    "eia": "US EIA",
    "worldbank": "World Bank",
    DERIVED: "EconPulse calculation",
}
