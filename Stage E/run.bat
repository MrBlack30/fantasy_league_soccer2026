@echo off
REM ============================================================
REM  Fantasy League Manager - Stage E launcher (Windows)
REM ============================================================
cd /d "%~dp0app"
echo Starting Fantasy League Manager...
python app.py
if errorlevel 1 (
    echo.
    echo The app exited with an error. Make sure you have installed the
    echo requirements:   pip install -r ..\requirements.txt
    echo and that the PostgreSQL container is running.
    pause
)
