"""A shared HTTP session with retries, used by every source client.

If a host stops answering (a connection error or a timeout, after the retries),
the rest of the run skips it instead of waiting through the same timeouts for
each of its series: those series keep their previous data and show as stale.

A few servers leave out the intermediate certificate that links theirs to a trusted
root. For those hosts the request is verified against the usual roots plus that
intermediate, kept in econpulse/certs/ (verification stays on).
"""

import tempfile
import threading
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

import certifi
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import HTTP_TIMEOUT, USER_AGENT

_local = threading.local()
_unreachable: set[str] = set()
_lock = threading.Lock()
CERTS = Path(__file__).parent / "certs"
INTERMEDIATES = {"www.mites.gob.es": "fnmt-ac-componentes.pem"}   # host -> missing intermediate


@lru_cache(maxsize=None)
def ca_bundle(name: str) -> str:
    """A CA file with the usual trusted roots plus one intermediate certificate."""
    pem = Path(certifi.where()).read_text(encoding="ascii") + "\n" + (CERTS / name).read_text(encoding="ascii")
    with tempfile.NamedTemporaryFile("w", suffix=".pem", delete=False, encoding="ascii") as f:
        f.write(pem)
    return f.name


def session() -> requests.Session:
    """One session per thread (requests sessions are not thread-safe)."""
    s = getattr(_local, "session", None)
    if s is None:
        s = requests.Session()
        retry = Retry(
            total=3,
            backoff_factor=1.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET",),
        )
        s.mount("https://", HTTPAdapter(max_retries=retry))
        s.headers["User-Agent"] = USER_AGENT
        _local.session = s
    return s


def get(url: str, **kwargs) -> requests.Response:
    host = urlparse(url).hostname or ""
    if host in _unreachable:
        raise requests.ConnectionError(f"{host} did not answer earlier in this run; skipped")
    kwargs.setdefault("timeout", HTTP_TIMEOUT)
    if host in INTERMEDIATES:
        kwargs.setdefault("verify", ca_bundle(INTERMEDIATES[host]))
    try:
        r = session().get(url, **kwargs)
    except (requests.ConnectionError, requests.Timeout):
        with _lock:
            _unreachable.add(host)
        raise
    r.raise_for_status()
    return r


def reset() -> None:
    """Forget unreachable hosts (each run starts afresh; also used by tests)."""
    with _lock:
        _unreachable.clear()
