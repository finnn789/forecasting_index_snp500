#!/usr/bin/env bash
# running.sh — One-click launcher: backend (FastAPI via uv) + frontend (Vite via npm)
#
# Cara pakai:
#   ./running.sh
#   (atau double-click running.bat di Windows Explorer)
#
# Tekan Ctrl+C untuk menghentikan kedua proses sekaligus.

set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/stock_prediction"
FRONTEND_DIR="$ROOT_DIR/ui-stock-prediction"
LOG_DIR="$ROOT_DIR/logs"
mkdir -p "$LOG_DIR"

BACKEND_LOG="$LOG_DIR/backend.log"
FRONTEND_LOG="$LOG_DIR/frontend.log"

PIDS=()

cleanup() {
    echo ""
    echo "🛑 Menghentikan semua proses..."
    for pid in "${PIDS[@]:-}"; do
        [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null && kill "$pid" 2>/dev/null
    done
    wait 2>/dev/null
    echo "✅ Semua proses dihentikan."
}
trap cleanup EXIT INT TERM

echo "============================================"
echo "  Stock Prediction — One-Click Runner"
echo "============================================"

# --- Cek dependency tool ---
if ! command -v uv >/dev/null 2>&1; then
    echo "❌ 'uv' tidak ditemukan di PATH. Install dulu: https://docs.astral.sh/uv/"
    exit 1
fi
if ! command -v npm >/dev/null 2>&1; then
    echo "❌ 'npm' tidak ditemukan di PATH. Install Node.js dulu: https://nodejs.org/"
    exit 1
fi

# --- Backend (FastAPI via uv) ---
echo "🚀 Menjalankan backend (FastAPI) di stock_prediction/ ..."
(
    cd "$BACKEND_DIR" || exit 1
    uv run python server.py
) > "$BACKEND_LOG" 2>&1 &
BACKEND_PID=$!
PIDS+=("$BACKEND_PID")
echo "   PID backend  : $BACKEND_PID  (log: logs/backend.log)"

# --- Frontend (Vite via npm) ---
if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
    echo "📦 node_modules belum ada, menjalankan npm install ..."
    (cd "$FRONTEND_DIR" && npm install) || { echo "❌ npm install gagal"; exit 1; }
fi

echo "🚀 Menjalankan frontend (Vite) di ui-stock-prediction/ ..."
(
    cd "$FRONTEND_DIR" || exit 1
    npm run dev
) > "$FRONTEND_LOG" 2>&1 &
FRONTEND_PID=$!
PIDS+=("$FRONTEND_PID")
echo "   PID frontend : $FRONTEND_PID  (log: logs/frontend.log)"

echo ""
echo "--------------------------------------------"
echo "  Backend  : http://localhost:8000/docs"
echo "  Frontend : http://localhost:5173"
echo "  Log      : logs/backend.log , logs/frontend.log"
echo "  Tekan Ctrl+C untuk menghentikan keduanya."
echo "--------------------------------------------"
echo ""

wait
