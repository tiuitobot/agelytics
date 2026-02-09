"""Pattern detection from aggregate match data.

100% deterministic Python/SQL — zero AI.
Generates structured patterns from SQLite match history.
"""

import json
import os
import sqlite3
from datetime import datetime
import sys
from typing import Optional

from .db import get_db, DEFAULT_DB


PATTERNS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "patterns.json")


def matchup_stats(conn: sqlite3.Connection, player: str, n_last: int = 0) -> list[dict]:
    """Winrate by matchup (my civ vs opponent civ).
    
    n_last=0 means all matches.
    """
    limit_clause = f"LIMIT {n_last}" if n_last > 0 else ""
    
    rows = conn.execute(f"""
        WITH my_matches AS (
            SELECT m.id, m.duration_secs, mp.civ_name AS my_civ, mp.winner AS my_win
            FROM matches m
            JOIN match_players mp ON mp.match_id = m.id
            WHERE mp.name = ?
            ORDER BY m.played_at DESC
            {limit_clause}
        ),
        opp AS (
            SELECT mm.id, mm.my_civ, mm.my_win, mm.duration_secs,
                   op.civ_name AS opp_civ
            FROM my_matches mm
            JOIN match_players op ON op.match_id = mm.id AND op.name != ?
        )
        SELECT my_civ, opp_civ,
               COUNT(*) AS games,
               SUM(my_win) AS wins,
               ROUND(AVG(duration_secs), 1) AS avg_duration,
               ROUND(CAST(SUM(my_win) AS FLOAT) / COUNT(*), 2) AS winrate
        FROM opp
        GROUP BY my_civ, opp_civ
        HAVING COUNT(*) >= 2
        ORDER BY winrate ASC, games DESC
    """, (player, player)).fetchall()
    
    return [dict(r) for r in rows]


def civ_stats(conn: sqlite3.Connection, player: str, n_last: int = 0) -> list[dict]:
    """Winrate per civilization played."""
    limit_clause = f"LIMIT {n_last}" if n_last > 0 else ""
    
    rows = conn.execute(f"""
        WITH recent AS (
            SELECT m.id, mp.civ_name, mp.winner, mp.elo, m.duration_secs
            FROM matches m
            JOIN match_players mp ON mp.match_id = m.id
            WHERE mp.name = ?
            ORDER BY m.played_at DESC
            {limit_clause}
        )
        SELECT civ_name,
               COUNT(*) AS games,
               SUM(winner) AS wins,
               ROUND(CAST(SUM(winner) AS FLOAT) / COUNT(*), 2) AS winrate,
               ROUND(AVG(duration_secs), 1) AS avg_duration
        FROM recent
        GROUP BY civ_name
        ORDER BY games DESC
    """, (player,)).fetchall()
    
    return [dict(r) for r in rows]


def age_up_trends(conn: sqlite3.Connection, player: str, n_recent: int = 10) -> dict:
    """Feudal and Castle age-up time trends: recent N vs previous N."""
    
    result = {}
    for age in ["Feudal Age", "Castle Age"]:
        rows = conn.execute("""
            SELECT a.timestamp_secs, m.played_at
            FROM match_age_ups a
            JOIN matches m ON a.match_id = m.id
            JOIN match_players mp ON mp.match_id = m.id AND mp.name = ?
            WHERE a.player = ? AND a.age = ?
            ORDER BY m.played_at DESC
        """, (player, player, age)).fetchall()
        
        if len(rows) < 4:
            continue
        
        recent = [r["timestamp_secs"] for r in rows[:n_recent]]
        older = [r["timestamp_secs"] for r in rows[n_recent:n_recent*2]]
        
        avg_recent = sum(recent) / len(recent) if recent else 0
        avg_older = sum(older) / len(older) if older else 0
        
        if avg_older > 0:
            diff = avg_recent - avg_older
            if diff < -10:
                trend = "improving"
            elif diff > 10:
                trend = "worsening"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"
        
        key = age.split()[0].lower()  # "feudal" or "castle"
        result[key] = {
            "avg_recent_secs": round(avg_recent, 1),
            "avg_older_secs": round(avg_older, 1) if avg_older else None,
            "diff_secs": round(avg_recent - avg_older, 1) if avg_older else None,
            "trend": trend,
            "sample_recent": len(recent),
            "sample_older": len(older),
        }
    
    return result


def military_timing(conn: sqlite3.Connection, player: str, n_last: int = 0) -> dict:
    """First military unit timing and correlation with wins/losses."""
    limit_clause = f"LIMIT {n_last}" if n_last > 0 else ""
    
    # Get first non-eco unit per match
    eco_units = ("Villager", "Scout Cavalry", "Fishing Ship", "Trade Cart", "Trade Cog")
    placeholders = ",".join("?" * len(eco_units))
    
    rows = conn.execute(f"""
        WITH recent AS (
            SELECT m.id AS match_id, mp.winner
            FROM matches m
            JOIN match_players mp ON mp.match_id = m.id
            WHERE mp.name = ?
            ORDER BY m.played_at DESC
            {limit_clause}
        ),
        first_mil AS (
            SELECT r.match_id, r.winner,
                   MIN(mu.timestamp_secs) AS first_mil_secs
            FROM recent r
            JOIN match_researches mu ON mu.match_id = r.match_id
            WHERE mu.player = ? AND mu.tech NOT IN ({placeholders})
            GROUP BY r.match_id
        )
        SELECT * FROM first_mil
    """, (player, player, *eco_units)).fetchall()
    
    # Actually, first military = first Queue of military unit
    # Let's use match_units instead — but we don't have timestamps there
    # Use match_researches for Man-at-Arms, Pikeman etc as proxy
    # Better: query first military from units table with a subquery
    
    # Simpler approach: use the unit production data
    # We need to check match_units but we don't store timestamps per unit queue
    # For now, use first non-age research as a proxy for military activity
    
    if not rows:
        # Fallback: just report overall stats
        return {"available": False, "reason": "no_timestamp_data"}
    
    win_times = [r["first_mil_secs"] for r in rows if r["winner"] and r["first_mil_secs"]]
    loss_times = [r["first_mil_secs"] for r in rows if not r["winner"] and r["first_mil_secs"]]
    all_times = [r["first_mil_secs"] for r in rows if r["first_mil_secs"]]
    
    return {
        "available": True,
        "avg_first_military_secs": round(sum(all_times) / len(all_times), 1) if all_times else None,
        "win_avg_secs": round(sum(win_times) / len(win_times), 1) if win_times else None,
        "loss_avg_secs": round(sum(loss_times) / len(loss_times), 1) if loss_times else None,
        "sample_wins": len(win_times),
        "sample_losses": len(loss_times),
    }


def eco_health(conn: sqlite3.Connection, player: str, n_last: int = 0) -> dict:
    """Economy health metrics: TC idle, villager production, farm count."""
    limit_clause = f"LIMIT {n_last}" if n_last > 0 else ""
    
    rows = conn.execute(f"""
        SELECT mp.tc_idle_secs, mp.winner, mp.eapm,
               m.duration_secs, m.id
        FROM match_players mp
        JOIN matches m ON mp.match_id = m.id
        WHERE mp.name = ? AND mp.tc_idle_secs IS NOT NULL
        ORDER BY m.played_at DESC
        {limit_clause}
    """, (player,)).fetchall()
    
    if not rows:
        return {"available": False}
    
    tc_idles = [r["tc_idle_secs"] for r in rows]
    durations = [r["duration_secs"] for r in rows if r["duration_secs"]]
    idle_pcts = [r["tc_idle_secs"] / r["duration_secs"] for r in rows 
                 if r["duration_secs"] and r["duration_secs"] > 0]
    
    win_idle_pcts = [r["tc_idle_secs"] / r["duration_secs"] for r in rows
                     if r["winner"] and r["duration_secs"] and r["duration_secs"] > 0]
    loss_idle_pcts = [r["tc_idle_secs"] / r["duration_secs"] for r in rows
                      if not r["winner"] and r["duration_secs"] and r["duration_secs"] > 0]
    
    # Villager production per match
    vill_rows = conn.execute(f"""
        WITH recent AS (
            SELECT m.id
            FROM matches m
            JOIN match_players mp ON mp.match_id = m.id
            WHERE mp.name = ?
            ORDER BY m.played_at DESC
            {limit_clause}
        )
        SELECT mu.match_id, mu.count
        FROM match_units mu
        JOIN recent r ON r.id = mu.match_id
        WHERE mu.player = ? AND mu.unit = 'Villager'
    """, (player, player)).fetchall()
    
    vill_counts = [r["count"] for r in vill_rows if r["count"]]
    
    return {
        "available": True,
        "avg_tc_idle_secs": round(sum(tc_idles) / len(tc_idles), 1),
        "avg_tc_idle_pct": round(sum(idle_pcts) / len(idle_pcts), 3) if idle_pcts else None,
        "win_tc_idle_pct": round(sum(win_idle_pcts) / len(win_idle_pcts), 3) if win_idle_pcts else None,
        "loss_tc_idle_pct": round(sum(loss_idle_pcts) / len(loss_idle_pcts), 3) if loss_idle_pcts else None,
        "avg_villagers": round(sum(vill_counts) / len(vill_counts), 1) if vill_counts else None,
        "sample": len(rows),
    }


def elo_trend(conn: sqlite3.Connection, player: str, n_last: int = 30) -> dict:
    """ELO trend with simple linear regression."""
    rows = conn.execute("""
        SELECT mp.elo, m.played_at
        FROM match_players mp
        JOIN matches m ON mp.match_id = m.id
        WHERE mp.name = ? AND mp.elo IS NOT NULL
        ORDER BY m.played_at ASC
    """, (player,)).fetchall()
    
    if len(rows) < 5:
        return {"available": False, "reason": "insufficient_data"}
    
    elos = [r["elo"] for r in rows]
    recent = elos[-n_last:] if len(elos) > n_last else elos
    
    # Simple linear regression on recent
    n = len(recent)
    x = list(range(n))
    x_mean = sum(x) / n
    y_mean = sum(recent) / n
    
    ss_xy = sum((x[i] - x_mean) * (recent[i] - y_mean) for i in range(n))
    ss_xx = sum((x[i] - x_mean) ** 2 for i in range(n))
    
    slope = ss_xy / ss_xx if ss_xx > 0 else 0
    
    if slope > 1:
        trend = "rising"
    elif slope < -1:
        trend = "falling"
    else:
        trend = "stable"
    
    return {
        "available": True,
        "current": elos[-1],
        "min": min(elos),
        "max": max(elos),
        "avg_recent": round(sum(recent) / len(recent), 1),
        "slope_per_game": round(slope, 2),
        "trend": trend,
        "total_games": len(elos),
        "recent_games": len(recent),
    }


def map_performance(conn: sqlite3.Connection, player: str, n_last: int = 0) -> list[dict]:
    """Winrate per map."""
    limit_clause = f"LIMIT {n_last}" if n_last > 0 else ""
    
    rows = conn.execute(f"""
        WITH recent AS (
            SELECT m.id, m.map_name, mp.winner
            FROM matches m
            JOIN match_players mp ON mp.match_id = m.id
            WHERE mp.name = ?
            ORDER BY m.played_at DESC
            {limit_clause}
        )
        SELECT map_name,
               COUNT(*) AS games,
               SUM(winner) AS wins,
               ROUND(CAST(SUM(winner) AS FLOAT) / COUNT(*), 2) AS winrate
        FROM recent
        GROUP BY map_name
        HAVING COUNT(*) >= 2
        ORDER BY games DESC
    """, (player,)).fetchall()
    
    return [dict(r) for r in rows]


PROFILE_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "knowledge", "aoe2", "player-profile.json")


def generate_player_profile(patterns: dict, output_path: str = None) -> dict:
    """Generate player profile from patterns. Auto-saved to knowledge/aoe2/."""
    p = patterns
    output_path = output_path or PROFILE_FILE
    
    elo_data = p.get("elo_trend", {})
    feudal = p.get("age_up_trends", {}).get("feudal", {})
    castle = p.get("age_up_trends", {}).get("castle", {})
    eco = p.get("eco_health", {})
    civs = p.get("civ_stats", [])
    
    cavalry_civs = {"Franks", "Teutons", "Lithuanians", "Burgundians", "Persians", "Huns", "Berbers"}
    main_civ = civs[0]["civ_name"] if civs else None
    
    profile = {
        "player": p["player"],
        "generated_at": p["generated_at"],
        "match_count": p["match_count"],
        "elo": {
            "current": elo_data.get("current"),
            "min": elo_data.get("min"),
            "max": elo_data.get("max"),
            "trend": elo_data.get("trend"),
            "slope": elo_data.get("slope_per_game"),
        } if elo_data.get("available") else {},
        "main_civ": main_civ,
        "civ_diversity": len(civs),
        "playstyle": "cavalry-focused" if main_civ in cavalry_civs else "mixed",
        "strengths": [],
        "weaknesses": [],
        "age_up_trends": p.get("age_up_trends", {}),
        "eco_health": eco,
    }
    
    # Derive strengths
    if feudal.get("trend") == "improving":
        profile["strengths"].append("feudal_time_improving")
    if elo_data.get("trend") == "rising":
        profile["strengths"].append("elo_rising")
    if eco.get("avg_tc_idle_pct", 1) < 0.3:
        profile["strengths"].append("low_tc_idle")
    
    # Derive weaknesses
    if castle.get("trend") == "worsening":
        profile["weaknesses"].append("castle_time_worsening")
    if castle.get("avg_recent_secs", 0) > 1300:
        profile["weaknesses"].append("castle_time_slow")
    if eco.get("avg_tc_idle_pct", 0) > 0.4:
        profile["weaknesses"].append("high_tc_idle")
    if feudal.get("trend") == "worsening":
        profile["weaknesses"].append("feudal_time_worsening")
    if len(civs) < 5:
        profile["weaknesses"].append("low_civ_diversity")
    
    # Best/worst map
    maps = p.get("map_performance", [])
    if maps:
        profile["best_map"] = max(maps, key=lambda x: x["winrate"])["map_name"]
        profile["worst_map"] = min(maps, key=lambda x: x["winrate"])["map_name"]
    
    # Save
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(profile, f, indent=2, ensure_ascii=False)
    
    return profile


KB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "knowledge", "aoe2")
KB_CHANGELOG = os.path.join(KB_DIR, "changelog.md")


def auto_promote(patterns: dict) -> list[str]:
    """Auto-promote consistent patterns to the Knowledge Base.
    
    Rules:
    - Matchup with >=5 games: add/update player_data in matchups.json
    - New civ encountered >=3 games: ensure it's in civilizations.json (flag only)
    - Benchmarks: update player-specific comparison notes
    
    Returns list of changes made.
    """
    changes = []
    
    # 1. Matchup auto-promotion
    matchups_path = os.path.join(KB_DIR, "matchups.json")
    matchups = {}
    try:
        with open(matchups_path) as f:
            matchups = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        matchups = {"description": "Matchup knowledge", "last_updated": "", "matchups": {}}
    
    matchup_data = matchups.get("matchups", {})
    updated_matchups = False
    
    for m in patterns.get("matchups", []):
        if m["games"] < 5:
            continue
        
        key = f"{m['my_civ']}_vs_{m['opp_civ']}"
        
        # Check if player_data changed
        existing = matchup_data.get(key, {})
        old_player_data = existing.get("player_data", {})
        new_player_data = {
            "games": m["games"],
            "wins": m["wins"],
            "winrate": m["winrate"],
            "avg_duration_min": round(m["avg_duration"] / 60, 1),
        }
        
        if old_player_data != new_player_data:
            if key not in matchup_data:
                # New matchup entry — create with player data only
                matchup_data[key] = {
                    "theoretical_advantage": "Unknown",
                    "reason": "No theory data yet — auto-created from match history.",
                    "suggested_strategy": "",
                    "player_data": new_player_data,
                }
                changes.append(f"matchup_new: {key} ({m['games']}G, {m['winrate']*100:.0f}%WR)")
            else:
                # Update existing matchup with player data
                matchup_data[key]["player_data"] = new_player_data
                changes.append(f"matchup_update: {key} ({m['games']}G, {m['winrate']*100:.0f}%WR)")
            updated_matchups = True
    
    if updated_matchups:
        matchups["matchups"] = matchup_data
        matchups["last_updated"] = datetime.now().strftime("%Y-%m-%d")
        with open(matchups_path, "w") as f:
            json.dump(matchups, f, indent=2, ensure_ascii=False)
    
    # 2. Civ coverage check — flag civs with >=3 games not in civilizations.json
    civs_path = os.path.join(KB_DIR, "civilizations.json")
    try:
        with open(civs_path) as f:
            civs_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        civs_data = {"civilizations": {}}
    
    known_civs = set(civs_data.get("civilizations", {}).keys())
    
    for c in patterns.get("civ_stats", []):
        if c["games"] >= 3 and c["civ_name"] not in known_civs:
            changes.append(f"civ_missing: {c['civ_name']} ({c['games']}G) — not in civilizations.json")
    
    # Also check opponent civs from matchups
    for m in patterns.get("matchups", []):
        if m["games"] >= 3 and m["opp_civ"] not in known_civs:
            changes.append(f"opp_civ_missing: {m['opp_civ']} ({m['games']}G) — not in civilizations.json")
    
    # Deduplicate
    changes = list(dict.fromkeys(changes))
    
    # 3. Log changes to changelog
    if changes:
        _append_changelog(changes, patterns["player"])
    
    return changes


def _append_changelog(changes: list[str], player: str):
    """Append promotion changes to knowledge/aoe2/changelog.md."""
    os.makedirs(os.path.dirname(KB_CHANGELOG), exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    entry = f"\n## {timestamp} — Auto-promotion ({player})\n\n"
    for c in changes:
        entry += f"- {c}\n"
    entry += "\n"
    
    # Create file if doesn't exist
    if not os.path.exists(KB_CHANGELOG):
        header = "# Knowledge Base Changelog\n\nAuto-generated log of pattern-to-KB promotions.\n\n"
        with open(KB_CHANGELOG, "w") as f:
            f.write(header)
    
    with open(KB_CHANGELOG, "a") as f:
        f.write(entry)


def generate_patterns(player: str = "blzulian", db_path: str = None, 
                       output_path: str = None) -> dict:
    """Generate all patterns and save to JSON."""
    conn = get_db(db_path)
    output_path = output_path or PATTERNS_FILE
    
    total = conn.execute(
        "SELECT COUNT(*) FROM match_players WHERE name = ?", (player,)
    ).fetchone()[0]
    
    patterns = {
        "generated_at": datetime.now().isoformat(),
        "player": player,
        "match_count": total,
        "matchups": matchup_stats(conn, player),
        "civ_stats": civ_stats(conn, player),
        "age_up_trends": age_up_trends(conn, player),
        "military_timing": military_timing(conn, player),
        "eco_health": eco_health(conn, player),
        "elo_trend": elo_trend(conn, player),
        "map_performance": map_performance(conn, player),
    }
    
    conn.close()
    
    # Save patterns to file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(patterns, f, indent=2, ensure_ascii=False)
    
    # Generate player profile from patterns
    try:
        generate_player_profile(patterns)
    except Exception as e:
        print(f"Player profile generation failed: {e}", file=sys.stderr)
    
    # Auto-promote patterns to KB
    try:
        promoted = auto_promote(patterns)
        if promoted:
            print(f"Auto-promoted {len(promoted)} updates to KB", file=sys.stderr)
    except Exception as e:
        print(f"Auto-promotion failed: {e}", file=sys.stderr)
    
    return patterns


def format_patterns_text(patterns: dict) -> str:
    """Format patterns as human-readable text."""
    lines = []
    p = patterns
    
    lines.append(f"📊 PATTERNS — {p['player']} ({p['match_count']} matches)")
    lines.append(f"Generated: {p['generated_at'][:16]}")
    lines.append("")
    
    # ELO
    elo = p.get("elo_trend", {})
    if elo.get("available"):
        emoji = {"rising": "📈", "falling": "📉", "stable": "➡️"}.get(elo["trend"], "")
        lines.append(f"🏆 ELO: {elo['current']} (min {elo['min']}, max {elo['max']}) {emoji} {elo['trend']}")
        lines.append(f"   Slope: {elo['slope_per_game']:+.1f}/game over last {elo['recent_games']} games")
        lines.append("")
    
    # Age-up trends
    trends = p.get("age_up_trends", {})
    if trends:
        lines.append("⏫ Age-Up Trends:")
        for age, data in trends.items():
            emoji = {"improving": "✅", "worsening": "⚠️", "stable": "➡️"}.get(data["trend"], "")
            avg = data["avg_recent_secs"]
            mins = int(avg) // 60
            secs = int(avg) % 60
            diff = data.get("diff_secs")
            diff_str = f" ({diff:+.0f}s vs previous)" if diff else ""
            lines.append(f"   {age.title()}: {mins}:{secs:02d} avg{diff_str} {emoji}")
        lines.append("")
    
    # Eco health
    eco = p.get("eco_health", {})
    if eco.get("available"):
        lines.append("🏠 Economy:")
        idle_pct = eco.get("avg_tc_idle_pct")
        if idle_pct:
            lines.append(f"   TC idle: {idle_pct*100:.0f}% avg")
            win_pct = eco.get("win_tc_idle_pct")
            loss_pct = eco.get("loss_tc_idle_pct")
            if win_pct and loss_pct:
                lines.append(f"   Wins: {win_pct*100:.0f}% idle | Losses: {loss_pct*100:.0f}% idle")
        if eco.get("avg_villagers"):
            lines.append(f"   Avg villagers: {eco['avg_villagers']:.0f}")
        lines.append("")
    
    # Civ stats (top 5)
    civs = p.get("civ_stats", [])
    if civs:
        lines.append("🛡️ Top Civs:")
        for c in civs[:5]:
            wr = c["winrate"] * 100
            lines.append(f"   {c['civ_name']}: {c['games']} games, {wr:.0f}% WR")
        lines.append("")
    
    # Map performance
    maps = p.get("map_performance", [])
    if maps:
        lines.append("🗺️ Maps:")
        for m in maps:
            wr = m["winrate"] * 100
            lines.append(f"   {m['map_name']}: {m['games']} games, {wr:.0f}% WR")
        lines.append("")
    
    # Worst matchups
    matchups = p.get("matchups", [])
    worst = [m for m in matchups if m["winrate"] < 0.4]
    if worst:
        lines.append("⚠️ Worst Matchups:")
        for m in worst[:5]:
            wr = m["winrate"] * 100
            lines.append(f"   {m['my_civ']} vs {m['opp_civ']}: {m['games']} games, {wr:.0f}% WR")
        lines.append("")
    
    best = [m for m in matchups if m["winrate"] > 0.6]
    if best:
        lines.append("✅ Best Matchups:")
        for m in best[:5]:
            wr = m["winrate"] * 100
            lines.append(f"   {m['my_civ']} vs {m['opp_civ']}: {m['games']} games, {wr:.0f}% WR")
        lines.append("")
    
    return "\n".join(lines)


if __name__ == "__main__":
    patterns = generate_patterns()
    print(format_patterns_text(patterns))
