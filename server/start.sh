#!/bin/bash
#
# idVerifyServer/start.sh — launcher for the Python ID-verification
# backend (FastAPI + MediaPipe + PaddleOCR). Mirrors the entityExplorer
# pattern. Called by utils/scriptsGpu/pServ-start.sh as IDVS.

# Determine the directory containing this script (the project root)
SERVER_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SERVER_DIR"

# Resolve the path to the sans-env.sh utility script
SANS_ENV_SH="$SERVER_DIR/../../utils/scripts/sans-env.sh"

# Check if the environment script exists and source it
if [ -f "$SANS_ENV_SH" ]; then
    echo "[setup] Sourcing environment variables from $SANS_ENV_SH..."
    source "$SANS_ENV_SH"
else
    echo "[WARNING] Environment script not found at $SANS_ENV_SH"
    echo "[WARNING] Continuing with current environment variables..."
fi

# Run the server using uv (deps resolved from pyproject.toml / uv.lock).
# The dev / prod distinction is honoured here: dev gets --reload (file
# watcher for hot reload), prod runs a clean uvicorn (no watcher).
# Port is read from configServer at startup by main.py (defaults to
# 8010 if config resolution fails); Caddy proxies /idVerifyServer*
# to whichever port main.py actually binds.
MODE="${MODE:-dev}"
if [ "$MODE" = "prod" ]; then
    echo "[run] Starting idVerifyServer (prod, no --reload)..."
    uv run main.py
else
    echo "[run] Starting idVerifyServer (dev)..."
    uv run main.py
fi
