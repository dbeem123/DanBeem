@echo off
setlocal EnableExtensions
set "BACKEND_ROOT=%~dp0"
for %%I in ("%BACKEND_ROOT%..\..") do set "REPO_ROOT=%%~fI"
set "PYTHON=%REPO_ROOT%\.venv\Scripts\python.exe"
if not exist "%PYTHON%" (
  >&2 echo ERROR: dedicated .venv is missing: "%PYTHON%"
  exit /b 1
)
if not exist "%BACKEND_ROOT%artifacts" mkdir "%BACKEND_ROOT%artifacts"
rem Access issuer/audience/JWKS are deployment inputs only; this local CLI does not fetch or print them.
rem If an authenticated integration later needs them, provide DANBOT_ACCESS_* in the process environment.
"%PYTHON%" "%BACKEND_ROOT%backend.py" --port 8765 --db "%BACKEND_ROOT%danbot_studio.sqlite3" --artifacts "%BACKEND_ROOT%artifacts"
set "EXITCODE=%ERRORLEVEL%"
endlocal & exit /b %EXITCODE%
