"""The local server behind EconPulse.exe (no network beyond this computer)."""

import socket
import threading
import urllib.request

import pytest

from econpulse import serve


def test_free_port_skips_a_busy_one():
    busy = socket.socket()
    busy.bind(("127.0.0.1", 0))
    busy.listen()
    port = busy.getsockname()[1]
    try:
        assert serve.free_port(port, tries=5) != port
    finally:
        busy.close()


def test_serves_the_site_without_caching(tmp_path, monkeypatch):
    (tmp_path / "index.html").write_text("<p>Macroscope</p>", encoding="utf-8")
    port = serve.free_port(18765)
    stop = {}

    class Server(serve.http.server.ThreadingHTTPServer):
        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            stop["server"] = self

    monkeypatch.setattr(serve.http.server, "ThreadingHTTPServer", Server)
    thread = threading.Thread(target=serve.serve, kwargs={"site_dir": tmp_path, "port": port, "open_browser": False},
                              daemon=True)
    thread.start()
    for _ in range(50):
        if "server" in stop:
            break
        threading.Event().wait(0.05)
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/") as r:
            assert r.read() == b"<p>Macroscope</p>" and r.headers["Cache-Control"] == "no-store"
    finally:
        stop["server"].shutdown()
        thread.join(5)


def test_refuses_a_site_that_is_not_built(tmp_path):
    with pytest.raises(FileNotFoundError):
        serve.serve(site_dir=tmp_path, open_browser=False)
