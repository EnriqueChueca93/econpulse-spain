"""Serve the built site on this computer and open it in the browser (python -m econpulse serve).

Only this computer can reach it (127.0.0.1). It uses the first free port from 8765, sends no
caching headers so a rebuild shows on the next reload, and runs until the window is closed or
Ctrl+C is pressed. EconPulse.exe in the project folder runs this command (scripts/launcher/).
"""

import functools
import http.server
import socket
import threading
import webbrowser
from pathlib import Path

from .config import SITE_DIR

FIRST_PORT = 8765


def free_port(start: int = FIRST_PORT, tries: int = 50) -> int:
    for port in range(start, start + tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
            except OSError:
                continue
            return port
    raise OSError(f"no free port between {start} and {start + tries - 1}")


class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args) -> None:   # keep the window for Macroscope's own messages
        pass

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


def serve(site_dir: Path = SITE_DIR, port: int | None = None, open_browser: bool = True) -> None:
    if not (site_dir / "index.html").exists():
        raise FileNotFoundError(f"{site_dir / 'index.html'} does not exist yet: build the site first")
    port = port or free_port()
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(Handler, directory=str(site_dir)))
    url = f"http://localhost:{port}/"
    print(f"\nMacroscope Spain is running at {url}\nClose this window, or press Ctrl+C, to stop it.\n", flush=True)
    if open_browser:
        threading.Timer(0.5, webbrowser.open, args=(url,)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Stopped.")
    finally:
        server.server_close()
