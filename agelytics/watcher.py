"""Watch for new AoE2 replays and notify via Telegram.

Pure deterministic — no AI, no TTS. Runs via Linux crontab every 2min.
When a new match is detected: parse → DB → Telegram notification with buttons.
Also writes to pending_notifications.json for Tiuito to pick up (audio etc).
"""

import json
import os
import hashlib
import sys
import time
from datetime import datetime
from pathlib import Path

from .parser import parse_replay
from .db import get_db, insert_match, get_match_by_id
from .report import format_duration

# Config
REPLAY_DIR = "/mnt/c/Users/administrador/Games/Age of Empires 2 DE/76561198028659538/savegame/"
PLAYER_NAME = "blzulian"
CHAT_ID = "8216818134"
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
STATE_FILE = os.path.join(DATA_DIR, "watcher_state.json")
NOTIFY_FILE = os.path.join(DATA_DIR, "pending_notifications.json")


def load_state():
    """Load set of already-seen file hashes."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return set(json.load(f).get("seen_hashes", []))
    return set()


def save_state(seen):
    """Save seen hashes."""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump({"seen_hashes": list(seen), "updated": time.time()}, f)


def send_telegram(text, buttons=None):
    """Send a text message via Telegram Bot API."""
    import urllib.request
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
    }
    if buttons:
        payload["reply_markup"] = json.dumps({
            "inline_keyboard": buttons
        })
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=10)
        return True
    except Exception as e:
        print(f"Telegram send failed: {e}", file=sys.stderr)
        return False


def write_pending_notification(match_id, summary_data):
    """Write notification for Tiuito to pick up (audio summary, etc)."""
    pending = []
    if os.path.exists(NOTIFY_FILE):
        try:
            with open(NOTIFY_FILE) as f:
                pending = json.load(f)
        except (json.JSONDecodeError, Exception):
            pending = []

    pending.append({
        "match_id": match_id,
        "timestamp": datetime.now().isoformat(),
        "summary": summary_data,
        "handled": False,
    })

    with open(NOTIFY_FILE, "w") as f:
        json.dump(pending, f, indent=2)


def build_notification(match):
    """Build Telegram notification text and summary data for a match."""
    me = None
    opp = None
    for p in match["players"]:
        if p["name"].lower() == PLAYER_NAME.lower():
            me = p
        else:
            opp = p

    if not me or not opp:
        return None, None

    is_win = bool(me.get("winner"))
    emoji = "🏆" if is_win else "❌"
    result = "VITÓRIA" if is_win else "DERROTA"
    duration = format_duration(match.get("duration_secs", 0))
    map_name = match.get("map_name", "?")

    # Telegram text
    text = (
        f"🎮 Nova partida detectada!\n\n"
        f"{emoji} *{result}*\n"
        f"{me.get('civ_name', '?')} vs {opp.get('civ_name', '?')} | "
        f"{map_name} | {duration}\n"
        f"ELO {me.get('elo', '?')} vs {opp.get('elo', '?')} | "
        f"eAPM {me.get('eapm', '?')} vs {opp.get('eapm', '?')}"
    )

    # Summary data for Tiuito's audio
    feudal_time = None
    for a in match.get("age_ups", []):
        if a["player"] == me["name"] and "Feudal" in a["age"]:
            feudal_time = format_duration(a["timestamp_secs"])
            break

    summary = {
        "result": result.lower(),
        "my_civ": me.get("civ_name", "?"),
        "opp_civ": opp.get("civ_name", "?"),
        "opp_name": opp.get("name", "?"),
        "map": map_name,
        "duration": duration,
        "my_elo": me.get("elo"),
        "opp_elo": opp.get("elo"),
        "feudal_time": feudal_time,
    }

    return text, summary


def get_today_str():
    """Get today's date as YYYY-MM-DD."""
    return datetime.now().strftime("%Y-%m-%d")


def check_new_replays(db_path=None):
    """Check for new replays, ingest, and notify."""
    if not BOT_TOKEN:
        print("TELEGRAM_BOT_TOKEN not set", file=sys.stderr)
        return 0

    conn = get_db(db_path)
    seen = load_state()

    replay_dir = Path(REPLAY_DIR)
    if not replay_dir.exists():
        print(f"Replay dir not found: {REPLAY_DIR}", file=sys.stderr)
        return 0

    files = sorted(replay_dir.glob("*.aoe2record"), key=lambda f: f.stat().st_mtime, reverse=True)

    new_matches = []

    for filepath in files:
        # Quick hash check
        h = hashlib.md5()
        with open(filepath, "rb") as f:
            h.update(f.read(65536))
        file_hash = h.hexdigest()

        if file_hash in seen:
            continue

        # Check DB too
        existing = conn.execute("SELECT id FROM matches WHERE file_hash = ?", (file_hash,)).fetchone()
        if existing:
            seen.add(file_hash)
            continue

        # New file — parse and ingest
        match_data = parse_replay(str(filepath))
        if match_data is None:
            seen.add(file_hash)
            continue

        match_id = insert_match(conn, match_data)
        seen.add(file_hash)

        if match_id is not None:
            full_match = get_match_by_id(conn, match_id)
            new_matches.append(full_match)

    save_state(seen)
    conn.close()

    # Notify for each new match
    today = get_today_str()
    for match in new_matches:
        match_id = match["id"]

        text, summary = build_notification(match)
        if text:
            buttons = [
                [
                    {"text": "📊 Report", "callback_data": f"agelytics_report_{match_id}"},
                    {"text": "🧠 Análise IA", "callback_data": f"agelytics_analyze_{match_id}"},
                    {"text": "🔬 Deep Coach", "callback_data": f"agelytics_deep_{match_id}"},
                ],
                [
                    {"text": "📋 Menu do dia", "callback_data": f"agelytics_day_{today}"},
                    {"text": "📈 Stats", "callback_data": "agelytics_stats"},
                ],
            ]
            send_telegram(text, buttons)

        if summary:
            write_pending_notification(match_id, summary)

        print(f"Notified: match #{match_id}")

    return len(new_matches)


if __name__ == "__main__":
    check_new_replays()
