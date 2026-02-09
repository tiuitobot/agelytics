"""Watch for new AoE2 replays and notify via Telegram."""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

from .parser import parse_replay
from .db import get_db, insert_match, get_match_by_id
from .report import format_duration

# Config
REPLAY_DIR = "/mnt/c/Users/administrador/Games/Age of Empires 2 DE/76561198028659538/savegame/"
PLAYER_NAME = "blzulian"
CHAT_ID = "8216818134"
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TTS_SCRIPT = "/home/linuxadmin/.openclaw/workspace/scripts/tts_send.sh"
STATE_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "watcher_state.json")


def load_state():
    """Load set of already-seen file hashes."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return set(json.load(f).get("seen_hashes", []))
    return set()


def save_state(seen):
    """Save seen hashes."""
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump({"seen_hashes": list(seen), "updated": time.time()}, f)


def send_telegram_text(text, buttons=None):
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


def send_tts_notification(text):
    """Send TTS audio via tts_send.sh."""
    if not os.path.exists(TTS_SCRIPT):
        return False
    try:
        subprocess.run(
            ["/bin/bash", TTS_SCRIPT, text, CHAT_ID],
            timeout=120,
            capture_output=True
        )
        return True
    except Exception as e:
        print(f"TTS send failed: {e}", file=sys.stderr)
        return False


def build_summary(match):
    """Build a short audio-friendly summary text."""
    me = None
    opp = None
    for p in match["players"]:
        if p["name"].lower() == PLAYER_NAME.lower():
            me = p
        else:
            opp = p

    if not me or not opp:
        return None

    result = "vitória" if me.get("winner") else "derrota"
    duration = format_duration(match.get("duration_secs", 0))
    elo = me.get("elo") or "desconhecido"
    opp_elo = opp.get("elo") or "desconhecido"

    text = (
        f"Agelytics: {result}! "
        f"{me.get('civ_name', '?')} contra {opp.get('civ_name', '?')}, "
        f"{match.get('map_name', '?')}, {duration}. "
        f"ELO {elo}, oponente {opp_elo}. "
    )

    # Add age-up times if available
    age_ups = match.get("age_ups", [])
    my_feudal = next((a for a in age_ups if a["player"] == me["name"] and "Feudal" in a["age"]), None)
    if my_feudal:
        text += f"Feudal aos {format_duration(my_feudal['timestamp_secs'])}. "

    text += "Quer o report completo?"
    return text


def build_telegram_text(match):
    """Build a short Telegram text notification."""
    me = None
    opp = None
    for p in match["players"]:
        if p["name"].lower() == PLAYER_NAME.lower():
            me = p
        else:
            opp = p

    if not me or not opp:
        return None

    emoji = "🏆" if me.get("winner") else "❌"
    result = "VITÓRIA" if me.get("winner") else "DERROTA"
    duration = format_duration(match.get("duration_secs", 0))

    return (
        f"🎮 Nova partida detectada!\n\n"
        f"{emoji} *{result}*\n"
        f"{me.get('civ_name', '?')} vs {opp.get('civ_name', '?')} | "
        f"{match.get('map_name', '?')} | {duration}"
    )


def check_new_replays(db_path=None):
    """Check for new replays, ingest, and notify."""
    if not BOT_TOKEN:
        print("TELEGRAM_BOT_TOKEN not set", file=sys.stderr)
        return

    conn = get_db(db_path)
    seen = load_state()

    # List replay files
    replay_dir = Path(REPLAY_DIR)
    if not replay_dir.exists():
        print(f"Replay dir not found: {REPLAY_DIR}", file=sys.stderr)
        return

    files = sorted(replay_dir.glob("*.aoe2record"), key=lambda f: f.stat().st_mtime, reverse=True)

    new_matches = []

    import hashlib

    for filepath in files:
        # Quick check: skip if file hash already seen
        h = hashlib.md5()
        with open(filepath, "rb") as f:
            h.update(f.read(65536))
        file_hash = h.hexdigest()

        if file_hash in seen:
            continue

        # Also check DB (in case state file was reset)
        existing = conn.execute("SELECT id FROM matches WHERE file_hash = ?", (file_hash,)).fetchone()
        if existing:
            seen.add(file_hash)
            continue

        # New file! Try to parse and ingest
        match_data = parse_replay(str(filepath))
        if match_data is None:
            seen.add(file_hash)
            continue

        match_id = insert_match(conn, match_data)
        seen.add(file_hash)

        if match_id is not None:
            # New match ingested!
            full_match = get_match_by_id(conn, match_id)
            new_matches.append(full_match)

    save_state(seen)
    conn.close()

    # Notify for each new match
    for match in new_matches:
        match_id = match["id"]

        # Send TTS audio summary
        summary = build_summary(match)
        if summary:
            send_tts_notification(summary)

        # Send Telegram text + buttons
        text = build_telegram_text(match)
        if text:
            buttons = [
                [
                    {"text": "📊 Report completo", "callback_data": f"agelytics_report_{match_id}"},
                    {"text": "🧠 Análise avançada", "callback_data": f"agelytics_analyze_{match_id}"},
                ],
                [
                    {"text": "📈 Stats gerais", "callback_data": "agelytics_stats"},
                ],
            ]
            send_telegram_text(text, buttons)

        print(f"Notified: match #{match_id}")

    if not new_matches:
        # Silent exit — no new matches
        pass

    return len(new_matches)


if __name__ == "__main__":
    check_new_replays()
