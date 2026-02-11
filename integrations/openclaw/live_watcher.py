"""Live game watcher — detects game start via rec.aoe2record changes, fetches match info from API.

Monitors the live replay file for size changes (new game = file resets to small size then grows).
When detected, polls aoe2companion API for the current match details.
Pushes opponent info + civs to the overlay server.

Usage:
    python -m integrations.openclaw.live_watcher [--poll-interval 5] [--server http://localhost:5555]
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

import httpx

# Config
REPLAY_DIR = "/mnt/c/Users/Administrador/Games/Age of Empires 2 DE/76561198028659538/savegame/"
REPLAY_PATTERN = "MP Replay"  # Live replays start with this prefix
MY_PROFILE_ID = 24635675
COMPANION_URL = "https://data.aoe2companion.com/api"
SERVER_URL = "http://localhost:5555"
POLL_INTERVAL = 5  # seconds
API_POLL_INTERVAL = 10  # seconds between API checks after detecting new game
API_TIMEOUT = 15.0
API_MAX_RETRIES = 12  # 12 * 10s = 2 minutes max wait for API


def get_newest_replay(directory: str) -> tuple[str, float, int]:
    """Find the newest MP Replay file. Returns (path, mtime, size) or ("", 0, 0)."""
    try:
        best_path, best_mtime, best_size = "", 0.0, 0
        for f in os.listdir(directory):
            if f.startswith(REPLAY_PATTERN) and f.endswith(".aoe2record"):
                full = os.path.join(directory, f)
                stat = os.stat(full)
                if stat.st_mtime > best_mtime:
                    best_path = full
                    best_mtime = stat.st_mtime
                    best_size = stat.st_size
        return best_path, best_mtime, best_size
    except OSError:
        return "", 0.0, 0


def fetch_current_match() -> dict | None:
    """Fetch most recent match from aoe2companion API.
    
    Returns match dict if it looks like a live/recent game, None otherwise.
    """
    try:
        with httpx.Client(timeout=API_TIMEOUT) as client:
            resp = client.get(
                f"{COMPANION_URL}/matches",
                params={"profile_ids": MY_PROFILE_ID, "count": 1},
            )
            resp.raise_for_status()
            data = resp.json()
    except (httpx.HTTPError, httpx.TimeoutException, ValueError) as e:
        print(f"[API] Error fetching match: {e}", file=sys.stderr)
        return None

    matches = data.get("matches", [])
    if not matches:
        return None

    match = matches[0]
    return match


def extract_match_info(match: dict) -> dict | None:
    """Extract relevant info from aoe2companion match data.
    
    Returns dict with my_civ, opponent_name, opponent_civ, opponent_profile_id, map, etc.
    """
    teams = match.get("teams", [])
    me = None
    opponent = None

    for team in teams:
        for player in team.get("players", []):
            if player.get("profileId") == MY_PROFILE_ID:
                me = player
            else:
                if opponent is None:  # Take first non-me player
                    opponent = player

    if not me or not opponent:
        return None

    return {
        "my_name": me.get("name", "blzulian"),
        "my_civ": me.get("civName", "Unknown"),
        "my_civ_key": me.get("civ", "unknown"),
        "my_rating": me.get("rating", 0),
        "opponent_name": opponent.get("name", "Unknown"),
        "opponent_civ": opponent.get("civName", "Unknown"),
        "opponent_civ_key": opponent.get("civ", "unknown"),
        "opponent_rating": opponent.get("rating", 0),
        "opponent_profile_id": opponent.get("profileId"),
        "opponent_country": opponent.get("country", ""),
        "map": match.get("mapName", "Unknown"),
        "leaderboard": match.get("leaderboardName", ""),
        "match_id": match.get("matchId"),
        "started": match.get("started"),
        "finished": match.get("finished"),
    }


def notify_server(match_info: dict, server_url: str) -> bool:
    """Push match info to overlay server."""
    try:
        with httpx.Client(timeout=5.0) as client:
            # Set game context on the overlay server
            payload = {
                "opponent_name": match_info["opponent_name"],
                "opponent_civ": match_info["opponent_civ"],
                "self_civ": match_info["my_civ"],
                "opponent_rating": match_info.get("opponent_rating"),
                "opponent_profile_id": match_info.get("opponent_profile_id"),
                "opponent_country": match_info.get("opponent_country"),
                "map": match_info.get("map"),
                "match_id": match_info.get("match_id"),
            }
            resp = client.post(
                f"{server_url}/api/match-context",
                json=payload,
            )
            resp.raise_for_status()
            print(f"[SERVER] Pushed match context: {match_info['opponent_name']} "
                  f"({match_info['opponent_civ']}) vs {match_info['my_civ']}")
            return True
    except (httpx.HTTPError, httpx.TimeoutException) as e:
        print(f"[SERVER] Error pushing context: {e}", file=sys.stderr)
        return False


def notify_openclaw(match_info: dict) -> None:
    """Write match info to a file that OpenClaw can pick up."""
    notify_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "data", "live_game.json"
    )
    os.makedirs(os.path.dirname(notify_path), exist_ok=True)
    with open(notify_path, "w") as f:
        json.dump(
            {
                "timestamp": time.time(),
                "match": match_info,
            },
            f,
            indent=2,
        )
    print(f"[FILE] Wrote live_game.json")


def run_watcher(poll_interval: float, server_url: str) -> None:
    """Main watcher loop."""
    print(f"[WATCHER] Monitoring: {REPLAY_DIR}")
    print(f"[WATCHER] Poll interval: {poll_interval}s")
    print(f"[WATCHER] Server: {server_url}")
    print(f"[WATCHER] Profile: {MY_PROFILE_ID}")
    print()

    last_path, last_mtime, last_size = get_newest_replay(REPLAY_DIR)
    last_match_id = None
    print(f"[WATCHER] Initial: {os.path.basename(last_path)} "
          f"(mtime={last_mtime:.0f}, size={last_size})")

    while True:
        time.sleep(poll_interval)

        path, mtime, size = get_newest_replay(REPLAY_DIR)

        # Detect new game: a NEW replay file appeared (different filename)
        # or the newest file's mtime jumped (still being written to)
        new_file = path != last_path
        mtime_changed = mtime != last_mtime

        if not new_file and not mtime_changed:
            continue

        if new_file:
            print(f"\n[DETECT] New replay file: {os.path.basename(path)} "
                  f"(size={size})")

            # Poll API for current match
            print(f"[API] Polling for match info...")
            for attempt in range(API_MAX_RETRIES):
                match = fetch_current_match()
                if match:
                    info = extract_match_info(match)
                    if info and info["match_id"] != last_match_id:
                        # Check if this is a recent match (started < 5 min ago)
                        started = match.get("started", "")
                        finished = match.get("finished")

                        print(f"[MATCH] Found: {info['opponent_name']} "
                              f"({info['opponent_civ']}) on {info['map']}")
                        print(f"  My civ: {info['my_civ']}, "
                              f"Opponent rating: {info['opponent_rating']}")

                        last_match_id = info["match_id"]

                        # Push to overlay server
                        notify_server(info, server_url)

                        # Overlay will auto-scout via /api/match-context polling (avoid duplicate requests)

                        # Write file for OpenClaw
                        notify_openclaw(info)

                        break
                    elif info and info["match_id"] == last_match_id:
                        print(f"[API] Same match ({last_match_id}), waiting...")

                if attempt < API_MAX_RETRIES - 1:
                    time.sleep(API_POLL_INTERVAL)
            else:
                print(f"[API] Could not find new match after {API_MAX_RETRIES} attempts")

        last_path = path
        last_mtime = mtime
        last_size = size


def trigger_scouting(match_info: dict, server_url: str) -> None:
    """Trigger scouting report for the opponent via the overlay server.

    The overlay server endpoint expects a *player name* (not profile_id).
    """
    opponent_name = match_info.get("opponent_name")
    if not opponent_name:
        return

    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.get(
                f"{server_url}/api/scout/{opponent_name}",
            )
            if resp.status_code == 200:
                print(f"[SCOUT] Scouting triggered for {opponent_name}")
            else:
                print(f"[SCOUT] Server returned {resp.status_code}")
    except (httpx.HTTPError, httpx.TimeoutException) as e:
        print(f"[SCOUT] Error: {e}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="AoE2 live game watcher")
    parser.add_argument("--poll-interval", type=float, default=POLL_INTERVAL,
                        help=f"File poll interval in seconds (default: {POLL_INTERVAL})")
    parser.add_argument("--server", default=SERVER_URL,
                        help=f"Overlay server URL (default: {SERVER_URL})")
    args = parser.parse_args()

    run_watcher(args.poll_interval, args.server)


if __name__ == "__main__":
    main()
