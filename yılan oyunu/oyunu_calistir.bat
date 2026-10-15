@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if not errorlevel 1 (
    py -3 "%~dp0yilan_oyunu.py"
    exit /b %errorlevel%
)

where python >nul 2>nul
if not errorlevel 1 (
    python "%~dp0yilan_oyunu.py"
    exit /b %errorlevel%
)

where pythonw >nul 2>nul
if not errorlevel 1 (
    pythonw "%~dp0yilan_oyunu.py"
    exit /b %errorlevel%
)

echo Python yüklu degil. Lutfen Python kurup tekrar deneyin.
pause
