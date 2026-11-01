"""Project paths and shared settings."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACKAGE_DIR = ROOT / "econpulse"

REGISTRY_FILE = PACKAGE_DIR / "indicators.yaml"
FORECASTS_FILE = PACKAGE_DIR / "forecasts.yaml"  # forecasts entered by hand

DATA_DIR = ROOT / "data"
SERIES_DIR = DATA_DIR / "series"
CATALOG_FILE = DATA_DIR / "catalog.json"

TEMPLATES_DIR = ROOT / "templates"
STATIC_DIR = ROOT / "static"
SITE_DIR = ROOT / "site"

SITE_URL = "https://enriquechueca93.github.io/econpulse-spain/"  # for absolute links, e.g. in the RSS feed

USER_AGENT = "EconPulseSpain/0.1 (economic dashboard; personal project)"
HTTP_TIMEOUT = 60  # seconds
FETCH_WORKERS = 6
