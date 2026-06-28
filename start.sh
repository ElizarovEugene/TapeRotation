#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && source "$NVM_DIR/nvm.sh"

# Backend
cd "$SCRIPT_DIR/backend"
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload &
BACKEND_PID=$!
echo "[taperotation] Backend started (PID $BACKEND_PID)"

# Frontend
cd "$SCRIPT_DIR/frontend"
if [ ! -d "node_modules" ]; then
    echo "[taperotation] Installing frontend deps..."
    npm install
fi
npm run dev &
FRONTEND_PID=$!
echo "[taperotation] Frontend started (PID $FRONTEND_PID)"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT INT TERM
wait
