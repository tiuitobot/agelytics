#!/bin/bash
# Start the game watcher (auto-detect opponent)
cd "$(dirname "$0")/.." || exit 1
source venv/bin/activate 2>/dev/null
exec python -m agelytics.game_watcher "$@"
