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

SITE_URL = "https://enriquechueca93.github.io/macroscope-spain/"  # for absolute links, e.g. in the RSS feed

# Google Analytics 4, loaded only after a visitor accepts it in the cookie banner (static/consent.js). It stays off,
# with no banner, until all three are set: the property's measurement ID ("G-..."), and who runs the site and how to
# reach them, which the privacy notice must say (GDPR art. 13). SITE_CONTACT is a link: https://... or mailto:...
GA_MEASUREMENT_ID: str | None = None
SITE_OWNER: str | None = None
SITE_CONTACT: str | None = None

USER_AGENT ="MacroscopeSpain/0.1 (economic dashboard; personal project)"
HTTP_TIMEOUT = 60  # seconds
FETCH_WORKERS = 6
