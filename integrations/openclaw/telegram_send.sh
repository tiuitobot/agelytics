#!/bin/bash
# telegram_send.sh — Send message + optional file directly to Telegram (no AI)
# Usage: telegram_send.sh <chat_id> <text> [file_path] [buttons_json]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
TELEGRAM_BOT_TOKEN=$(grep '^TELEGRAM_BOT_TOKEN=' "$SCRIPT_DIR/.env" | cut -d= -f2)

CHAT_ID="$1"
TEXT="$2"
FILE="${3:-}"
BUTTONS="${4:-}"

API="https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}"

if [ -n "$FILE" ] && [ -f "$FILE" ]; then
    # Send document with caption
    CAPTION="$TEXT"
    if [ ${#CAPTION} -gt 1024 ]; then
        CAPTION="${CAPTION:0:1020}..."
    fi
    
    ARGS=(-F "chat_id=$CHAT_ID" -F "document=@$FILE" -F "caption=$CAPTION" -F "parse_mode=Markdown")
    
    if [ -n "$BUTTONS" ]; then
        ARGS+=(-F "reply_markup=$BUTTONS")
    fi
    
    curl -s "$API/sendDocument" "${ARGS[@]}" > /dev/null
    
    # If text was truncated, send full text separately
    if [ ${#TEXT} -gt 1024 ]; then
        ARGS2=(-d "chat_id=$CHAT_ID" -d "text=$TEXT" -d "parse_mode=Markdown")
        if [ -n "$BUTTONS" ]; then
            ARGS2+=(--data-urlencode "reply_markup=$BUTTONS")
        fi
        curl -s "$API/sendMessage" "${ARGS2[@]}" > /dev/null
    fi
else
    # Send text only
    ARGS=(--data-urlencode "chat_id=$CHAT_ID" --data-urlencode "text=$TEXT" -d "parse_mode=Markdown")
    
    if [ -n "$BUTTONS" ]; then
        ARGS+=(--data-urlencode "reply_markup=$BUTTONS")
    fi
    
    curl -s "$API/sendMessage" "${ARGS[@]}" > /dev/null
fi
