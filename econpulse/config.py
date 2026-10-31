"""Project paths and shared settings."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACKAGE_DIR = ROOT / "econpulse"

REGISTRY_FILE = PACKAGE_DIR / "indicators.yaml"

DATA_DIR = ROOT / "data"
SERIES_DIR = DATA_DIR / "series"
CATALOG_FILE = DATA_DIR / "catalog.json"

TEMPLATES_DIR = ROOT / "templates"
STATIC_DIR = ROOT / "static"
SITE_DIR = ROOT / "site"

USER_AGENT = "EconPulseSpain/0.1 (economic dashboard; github.com/econpulse-spain)"
HTTP_TIMEOUT = 60  # seconds
FETCH_WORKERS = 6
