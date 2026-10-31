"""INE (Instituto Nacional de Estadística) JSON API.

Docs: https://www.ine.es/dyngs/DataLab/manual.html?cid=45
A series is fetched by its code, e.g. IPC290750 (CPI, annual rate of change).
"""

import pandas as pd

from .. import http
from .base import FetchResult, make_series

BASE = "https://servicios.ine.es/wstempus/js/ES"

# FK_Periodo codes: 1-12 are months, 19-22 are quarters 1-4, 28 is a full year.
_QUARTER_CODES = {19: 1, 20: 4, 21: 7, 22: 10}
_ANNUAL_CODE = 28
# FK_TipoDato: 1 = final, 2 = provisional, 3 = advance (flash) estimate.
_FLASH = 3


def source_url(key: str, params: dict | None = None) -> str:
    return f"https://www.ine.es/consul/serie.do?s={key}"


def _date(obs: dict) -> pd.Timestamp:
    year, period = obs["Anyo"], obs["FK_Periodo"]
    if 1 <= period <= 12:
        return pd.Timestamp(year, period, 1)
    if period in _QUARTER_CODES:
        return pd.Timestamp(year, _QUARTER_CODES[period], 1)
    if period == _ANNUAL_CODE:
        return pd.Timestamp(year, 1, 1)
    # Unknown period code: fall back to the timestamp, which INE gives in Madrid time.
    return pd.Timestamp(obs["Fecha"], unit="ms", tz="UTC").tz_convert("Europe/Madrid").tz_localize(None).normalize()


def parse(payload: dict) -> FetchResult:
    obs = [o for o in payload.get("Data", []) if o.get("Valor") is not None and not o.get("Secreto")]
    series = make_series((_date(o) for o in obs), (o["Valor"] for o in obs))
    meta = {"flash": obs[-1].get("FK_TipoDato") == _FLASH, "source_name": payload.get("Nombre", "").strip()}
    return FetchResult(series, meta)


def fetch(key: str, params: dict | None = None) -> FetchResult:
    payload = http.get(f"{BASE}/DATOS_SERIE/{key}", params={"nult": 5000}).json()
    return parse(payload)
