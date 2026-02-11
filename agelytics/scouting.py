"""Scouting engine — analyze opponent from API data."""

import time
from collections import Counter, defaultdict
from typing import Optional

from .api_client import search_player, get_match_history, get_leaderboard_entry
from .data import CIVILIZATIONS


def _elo_trend(matches: list[dict], profile_id: int) -> str:
    """Determine ELO trend from recent matches.

    Looks at rating changes over last 30 days.
    Returns 'rising', 'falling', or 'stable'.
    """
    now = time.time()
    thirty_days_ago = now - (30 * 86400)

    ratings = []
    for m in matches:
        if m["starttime"] < thirty_days_ago:
            continue
        for p in m["players"]:
            if p["profile_id"] == profile_id:
                ratings.append(p["new_rating"])
                break

    if len(ratings) < 2:
        return "stable"

    # Compare oldest rating to most recent
    # ratings[0] is most recent (matches come newest-first)
    newest = ratings[0]
    oldest = ratings[-1]
    diff = newest - oldest

    if diff > 20:
        return "rising"
    elif diff < -20:
        return "falling"
    return "stable"


def _top_civs(matches: list[dict], profile_id: int, top_n: int = 3) -> list[dict]:
    """Get top N most played civs with win rates."""
    civ_stats: dict[str, dict] = defaultdict(lambda: {"wins": 0, "total": 0})

    for m in matches:
        for p in m["players"]:
            if p["profile_id"] == profile_id:
                civ = p["civ_name"]
                civ_stats[civ]["total"] += 1
                if p["outcome"] == 1:
                    civ_stats[civ]["wins"] += 1
                break

    sorted_civs = sorted(civ_stats.items(), key=lambda x: x[1]["total"], reverse=True)

    result = []
    for civ_name, stats in sorted_civs[:top_n]:
        total = stats["total"]
        wins = stats["wins"]
        result.append({
            "civ": civ_name,
            "games": total,
            "wins": wins,
            "win_rate": round(wins / total * 100, 1) if total > 0 else 0,
        })

    return result


def _opening_tendency(matches: list[dict], profile_id: int) -> str:
    """Classify opening tendency from match duration patterns.

    Short games (<20min) → rush tendency
    Medium games (20-35min) → hybrid/adaptive
    Long games (>35min) → boom tendency
    """
    durations = []
    for m in matches:
        if m["duration_secs"] > 0:
            for p in m["players"]:
                if p["profile_id"] == profile_id:
                    durations.append(m["duration_secs"])
                    break

    if not durations:
        return "Unknown"

    avg_duration = sum(durations) / len(durations)
    short = sum(1 for d in durations if d < 1200)  # <20min
    long_ = sum(1 for d in durations if d > 2100)   # >35min

    total = len(durations)
    short_pct = short / total
    long_pct = long_ / total

    if short_pct > 0.5:
        return "Aggressive (Rush)"
    elif long_pct > 0.5:
        return "Boom / Late Game"
    elif avg_duration < 1500:
        return "Early Aggression"
    elif avg_duration > 2400:
        return "Defensive / Boom"
    return "Hybrid / Adaptive"


def _win_rate(matches: list[dict], profile_id: int) -> dict:
    """Calculate overall win rate from matches."""
    wins = 0
    total = 0
    for m in matches:
        for p in m["players"]:
            if p["profile_id"] == profile_id:
                total += 1
                if p["outcome"] == 1:
                    wins += 1
                break

    return {
        "wins": wins,
        "losses": total - wins,
        "total": total,
        "win_rate": round(wins / total * 100, 1) if total > 0 else 0,
    }


def scout_player(player_name: str) -> dict:
    """Generate a full scouting report for an opponent.

    Returns structured dict with all scouting data, or error info.
    """
    # Search player
    player = search_player(player_name)
    if not player:
        return {"error": f"Player '{player_name}' not found", "available": False}

    profile_id = player["profile_id"]

    # Get match history
    matches = get_match_history(profile_id, count=50)
    if not matches:
        # Return partial data
        return {
            "available": True,
            "player": player,
            "matches_available": False,
            "error": "Could not fetch match history",
        }

    # Filter to 1v1 RM only (matchtype_id 6) for accurate stats
    rm_matches = [m for m in matches if m.get("matchtype_id") == 6]
    # Fallback to all matches if no 1v1 RM found
    analysis_matches = rm_matches if rm_matches else matches

    # Compute scouting data
    trend = _elo_trend(analysis_matches, profile_id)
    top_civs = _top_civs(analysis_matches, profile_id)
    opening = _opening_tendency(analysis_matches, profile_id)
    wr = _win_rate(analysis_matches, profile_id)

    # Get favorite maps
    map_counter = Counter()
    for m in analysis_matches:
        map_counter[m["map"]] += 1
    top_maps = [{"map": name, "games": count} for name, count in map_counter.most_common(3)]

    return {
        "available": True,
        "matches_available": True,
        "player": {
            "alias": player["alias"],
            "profile_id": profile_id,
            "country": player["country"],
            "rating": player["rating"],
            "rank": player["rank"],
            "highest_rating": player["highest_rating"],
        },
        "elo_trend": trend,
        "top_civs": top_civs,
        "opening_tendency": opening,
        "win_rate": wr,
        "top_maps": top_maps,
        "recent_matches": len(analysis_matches),
        "streak": player.get("streak", 0),
    }
