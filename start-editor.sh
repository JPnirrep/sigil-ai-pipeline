#!/bin/bash
# KLEIA-UP Book Editor — Démarrage rapide
# Usage: ./start-editor.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_PORT=8586
FRONTEND_PORT=5174

echo "== KLEIA-UP Book Editor =="
echo ""

# Kill existing
kill $(lsof -t -i:$BACKEND_PORT -i:$FRONTEND_PORT 2>/dev/null) 2>/dev/null

# Backend
echo "[Backend] Démarrage sur :$BACKEND_PORT..."
cd "$SCRIPT_DIR"
python -m uvicorn editor.api.main:app --port $BACKEND_PORT --host 0.0.0.0 &
BACKEND_PID=$!
sleep 2

# Check backend
curl -sf http://localhost:$BACKEND_PORT/api/health > /dev/null && \
  echo "  ✓ Backend OK (PID $BACKEND_PID)" || \
  echo "  ✗ Backend FAILED"

# Frontend
echo "[Frontend] Démarrage sur :$FRONTEND_PORT..."
cd "$SCRIPT_DIR/editor/frontend"
npx vite --port $FRONTEND_PORT --host 0.0.0.0 &
FRONTEND_PID=$!
sleep 2

echo ""
echo "═══ Éditeur prêt ═══"
echo "  Backend : http://localhost:$BACKEND_PORT"
echo "  Frontend: http://localhost:$FRONTEND_PORT"
echo "═══════════════════════"
echo ""
echo "Pour arrêter : kill $BACKEND_PID $FRONTEND_PID"
wait
