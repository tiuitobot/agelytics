#!/bin/bash
# agelytics_callback.sh — Handle Agelytics inline button callbacks
# Usage: ./scripts/agelytics_callback.sh <callback_data> [chat_id]
#
# Callbacks:
#   agelytics_report_{id}    → Match report
#   agelytics_analyze_{id}   → AI analysis (outputs prompt, doesn't call AI)
#   agelytics_stats          → Player stats
#   agelytics_day_{date}     → Day summary menu
#
# Output: text to send to Telegram (caller handles sending)

set -euo pipefail

CALLBACK="$1"
CHAT_ID="${2:-8216818134}"
PLAYER="blzulian"
REPO="/home/linuxadmin/repos/agelytics"
VENV="$REPO/venv/bin/activate"

run_agelytics() {
    cd "$REPO" && source "$VENV" && "$@"
}

case "$CALLBACK" in
    agelytics_report_*)
        MATCH_ID="${CALLBACK#agelytics_report_}"
        # Generate PDF report
        PDF_PATH="/tmp/agelytics_match_${MATCH_ID}.pdf"
        cd "$REPO" && source "$VENV" && python3 -c "
from agelytics.pdf_report import generate_match_pdf
from agelytics.db import get_db, get_match_by_id
db = get_db()
match = get_match_by_id(db, $MATCH_ID)
if match:
    generate_match_pdf(match, '$PDF_PATH')
    print('PDF:$PDF_PATH')
else:
    print('Match $MATCH_ID not found')
" 2>&1 | grep -v "UserWarning\|tight_layout"
        ;;
    agelytics_stats)
        run_agelytics python -m agelytics stats "$PLAYER" 2>&1
        ;;
    agelytics_patterns)
        run_agelytics python -m agelytics patterns -p "$PLAYER" 2>&1
        ;;
    agelytics_analyze_*)
        MATCH_ID="${CALLBACK#agelytics_analyze_}"
        # Output report text for AI to analyze, then generate PDF
        PDF_PATH="/tmp/agelytics_ai_${MATCH_ID}.pdf"
        echo "ANALYZE_MATCH:$MATCH_ID:$PDF_PATH"
        run_agelytics python -m agelytics report --id "$MATCH_ID" -p "$PLAYER" 2>&1
        ;;
    agelytics_deep_*)
        MATCH_ID="${CALLBACK#agelytics_deep_}"
        PDF_PATH="/tmp/agelytics_deep_${MATCH_ID}.pdf"
        echo "DEEP_COACH:$MATCH_ID:$PDF_PATH"
        run_agelytics python -m agelytics report --id "$MATCH_ID" -p "$PLAYER" 2>&1
        ;;
    agelytics_day_*)
        DATE="${CALLBACK#agelytics_day_}"
        cd "$REPO" && source "$VENV" && python3 -c "
import sqlite3
conn = sqlite3.connect('data/aoe2_matches.db')
c = conn.cursor()
c.execute('''SELECT m.id, m.duration_secs, m.map_name,
    GROUP_CONCAT(p.name || '|' || p.civ_name || '|' || COALESCE(p.elo,0) || '|' || p.winner, ';')
    FROM matches m JOIN match_players p ON p.match_id = m.id
    WHERE m.played_at LIKE '${DATE}%'
    GROUP BY m.id ORDER BY m.played_at''')
wins, losses = 0, 0
for row in c.fetchall():
    mid, dur, map_n, players = row
    mins = dur / 60
    for p in players.split(';'):
        parts = p.split('|')
        if 'blzulian' in parts[0]:
            w = '✅' if parts[3]=='1' else '❌'
            if parts[3]=='1': wins += 1
            else: losses += 1
        else:
            opp_civ = parts[1]
    print(f'{w} ID={mid} vs {opp_civ} {map_n} {mins:.0f}min')
print(f'---')
print(f'Total: {wins}W/{losses}L')
conn.close()
" 2>&1
        ;;
    *)
        echo "Unknown callback: $CALLBACK"
        exit 1
        ;;
esac
