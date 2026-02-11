"""AoE2 DE WorldsEdge API client with caching."""

import time
import httpx
from typing import Optional

from .data import CIVILIZATIONS

BASE_URL = "https://aoe-api.worldsedgelink.com/community/leaderboard"

# WorldsEdge API uses alphabetical civ IDs (0-indexed), NOT the same as replay files.
# Built by cross-referencing API data with parsed replay files (9/9 confirmed).
_API_CIVS_ALPHA = sorted(
    [name for cid, name in CIVILIZATIONS.items() if cid > 0]
)
API_CIV_MAP = {i: name for i, name in enumerate(_API_CIVS_ALPHA)}
# Reverse: replay civ_id from API civ_id
_REPLAY_CIV_BY_NAME = {name: cid for cid, name in CIVILIZATIONS.items() if cid > 0}


def api_civ_name(api_civ_id: int) -> str:
    """Translate WorldsEdge API civ_id (alphabetical) to correct civ name."""
    return API_CIV_MAP.get(api_civ_id, f"Unknown({api_civ_id})")


def api_civ_to_replay_id(api_civ_id: int) -> int:
    """Convert API civ_id to replay file civ_id."""
    name = API_CIV_MAP.get(api_civ_id)
    if name:
        return _REPLAY_CIV_BY_NAME.get(name, -1)
    return -1
TIMEOUT = 10.0
CACHE_TTL = 300  # 5 minutes

# Simple in-memory cache: key -> (timestamp, data)
_cache: dict[str, tuple[float, dict]] = {}


def _cache_get(key: str) -> Optional[dict]:
    """Get cached value if still valid."""
    if key in _cache:
        ts, data = _cache[key]
        if time.time() - ts < CACHE_TTL:
            return data
        del _cache[key]
    return None


def _cache_set(key: str, data: dict):
    """Store value in cache."""
    _cache[key] = (time.time(), data)


def clear_cache():
    """Clear the entire cache."""
    _cache.clear()


def _get(endpoint: str, params: dict) -> Optional[dict]:
    """Make a GET request to the WorldsEdge API."""
    params["title"] = "age2"
    url = f"{BASE_URL}/{endpoint}"
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            resp = client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            if data.get("result", {}).get("code") != 0:
                return None
            return data
    except (httpx.HTTPError, httpx.TimeoutException, ValueError):
        return None


def search_player(name: str) -> Optional[dict]:
    """Search for a player by name.

    Returns dict with keys: profile_id, alias, country, xp, level,
    leaderboard stats (rating, rank, wins, losses, streak, etc).
    Returns None if not found.
    """
    cache_key = f"search:{name.lower()}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    data = _get("GetPersonalStat", {"search": name})
    if not data:
        return None

    stat_groups = data.get("statGroups", [])
    leaderboard_stats = data.get("leaderboardStats", [])

    # Build list of all matching candidates with their leaderboard stats
    candidates = []
    for sg in stat_groups:
        for member in sg.get("members", []):
            if member.get("alias", "").lower() != name.lower():
                continue
            sgid = member.get("personal_statgroup_id") or sg.get("id")
            lb = None
            for ls in leaderboard_stats:
                if ls.get("statgroup_id") == sgid and ls.get("leaderboard_id") == 3:
                    lb = ls
                    break
            candidates.append((member, lb))

    if not candidates:
        # Fallback: accept partial matches
        for sg in stat_groups:
            for member in sg.get("members", []):
                sgid = member.get("personal_statgroup_id") or sg.get("id")
                lb = None
                for ls in leaderboard_stats:
                    if ls.get("statgroup_id") == sgid and ls.get("leaderboard_id") == 3:
                        lb = ls
                        break
                candidates.append((member, lb))

    if not candidates:
        return None

    # Pick the most active player: highest (wins + losses), then highest rating
    def _score(c):
        m, lb = c
        if not lb:
            return (0, 0)
        return (lb.get("wins", 0) + lb.get("losses", 0), lb.get("rating", 0))

    target, lb_stat = max(candidates, key=_score)

    profile_id = target["profile_id"]

    result = {
        "profile_id": profile_id,
        "alias": target.get("alias", name),
        "country": target.get("country", ""),
        "xp": target.get("xp", 0),
        "level": target.get("level", 0),
        "rating": lb_stat.get("rating", 0) if lb_stat else 0,
        "rank": lb_stat.get("rank", 0) if lb_stat else 0,
        "wins": lb_stat.get("wins", 0) if lb_stat else 0,
        "losses": lb_stat.get("losses", 0) if lb_stat else 0,
        "streak": lb_stat.get("streak", 0) if lb_stat else 0,
        "highest_rating": lb_stat.get("highestrating", 0) if lb_stat else 0,
        "last_match_date": lb_stat.get("lastmatchdate", 0) if lb_stat else 0,
    }

    _cache_set(cache_key, result)
    return result


def get_match_history(profile_id: int, count: int = 20) -> Optional[list[dict]]:
    """Get recent match history for a player.

    Returns list of match dicts with keys: match_id, map, starttime, duration_secs,
    players (list of {profile_id, civ_id, civ_name, team, outcome, rating_change}).
    """
    cache_key = f"history:{profile_id}:{count}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    data = _get("getRecentMatchHistory", {
        "profile_ids": f"[{profile_id}]",
        "count": str(count),
    })
    if not data:
        return None

    matches = []
    for mh in data.get("matchHistoryStats", []):
        start = mh.get("startgametime", 0)
        end = mh.get("completiontime", 0)
        duration = max(0, end - start) if start and end else 0

        players = []
        for member in mh.get("matchhistorymember", []):
            civ_id = member.get("civilization_id", 0)
            players.append({
                "profile_id": member.get("profile_id"),
                "civ_id": civ_id,
                "civ_name": api_civ_name(civ_id),
                "team": member.get("teamid", 0),
                "outcome": member.get("outcome", -1),  # 1=win, 0=loss
                "old_rating": member.get("oldrating", 0),
                "new_rating": member.get("newrating", 0),
            })

        matches.append({
            "match_id": mh.get("id"),
            "map": mh.get("mapname", "Unknown").replace(".rms", ""),
            "starttime": start,
            "duration_secs": duration,
            "matchtype_id": mh.get("matchtype_id", 0),
            "description": mh.get("description", ""),
            "players": players,
        })

    _cache_set(cache_key, matches)
    return matches


def get_leaderboard_entry(profile_id: int, leaderboard_id: int = 3) -> Optional[dict]:
    """Get current leaderboard entry for a player.

    Default leaderboard_id=3 is 1v1 Random Map.
    Returns dict with rating, rank, wins, losses, streak, etc.
    """
    cache_key = f"lb:{profile_id}:{leaderboard_id}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    data = _get("GetPersonalStat", {
        "profile_ids": f"[{profile_id}]",
    })
    if not data:
        return None

    for ls in data.get("leaderboardStats", []):
        if ls.get("leaderboard_id") == leaderboard_id:
            result = {
                "rating": ls.get("rating", 0),
                "rank": ls.get("rank", 0),
                "wins": ls.get("wins", 0),
                "losses": ls.get("losses", 0),
                "streak": ls.get("streak", 0),
                "highest_rating": ls.get("highestrating", 0),
                "highest_rank": ls.get("highestrank", 0),
                "last_match_date": ls.get("lastmatchdate", 0),
            }
            _cache_set(cache_key, result)
            return result

    return None
