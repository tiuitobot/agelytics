"""Cross-game player statistics queries."""

import json
import sqlite3
from typing import Optional


def player_stats(conn: sqlite3.Connection, player_name: str) -> dict:
    """Get overall stats for a player: games, wins, losses, win rate, avg duration, ELO range."""
    
    cursor = conn.execute("""
        SELECT 
            COUNT(*) as total_games,
            SUM(CASE WHEN winner = 1 THEN 1 ELSE 0 END) as wins,
            SUM(CASE WHEN winner = 0 THEN 1 ELSE 0 END) as losses,
            AVG(m.duration_secs) as avg_duration,
            MIN(mp.elo) as min_elo,
            MAX(mp.elo) as max_elo,
            AVG(mp.elo) as avg_elo
        FROM match_players mp
        JOIN matches m ON mp.match_id = m.id
        WHERE mp.name = ?
    """, (player_name,))
    
    row = cursor.fetchone()
    if not row or row["total_games"] == 0:
        return {
            "player_name": player_name,
            "total_games": 0,
            "wins": 0,
            "losses": 0,
            "win_rate": 0.0,
            "avg_duration_mins": 0.0,
            "elo_range": None,
        }
    
    total = row["total_games"]
    wins = row["wins"]
    win_rate = (wins / total * 100) if total > 0 else 0.0
    
    return {
        "player_name": player_name,
        "total_games": total,
        "wins": wins,
        "losses": row["losses"],
        "win_rate": round(win_rate, 1),
        "avg_duration_mins": round(row["avg_duration"] / 60, 1) if row["avg_duration"] else 0,
        "elo_range": {
            "min": row["min_elo"],
            "max": row["max_elo"],
            "avg": round(row["avg_elo"], 0) if row["avg_elo"] else None,
        } if row["min_elo"] is not None else None,
    }


def win_rate_by_civ(conn: sqlite3.Connection, player_name: str) -> list[dict]:
    """Get win rate per civilization played."""
    
    cursor = conn.execute("""
        SELECT 
            civ_name,
            COUNT(*) as games,
            SUM(CASE WHEN winner = 1 THEN 1 ELSE 0 END) as wins,
            ROUND(100.0 * SUM(CASE WHEN winner = 1 THEN 1 ELSE 0 END) / COUNT(*), 1) as win_rate
        FROM match_players
        WHERE name = ?
        GROUP BY civ_name
        ORDER BY games DESC
    """, (player_name,))
    
    results = []
    for row in cursor.fetchall():
        results.append({
            "civ": row["civ_name"],
            "games": row["games"],
            "wins": row["wins"],
            "win_rate": row["win_rate"],
        })
    
    return results


def win_rate_by_map(conn: sqlite3.Connection, player_name: str) -> list[dict]:
    """Get win rate per map."""
    
    cursor = conn.execute("""
        SELECT 
            m.map_name,
            COUNT(*) as games,
            SUM(CASE WHEN mp.winner = 1 THEN 1 ELSE 0 END) as wins,
            ROUND(100.0 * SUM(CASE WHEN mp.winner = 1 THEN 1 ELSE 0 END) / COUNT(*), 1) as win_rate
        FROM match_players mp
        JOIN matches m ON mp.match_id = m.id
        WHERE mp.name = ?
        GROUP BY m.map_name
        ORDER BY games DESC
    """, (player_name,))
    
    results = []
    for row in cursor.fetchall():
        results.append({
            "map": row["map_name"],
            "games": row["games"],
            "wins": row["wins"],
            "win_rate": row["win_rate"],
        })
    
    return results


def win_rate_by_opening(conn: sqlite3.Connection, player_name: str) -> list[dict]:
    """Get win rate per opening strategy."""
    
    cursor = conn.execute("""
        SELECT 
            opening_strategy,
            COUNT(*) as games,
            SUM(CASE WHEN winner = 1 THEN 1 ELSE 0 END) as wins,
            ROUND(100.0 * SUM(CASE WHEN winner = 1 THEN 1 ELSE 0 END) / COUNT(*), 1) as win_rate
        FROM match_players
        WHERE name = ? AND opening_strategy IS NOT NULL
        GROUP BY opening_strategy
        ORDER BY games DESC
    """, (player_name,))
    
    results = []
    for row in cursor.fetchall():
        results.append({
            "opening": row["opening_strategy"],
            "games": row["games"],
            "wins": row["wins"],
            "win_rate": row["win_rate"],
        })
    
    return results


def elo_progression(conn: sqlite3.Connection, player_name: str) -> list[dict]:
    """Get ELO progression over time: [{date, elo, result}]."""
    
    cursor = conn.execute("""
        SELECT 
            m.played_at,
            mp.elo,
            mp.winner
        FROM match_players mp
        JOIN matches m ON mp.match_id = m.id
        WHERE mp.name = ? AND mp.elo IS NOT NULL
        ORDER BY m.played_at ASC
    """, (player_name,))
    
    results = []
    for row in cursor.fetchall():
        results.append({
            "date": row["played_at"],
            "elo": row["elo"],
            "result": "win" if row["winner"] else "loss",
        })
    
    return results


def avg_metrics(conn: sqlite3.Connection, player_name: str) -> dict:
    """Get average metrics across all games: TC idle, farm gap, housed count."""
    
    cursor = conn.execute("""
        SELECT 
            AVG(tc_idle_secs) as avg_tc_idle,
            AVG(farm_gap_average) as avg_farm_gap,
            AVG(housed_count) as avg_housed,
            AVG(tc_idle_dark) as avg_tc_idle_dark,
            AVG(tc_idle_feudal) as avg_tc_idle_feudal,
            AVG(tc_idle_castle) as avg_tc_idle_castle,
            AVG(tc_idle_imperial) as avg_tc_idle_imperial
        FROM match_players
        WHERE name = ?
    """, (player_name,))
    
    row = cursor.fetchone()
    if not row:
        return {}
    
    return {
        "avg_tc_idle_secs": round(row["avg_tc_idle"], 1) if row["avg_tc_idle"] else None,
        "avg_farm_gap_secs": round(row["avg_farm_gap"], 1) if row["avg_farm_gap"] else None,
        "avg_housed_count": round(row["avg_housed"], 1) if row["avg_housed"] else None,
        "avg_tc_idle_by_age": {
            "Dark": round(row["avg_tc_idle_dark"], 1) if row["avg_tc_idle_dark"] else None,
            "Feudal": round(row["avg_tc_idle_feudal"], 1) if row["avg_tc_idle_feudal"] else None,
            "Castle": round(row["avg_tc_idle_castle"], 1) if row["avg_tc_idle_castle"] else None,
            "Imperial": round(row["avg_tc_idle_imperial"], 1) if row["avg_tc_idle_imperial"] else None,
        },
    }


def stats_report(conn: sqlite3.Connection, player_name: str) -> str:
    """Generate a formatted career stats report for a player."""
    
    overall = player_stats(conn, player_name)
    
    if overall["total_games"] == 0:
        return f"📊 Career Stats: {player_name}\n\nNo games found for this player."
    
    report = []
    report.append(f"📊 Career Stats: {player_name}")
    report.append("=" * 50)
    report.append("")
    
    # Overall stats
    report.append("🎮 Overall Performance")
    report.append(f"  Games Played: {overall['total_games']}")
    report.append(f"  Wins: {overall['wins']} | Losses: {overall['losses']}")
    report.append(f"  Win Rate: {overall['win_rate']}%")
    report.append(f"  Avg Game Duration: {overall['avg_duration_mins']} minutes")
    
    if overall["elo_range"]:
        elo = overall["elo_range"]
        if elo["avg"]:
            report.append(f"  ELO: {int(elo['avg'])} (range: {elo['min']}-{elo['max']})")
    report.append("")
    
    # Civilization stats
    civ_stats = win_rate_by_civ(conn, player_name)
    if civ_stats:
        report.append("🏛️ Performance by Civilization")
        for stat in civ_stats[:10]:  # Top 10
            report.append(f"  {stat['civ']}: {stat['win_rate']}% ({stat['wins']}/{stat['games']} games)")
        report.append("")
    
    # Map stats
    map_stats = win_rate_by_map(conn, player_name)
    if map_stats:
        report.append("🗺️ Performance by Map")
        for stat in map_stats[:10]:  # Top 10
            report.append(f"  {stat['map']}: {stat['win_rate']}% ({stat['wins']}/{stat['games']} games)")
        report.append("")
    
    # Opening stats
    opening_stats = win_rate_by_opening(conn, player_name)
    if opening_stats:
        report.append("🎯 Performance by Opening Strategy")
        for stat in opening_stats:
            report.append(f"  {stat['opening']}: {stat['win_rate']}% ({stat['wins']}/{stat['games']} games)")
        report.append("")
    
    # Average metrics
    metrics = avg_metrics(conn, player_name)
    if metrics:
        report.append("📈 Average Metrics")
        if metrics.get("avg_tc_idle_secs") is not None:
            report.append(f"  TC Idle Time: {metrics['avg_tc_idle_secs']}s")
        
        if metrics.get("avg_tc_idle_by_age"):
            tc_by_age = metrics["avg_tc_idle_by_age"]
            if any(v is not None for v in tc_by_age.values()):
                report.append("  TC Idle by Age:")
                for age, value in tc_by_age.items():
                    if value is not None:
                        report.append(f"    {age}: {value}s")
        
        if metrics.get("avg_farm_gap_secs") is not None:
            report.append(f"  Farm Gap: {metrics['avg_farm_gap_secs']}s")
        
        if metrics.get("avg_housed_count") is not None:
            report.append(f"  Housed Count: {metrics['avg_housed_count']}")
        report.append("")
    
    return "\n".join(report)
