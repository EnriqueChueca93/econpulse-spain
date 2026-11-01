"""US Energy Information Administration: daily spot prices from its public history pages
(the same data FRED republishes); no key needed.

Key is the EIA series code, e.g. RBRTE (Europe Brent spot price FOB, $/barrel). The page
lists one row per week ("2026 Oct-26 to Oct-30") with Monday-to-Friday prices.
"""

import re

import pandas as pd

from .. import http
from .base import FetchResult, make_series

PAGE = "https://www.eia.gov/dnav/pet/hist/LeafHandler.ashx"
_WEEK = re.compile(r"<td class='B6'>(?:&nbsp;)*\s*(\d{4}) ([A-Z][a-z]{2})-\s?(\d{1,2}) to [^<]*</td>((?:\s*<td class='B3'>[^<]*</td>){5})")
_CELL = re.compile(r"<td class='B3'>([^<]*)</td>")


def source_url(key: str, params: dict | None = None) -> str:
    return f"{PAGE}?n=PET&s={key}&f=D"


def parse(html: str) -> FetchResult:
    dates, values = [], []
    for year, month, day, cells in _WEEK.findall(html):
        monday = pd.Timestamp(f"{day} {month} {year}")
        for i, value in enumerate(_CELL.findall(cells)):
            if value.strip():
                dates.append(monday + pd.Timedelta(days=i))
                values.append(value.replace(",", ""))
    return FetchResult(make_series(dates, values))


def fetch(key: str, params: dict | None = None, **_) -> FetchResult:
    return parse(http.get(PAGE, params={"n": "PET", "s": key, "f": "D"}).text)
