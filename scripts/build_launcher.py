"""Build EconPulse.exe in the project folder from scripts/launcher/EconPulse.cs.

Uses the C# compiler that comes with Windows (.NET Framework 4), so nothing needs installing:
    .venv\\Scripts\\python.exe scripts\\build_launcher.py
"""

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "scripts" / "launcher" / "EconPulse.cs"
TARGET = ROOT / "EconPulse.exe"


def compiler() -> Path:
    windows = Path(os.environ.get("WINDIR", r"C:\Windows"))
    for framework in ("Framework64", "Framework"):
        csc = windows / "Microsoft.NET" / framework / "v4.0.30319" / "csc.exe"
        if csc.exists():
            return csc
    raise SystemExit("No C# compiler found (.NET Framework 4 is part of Windows 10 and 11).")


def main() -> int:
    result = subprocess.run([str(compiler()), "/nologo", "/optimize+", "/target:exe", "/platform:anycpu",
                             f"/out:{TARGET}", str(SOURCE)], capture_output=True, text=True)
    print(result.stdout.strip() or f"Built {TARGET}")
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
