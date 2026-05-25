#!/usr/bin/env bash
# run_api.sh — Jalankan FastAPI server (development mode)

set -e

# Pindah ke root proyek
cd "$(dirname "$0")/.."

echo "🚀 Starting Stock Market Prediction API..."
echo "   Swagger UI : http://localhost:8000/docs"
echo "   ReDoc       : http://localhost:8000/redoc"
echo "   Status      : http://localhost:8000/api/status"
echo "   Health      : http://localhost:8000/api/health"
echo ""

python server.py
