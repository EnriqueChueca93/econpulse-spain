"""A host that stops answering is skipped for the rest of the run (no network)."""

import pytest
import requests

from econpulse import http


class FakeSession:
    def __init__(self):
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append(url)
        if "slow.example" in url:
            raise requests.ReadTimeout("read timed out")
        response = requests.Response()
        response.status_code = 200
        return response


def test_unreachable_host_is_skipped_for_the_rest_of_the_run(monkeypatch):
    fake = FakeSession()
    monkeypatch.setattr(http, "session", lambda: fake)
    http.reset()
    with pytest.raises(requests.Timeout):
        http.get("https://slow.example/a.csv")
    with pytest.raises(requests.ConnectionError, match="skipped"):
        http.get("https://slow.example/b.csv")
    assert http.get("https://fine.example/c.csv").status_code == 200
    assert fake.calls == ["https://slow.example/a.csv", "https://fine.example/c.csv"]  # b was never requested
    http.reset()
