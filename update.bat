@echo off
rem Macroscope Spain: fetch the latest data, rebuild the site, open it.
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Setting up the Python environment, first run only...
  python -m venv .venv || goto :error
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt || goto :error
)

".venv\Scripts\python.exe" -m econpulse update || goto :error
start "" "site\index.html"
exit /b 0

:error
echo.
echo Update failed. See the messages above.
pause
exit /b 1
