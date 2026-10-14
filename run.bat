@echo off
setlocal enabledelayedexpansion
title Spamify AI - SMS & Email Spam Filter

echo ============================================================
echo   Spamify AI - High-Accuracy Spam and Phishing Detection
echo ============================================================
echo.

set "PYCMD="

:: 1. Check direct actual Python installation paths first (bypassing Windows Store stub)
if exist "%LOCALAPPDATA%\Python\bin\python.exe" (
    set "PYCMD=%LOCALAPPDATA%\Python\bin\python.exe"
    goto :found_python
)

if exist "%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe" (
    set "PYCMD=%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe"
    goto :found_python
)

if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" (
    set "PYCMD=%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    goto :found_python
)

:: 2. Check Python Launcher 'py'
py --version >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    set "PYCMD=py"
    goto :found_python
)

:: 3. Check if standard python works (not windows store stub)
python -c "import sys; sys.exit(0)" >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    set "PYCMD=python"
    goto :found_python
)

echo [ERROR] Python was not found in standard paths.
echo Please install Python from python.org or run using: py app.py
pause
exit /b 1

:found_python
echo [*] Detected Python engine: "%PYCMD%"
"%PYCMD%" --version
echo.

if not exist "models\spam_model.joblib" (
    echo [*] Model artifact not found. Training model now...
    "%PYCMD%" train.py
)

echo [*] Launching Spamify Web Application...
echo [*] Open your browser at: http://127.0.0.1:5000
echo [*] Press Ctrl+C in this terminal window to stop the server.
echo.
"%PYCMD%" app.py
pause
