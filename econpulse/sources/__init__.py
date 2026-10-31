"""Source clients. Each module exposes fetch(key, params) and source_url(key, params)."""

from . import ecb, eurostat, ine

CLIENTS = {
    "ine": ine,
    "eurostat": eurostat,
    "ecb": ecb,
}

# Computed from other indicators after fetching; see derived.py.
DERIVED = "derived"

SOURCE_NAMES = {
    "ine": "INE",
    "eurostat": "Eurostat",
    "ecb": "ECB",
    DERIVED: "EconPulse calculation",
}
