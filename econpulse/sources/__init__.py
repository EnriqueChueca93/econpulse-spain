"""Source clients.

Each module exposes fetch(key, params, *, since=None, freq=None) and source_url(key, params).
Clients with INCREMENTAL = True can't serve full history in one request; when given
`since` they return only recent observations, which fetch.py merges into the store.
"""

from . import (afiliacion, ageing, bde, bdeproj, bel, bis, bls, bundesbank, comext, dbnomics, ecb, eia, eurostat, fred, funcas, hicpdist, imf, ine,
               oecd, oilbulletin, ree, reg, segsocial, worldbank)

CLIENTS = {
    "ine": ine,
    "eurostat": eurostat,
    "ecb": ecb,
    "bde": bde,
    "segsocial": segsocial,
    "afiliacion": afiliacion,
    "fred": fred,
    "ree": ree,
    "oecd": oecd,
    "bis": bis,
    "bls": bls,
    "dbnomics": dbnomics,
    "eia": eia,
    "worldbank": worldbank,
    "bundesbank": bundesbank,
    "imf": imf,
    "bdeproj": bdeproj,
    "funcas": funcas,
    "hicpdist": hicpdist,
    "ageing": ageing,
    "reg": reg,
    "bel": bel,
    "comext": comext,
    "oilbulletin": oilbulletin,
}

# Computed from other indicators after fetching; see derived.py.
DERIVED = "derived"

SOURCE_NAMES = {
    "ine": "INE",
    "eurostat": "Eurostat",
    "ecb": "ECB",
    "bde": "Banco de España",
    "segsocial": "Seguridad Social",
    "afiliacion": "Seguridad Social",
    "fred": "FRED",
    "ree": "Red Eléctrica",
    "oecd": "OECD",
    "bis": "BIS",
    "bls": "US BLS",
    "dbnomics": "DBnomics",
    "eia": "US EIA",
    "worldbank": "World Bank",
    "bundesbank": "Bundesbank",
    "imf": "IMF",
    "bdeproj": "Banco de España",
    "funcas": "FUNCAS",
    "hicpdist": "Eurostat (EconPulse calculation)",
    "ageing": "Eurostat (EconPulse calculation)",
    "reg": "Ministerio de Trabajo",
    "bel": "Ministerio de Trabajo",
    "comext": "Eurostat (Comext)",
    "oilbulletin": "European Commission (Weekly Oil Bulletin)",
    DERIVED: "EconPulse calculation",
}

# EconPulse calculations made while fetching, from another publisher's data: charts credit both.
CALCULATED_FROM = {"hicpdist": "Eurostat", "ageing": "Eurostat"}

# DBnomics mirrors several agencies; credit the one behind the series (the key's first part).
DBNOMICS_PROVIDERS = {"BEA": "US BEA (via DBnomics)", "AMECO": "European Commission (via DBnomics)"}


def source_name(source: str, key: str = "") -> str:
    """Who publishes an indicator's data, as shown on the site."""
    if source == "dbnomics":
        return DBNOMICS_PROVIDERS.get(key.split("/", 1)[0], SOURCE_NAMES[source])
    return SOURCE_NAMES.get(source, source)
