@echo off
setlocal
cd /d "%~dp0"
python adapter.py --host 127.0.0.1 --port 8787
