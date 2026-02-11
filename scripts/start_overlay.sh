#!/usr/bin/env bash
# Start the Agelytics Scouting Overlay server
# Usage: ./scripts/start_overlay.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"

cd "$REPO_DIR"

echo "Starting Agelytics Scouting Overlay on http://0.0.0.0:5555"
echo "Overlay UI: http://localhost:5555/overlay"
echo ""

python3 -m uvicorn agelytics.overlay_server:app --host 0.0.0.0 --port 5555 --reload
