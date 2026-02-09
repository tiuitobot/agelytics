#!/bin/bash
# Agelytics watcher — runs every 1 min via crontab
# Checks for new replays and notifies via Telegram (TTS + text + buttons)

cd /home/linuxadmin/repos/agelytics
source venv/bin/activate

export TELEGRAM_BOT_TOKEN="8437707256:AAHm_oKlEn7qoV9bARV7uiBE1Q9J2CpM7GE"

python -m agelytics.watcher 2>/dev/null
