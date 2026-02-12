#!/bin/bash
# dispatch.sh — Route agelytics callbacks with minimal AI usage
# Deterministic: report, day, stats (zero AI, sends directly via Telegram API)
# AI-assisted: analyze, deep (extracts data, outputs for Haiku spawn)
#
# Usage: dispatch.sh <callback_data> <chat_id>
# Exit codes: 0=deterministic (already sent), 1=error, 2=needs AI (data on stdout)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$SCRIPT_DIR/../.." && pwd)"
CALLBACK="$1"
CHAT_ID="${2:-8216818134}"
VENV="$REPO/venv/bin/activate"
SEND="$SCRIPT_DIR/telegram_send.sh"

BUTTONS_REPORT='{"inline_keyboard":[[{"text":"🧠 Análise IA","callback_data":"agelytics_analyze_ID"},{"text":"🔬 Deep Coach","callback_data":"agelytics_deep_ID"}],[{"text":"📋 Menu do dia","callback_data":"agelytics_day_DATE"},{"text":"📈 Stats","callback_data":"agelytics_stats"}]]}'
BUTTONS_DAY='{"inline_keyboard":[[{"text":"📈 Stats","callback_data":"agelytics_stats"}]]}'
TODAY=$(date +%Y-%m-%d)

case "$CALLBACK" in
    agelytics_report_*)
        MATCH_ID="${CALLBACK#agelytics_report_}"
        
        # Generate KPI text (deterministic)
        cd "$REPO" && source "$VENV"
        TEXT=$(python3 -m integrations.openclaw.quick_report "$MATCH_ID" 2>&1)
        
        # Generate PDF
        PDF_PATH="/tmp/agelytics_match_${MATCH_ID}.pdf"
        python3 -c "
from agelytics.pdf_report import generate_match_pdf
from agelytics.db import get_db, get_match_by_id
db = get_db()
match = get_match_by_id(db, $MATCH_ID)
if match:
    generate_match_pdf(match, '$PDF_PATH')
" 2>&1 | grep -v "UserWarning\|tight_layout" || true
        
        # Prepare buttons with correct ID/date
        BTNS=$(echo "$BUTTONS_REPORT" | sed "s/ID/$MATCH_ID/g" | sed "s/DATE/$TODAY/g")
        
        # Send directly
        bash "$SEND" "$CHAT_ID" "$TEXT" "$PDF_PATH" "$BTNS"
        
        # Output text for main session awareness
        echo "SENT_DETERMINISTIC"
        echo "$TEXT"
        exit 0
        ;;
        
    agelytics_day_*)
        DATE="${CALLBACK#agelytics_day_}"
        
        cd "$REPO" && source "$VENV"
        DAY_DATA=$(python3 -c "
import sqlite3
conn = sqlite3.connect('data/aoe2_matches.db')
c = conn.cursor()
c.execute('''SELECT m.id, m.duration_secs, m.map_name,
    GROUP_CONCAT(p.name || '|' || p.civ_name || '|' || COALESCE(p.elo,0) || '|' || p.winner, ';')
    FROM matches m JOIN match_players p ON p.match_id = m.id
    WHERE m.played_at LIKE '${DATE}%'
    GROUP BY m.id ORDER BY m.played_at''')
wins, losses = 0, 0
lines = []
ids = []
for row in c.fetchall():
    mid, dur, map_n, players = row
    mins = dur / 60
    my_civ = opp_civ = ''
    w = ''
    for p in players.split(';'):
        parts = p.split('|')
        if 'blzulian' in parts[0]:
            w = '✅' if parts[3]=='1' else '❌'
            my_civ = parts[1]
            if parts[3]=='1': wins += 1
            else: losses += 1
        else:
            opp_civ = parts[1]
    lines.append(f'{w} #{mid} {my_civ} vs {opp_civ} | {map_n} | {mins:.0f}min')
    ids.append(str(mid))
print(f'📋 Partidas {\"$DATE\"} ({wins}W/{losses}L)')
print()
for l in lines:
    print(l)
print('---IDS---')
print(','.join(ids))
conn.close()
" 2>&1)
        
        # Extract text and IDs
        TEXT=$(echo "$DAY_DATA" | sed '/^---IDS---$/,$d')
        IDS=$(echo "$DAY_DATA" | sed -n '/^---IDS---$/,$ p' | tail -1)
        
        # Build buttons dynamically
        BTN_ROWS=""
        IFS=',' read -ra ID_ARR <<< "$IDS"
        ROW=""
        COUNT=0
        for id in "${ID_ARR[@]}"; do
            if [ -n "$ROW" ]; then ROW="$ROW,"; fi
            ROW="$ROW{\"text\":\"📊 #$id\",\"callback_data\":\"agelytics_report_$id\"}"
            COUNT=$((COUNT + 1))
            if [ $COUNT -ge 3 ]; then
                BTN_ROWS="$BTN_ROWS[$ROW],"
                ROW=""
                COUNT=0
            fi
        done
        if [ -n "$ROW" ]; then
            BTN_ROWS="$BTN_ROWS[$ROW],"
        fi
        BTN_ROWS="$BTN_ROWS[{\"text\":\"📈 Stats\",\"callback_data\":\"agelytics_stats\"}]"
        BTNS="{\"inline_keyboard\":[$BTN_ROWS]}"
        
        bash "$SEND" "$CHAT_ID" "$TEXT" "" "$BTNS"
        
        echo "SENT_DETERMINISTIC"
        echo "$TEXT"
        exit 0
        ;;
        
    agelytics_stats)
        cd "$REPO" && source "$VENV"
        TEXT=$(python3 -m agelytics stats blzulian 2>&1)
        
        bash "$SEND" "$CHAT_ID" "$TEXT"
        
        echo "SENT_DETERMINISTIC"
        echo "$TEXT"
        exit 0
        ;;
        
    agelytics_analyze_*|agelytics_deep_*)
        MATCH_ID="${CALLBACK#agelytics_analyze_}"
        MATCH_ID="${MATCH_ID#agelytics_deep_}"  # handles both prefixes
        
        cd "$REPO" && source "$VENV"
        
        # Extract data for AI (deterministic extraction)
        python3 -m integrations.openclaw.deep_coach "$MATCH_ID" 2>&1
        
        # Also generate PDF path
        PDF_PATH="/tmp/agelytics_match_${MATCH_ID}.pdf"
        python3 -c "
from agelytics.pdf_report import generate_match_pdf
from agelytics.db import get_db, get_match_by_id
db = get_db()
match = get_match_by_id(db, $MATCH_ID)
if match:
    generate_match_pdf(match, '$PDF_PATH')
" 2>&1 | grep -v "UserWarning\|tight_layout" || true
        
        echo "---PDF_PATH---"
        echo "$PDF_PATH"
        
        # Exit 2 = needs AI processing
        exit 2
        ;;
        
    *)
        echo "Unknown callback: $CALLBACK"
        exit 1
        ;;
esac
