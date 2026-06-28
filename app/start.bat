@echo off
SETLOCAL ENABLEDELAYEDEXPANSION

:: start.bat - Windows launcher for the n_g_m_utils_idVerify/app (Nuxt) app. Loads the shared
:: SANS dev environment (utils\scripts\sans-env.bat), then starts the dev
:: server with pnpm. Mirrors the per-service start.bat convention and the
:: bulk launcher utils\scripts\uServ-start.bat (call sans-env + pnpm run dev).

:: Directory containing this script (the app source folder)
SET "APP_DIR=%~dp0"
cd /d "%APP_DIR%"

:: Resolve the shared environment script (repo-root\utils\scripts)
SET "SANS_ENV_BAT=%APP_DIR%..\..\utils\scripts\sans-env.bat"

IF EXIST "%SANS_ENV_BAT%" (
    echo [setup] Sourcing environment variables from %SANS_ENV_BAT%...
    call "%SANS_ENV_BAT%"
) ELSE (
    echo [WARNING] Environment script not found at %SANS_ENV_BAT%
    echo [WARNING] Continuing with current environment variables...
)

echo [run] Starting n_g_m_utils_idVerify/app dev server with pnpm...
call pnpm run dev

IF ERRORLEVEL 1 (
    echo [ERROR] Failed to start the dev server.
    pause
    exit /b 1
)

ENDLOCAL
