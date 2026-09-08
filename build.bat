@echo off
echo ===================================================
echo   Compilador de NominaApp con PyInstaller
echo ===================================================
echo.

set PYTHON_CMD=.venv\Scripts\python.exe
if not exist %PYTHON_CMD% (
    set PYTHON_CMD=python
)

%PYTHON_CMD% build_exe.py

pause
