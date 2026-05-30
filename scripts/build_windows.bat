@echo off
setlocal
cd /d %~dp0\..
if not exist .venv (
  py -3 -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
pyinstaller --noconfirm --clean --windowed --name cc2-dash-companion app.py
if errorlevel 1 exit /b %errorlevel%
echo.
echo Built dist\cc2-dash-companion.exe
