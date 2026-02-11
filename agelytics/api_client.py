"""AoE2 DE API client — aoe2companion (primary) + WorldsEdge (player search)."""

import time
import httpx
from typing import Optional

COMPANION_URL = "https://data.aoe2companion.com/api"
WORLDSEDGE_URL = "https://aoe-api.worldsedgelink.com/community/leaderboard"
TIMEOUT = 15.0
CACHE_TTL = 300  # 5 minutes

_cache: dict[str, tuple[float, any]] = {}


def _cache_get(key: str):
    if key in _cache:
        ts, data = _cache[key]
        if time.time() - ts < CACHE_TTL:
            return data
        del _cache[key]
    return None


def _cache_set(key: str, data):
    _cache[key] = (time.time(), data)


def clear_cache():
    _cache.clear()


def _get_companion(endpoint: str, params: dict) -> Optional[dict]:
    """GET request to aoe2companion API."""
    url = f"{COMPANION_URL}/{endpoint}"
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            resp = client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()
    except (httpx.HTTPError, httpx.TimeoutException, ValueError):
        return None


def _get_worldsedge(endpoint: str, params: dict) -> Optional[dict]:
    """GET request to WorldsEdge API."""
    params["title"] = "age2"
    url = f"{WORLDSEDGE_URL}/{endpoint}"
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

    Uses WorldsEdge for search (better matching), enriches with companion data.
    Returns dict with profile_id, alias, country, rating, rank, wins, losses, etc.
    """
    cache_key = f"search:{name.lower()}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    data = _get_worldsedge("GetPersonalStat", {"search": name})
    if not data:
        return None

    stat_groups = data.get("statGroups", [])
    leaderboard_stats = data.get("leaderboardStats", [])

    # Build candidates with leaderboard stats
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
        # Fallback: accept any match
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

    # Pick most active player
    def _score(c):
        m, lb = c
        if not lb:
            return (0, 0)
        return (lb.get("wins", 0) + lb.get("losses", 0), lb.get("rating", 0))

    target, lb_stat = max(candidates, key=_score)

    result = {
        "profile_id": target["profile_id"],
        "alias": target.get("alias", name),
        "country": target.get("country", ""),
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


def get_match_history(profile_id: int, count: int = 100) -> Optional[list[dict]]:
    """Get match history via aoe2companion (paginated, up to count matches).

    Returns list of match dicts with normalized structure.
    aoe2companion provides correct civ names natively — no mapping needed.
    """
    cache_key = f"history:{profile_id}:{count}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    all_matches = []
    per_page = 20  # aoe2companion returns max 20 per page
    max_pages = (count + per_page - 1) // per_page

    for page in range(1, max_pages + 1):
        data = _get_companion("matches", {
            "profile_ids": str(profile_id),
            "count": str(per_page),
            "page": str(page),
        })
        if not data:
            break

        page_matches = data.get("matches", [])
        if not page_matches:
            break

        for m in page_matches:
            started = m.get("started") or 0
            finished = m.get("finished") or 0
            # Companion returns timestamps as int or ISO string
            if isinstance(started, str):
                from datetime import datetime
                try:
                    started = int(datetime.fromisoformat(started.replace("Z", "+00:00")).timestamp())
                except (ValueError, TypeError):
                    started = 0
            if isinstance(finished, str):
                from datetime import datetime
                try:
                    finished = int(datetime.fromisoformat(finished.replace("Z", "+00:00")).timestamp())
                except (ValueError, TypeError):
                    finished = 0
            duration = max(0, finished - started) if started and finished else 0

            # Determine matchtype from leaderboard
            lb_name = (m.get("leaderboardName") or "").lower()
            if "1v1" in lb_name and "empire wars" not in lb_name:
                matchtype_id = 6  # 1v1 RM
            elif "team" in lb_name and "empire wars" not in lb_name:
                matchtype_id = 7  # Team RM
            elif "1v1" in lb_name and "empire wars" in lb_name:
                matchtype_id = 8  # 1v1 EW
            elif "team" in lb_name and "empire wars" in lb_name:
                matchtype_id = 9  # Team EW
            else:
                matchtype_id = 0  # Unknown/custom

            players = []
            for team in m.get("teams", []):
                team_players = team.get("players", team) if isinstance(team, dict) else team
                if isinstance(team_players, dict):
                    team_players = [team_players]
                for p in team_players:
                    if not isinstance(p, dict):
                        continue
                    players.append({
                        "profile_id": p.get("profileId"),
                        "civ_id": 0,  # Not needed — we have civ_name directly
                        "civ_name": p.get("civName", "Unknown"),
                        "team": p.get("team", 0),
                        "outcome": 1 if p.get("won") else 0,
                        "old_rating": (p.get("rating") or 0) - (p.get("ratingDiff") or 0),
                        "new_rating": p.get("rating") or 0,
                    })

            all_matches.append({
                "match_id": m.get("matchId"),
                "map": m.get("mapName", "Unknown"),
                "starttime": started,
                "duration_secs": duration,
                "matchtype_id": matchtype_id,
                "leaderboard": m.get("leaderboardName", ""),
                "description": m.get("name", "AUTOMATCH"),
                "players": players,
            })

        if len(page_matches) < per_page:
            break

    if not all_matches:
        return None

    _cache_set(cache_key, all_matches)
    return all_matches


def get_leaderboard_entry(profile_id: int, leaderboard_id: int = 3) -> Optional[dict]:
    """Get current leaderboard entry via WorldsEdge."""
    cache_key = f"lb:{profile_id}:{leaderboard_id}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    data = _get_worldsedge("GetPersonalStat", {
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
