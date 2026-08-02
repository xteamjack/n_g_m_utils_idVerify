@echo off
SETLOCAL ENABLEDELAYEDEXPANSION

:: idVerifyServer/start.bat — Windows launcher for the ID-verification
:: Python backend. Mirrors the entityExplorer pattern. Called by
:: utils/scripts/pServ-start.bat as IDVS.

:: Determine the directory containing this script (the project root)
SET "SERVER_DIR=%~dp0"
cd /d "%SERVER_DIR%"

:: Resolve the path to the sans-env.bat utility script. This script lives at
:: <repoRoot>\<category>\<app>\server\, so the repo root (which holds
:: utils\scripts) is THREE levels up from SERVER_DIR (post category-reorg).
SET "SANS_ENV_BAT=%SERVER_DIR%..\..\..\utils\scripts\sans-env.bat"

IF EXIST "%SANS_ENV_BAT%" (
    echo [setup] Sourcing environment variables from %SANS_ENV_BAT%...
    call "%SANS_ENV_BAT%"
) ELSE (
    echo [WARNING] Environment script not found at %SANS_ENV_BAT%
    echo [WARNING] Continuing with current environment variables...
)

IF "%MODE%"=="" SET "MODE=dev"
echo [run] Starting idVerifyServer (mode=%MODE%) with uv...
uv run main.py

IF ERRORLEVEL 1 (
    echo [ERROR] Failed to run main.py with uv.
    exit /b 1
)

ENDLOCAL
