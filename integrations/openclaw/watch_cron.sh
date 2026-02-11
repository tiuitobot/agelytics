#!/bin/bash
# Agelytics watcher — runs every 2 min via crontab
# Checks for new replays, parses, stores in DB, sends Telegram notification
# 100% deterministic — no AI, no TTS

cd /home/linuxadmin/repos/agelytics
source venv/bin/activate

# Bot token from env file
set -a
source /home/linuxadmin/repos/agelytics/.env 2>/dev/null
set +a

python3 -m integrations.openclaw.watcher 2>/dev/null
