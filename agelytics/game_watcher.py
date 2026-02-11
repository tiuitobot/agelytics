"""Game watcher — auto-detect opponent when AoE2 match starts.

Monitors the live replay file (rec.aoe2record) for changes.
When a new game is detected, parses player names and triggers scouting.

Runs from WSL2, accesses Windows files via /mnt/c/.
"""

import os
import sys
import time
import subprocess
import json
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

# Paths from .env
SAVEGAME_DIR = Path(os.environ.get(
    "AOE2_SAVEGAME_DIR",
    "/mnt/c/Users/Administrador/Games/Age of Empires 2 DE/76561198028659538/savegame"
))
LIVE_REPLAY = SAVEGAME_DIR / "rec.aoe2record"
SELF_NAME = os.environ.get("AOE2_PLAYER_NAME", "blzulian")

# Polling intervals
POLL_GAME_RUNNING = 0.5    # seconds — when game is running
POLL_GAME_IDLE = 15.0      # seconds — when game is not running
POLL_IN_MATCH = 5.0        # seconds — when already in a match (just monitor)

# Server
OVERLAY_URL = "http://localhost:5555"


def is_game_running() -> bool:
    """Check if AoE2 DE process is running on Windows."""
    try:
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command",
             "Get-Process AoE2DE_s -ErrorAction SilentlyContinue | Select-Object -First 1 Id"],
            capture_output=True, text=True, timeout=5
        )
        return bool(result.stdout.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def get_replay_mtime() -> float:
    """Get modification time of live replay file."""
    try:
        return LIVE_REPLAY.stat().st_mtime
    except FileNotFoundError:
        return 0


def parse_match_from_replay() -> Optional[dict]:
    """Parse the live replay file and extract match info.

    Returns dict with: opponent_name, opponent_civ, self_civ, map_name
    or None if parsing fails.
    """
    if not LIVE_REPLAY.exists():
        return None

    try:
        from mgz import header
        from agelytics.data import CIVILIZATIONS

        with open(LIVE_REPLAY, "rb") as f:
            h = header.parse_stream(f)

        players = []
        for p in h.de.players:
            name = p.name
            if hasattr(name, 'value'):
                name = name.value
            if isinstance(name, bytes):
                name = name.decode('utf-8', errors='replace')
            name = str(name).strip()

            civ_id = getattr(p, 'civ_id', None) or getattr(p, 'civilization', None)
            if hasattr(civ_id, 'value'):
                civ_id = civ_id.value
            civ_name = CIVILIZATIONS.get(civ_id, f"Unknown({civ_id})") if civ_id else "Unknown"

            if name and len(name) > 0:
                players.append({"name": name, "civ": civ_name, "civ_id": civ_id})

        if not players:
            return None

        self_player = None
        opponent = None
        for p in players:
            if p["name"].lower() == SELF_NAME.lower():
                self_player = p
            else:
                opponent = p

        if not opponent:
            return None

        return {
            "opponent_name": opponent["name"],
            "opponent_civ": opponent["civ"],
            "self_civ": self_player["civ"] if self_player else "Unknown",
        }

    except Exception as e:
        print(f"[WARN] Failed to parse replay: {e}", file=sys.stderr)
        return None


def trigger_scout(match_info: dict):
    """Notify that a new opponent was detected and set match context."""
    opp = match_info["opponent_name"]
    opp_civ = match_info["opponent_civ"]
    self_civ = match_info["self_civ"]

    print(f"\n{'='*50}")
    print(f"🎯 OPPONENT: {opp} ({opp_civ})")
    print(f"🛡️ YOU: {SELF_NAME} ({self_civ})")
    print(f"⚔️ MATCHUP: {self_civ} vs {opp_civ}")
    print(f"{'='*50}\n")

    try:
        import httpx

        # Set match context on server
        httpx.post(
            f"{OVERLAY_URL}/api/match-context",
            json={
                "opponent_name": opp,
                "opponent_civ": opp_civ,
                "self_civ": self_civ,
            },
            timeout=5.0
        )

        # Pre-fetch scouting data
        resp = httpx.get(
            f"{OVERLAY_URL}/api/scout/{opp}",
            timeout=30.0
        )
        if resp.status_code == 200:
            data = resp.json()
            p = data.get("player", {})
            print(f"  ELO: {p.get('rating', '?')}")
            print(f"  ✅ Data cached — overlay ready")
        else:
            print(f"  ⚠️ Scout request failed: {resp.status_code}")
    except Exception as e:
        print(f"  ⚠️ Could not pre-fetch: {e}")


def main():
    """Main watcher loop."""
    print(f"🎮 Agelytics Game Watcher v1.1.0")
    print(f"📁 Monitoring: {LIVE_REPLAY}")
    print(f"👤 Self: {SELF_NAME}")
    print(f"🌐 Overlay: {OVERLAY_URL}")
    print()

    last_mtime = get_replay_mtime()
    last_opponent = None
    in_match = False

    while True:
        game_running = is_game_running()

        if not game_running:
            if in_match:
                print("🏁 Game closed — match ended")
                in_match = False
                last_opponent = None
            time.sleep(POLL_GAME_IDLE)
            continue

        # Game is running — check for replay changes
        current_mtime = get_replay_mtime()

        if current_mtime > last_mtime:
            # Replay file changed — new match or ongoing update
            last_mtime = current_mtime

            if not in_match:
                # Try to parse match info
                match_info = parse_match_from_replay()
                if match_info and match_info["opponent_name"] != last_opponent:
                    last_opponent = match_info["opponent_name"]
                    in_match = True
                    trigger_scout(match_info)

            time.sleep(POLL_IN_MATCH)
        else:
            # No change — game running but no new replay data
            time.sleep(POLL_GAME_RUNNING)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Watcher stopped.")
