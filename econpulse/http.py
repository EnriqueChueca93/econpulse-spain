"""A shared HTTP session with retries, used by every source client."""

import threading

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import HTTP_TIMEOUT, USER_AGENT

_local = threading.local()


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
    kwargs.setdefault("timeout", HTTP_TIMEOUT)
    r = session().get(url, **kwargs)
    r.raise_for_status()
    return r
