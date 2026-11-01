"""A shared HTTP session with retries, used by every source client.

If a host stops answering (a connection error or a timeout, after the retries),
the rest of the run skips it instead of waiting through the same timeouts for
each of its series: those series keep their previous data and show as stale.
"""

import threading
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import HTTP_TIMEOUT, USER_AGENT

_local = threading.local()
_unreachable: set[str] = set()
_lock = threading.Lock()


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
