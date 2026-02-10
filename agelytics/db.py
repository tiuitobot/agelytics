"""SQLite storage for match data."""

import sqlite3
import os
from pathlib import Path
from typing import Optional


DEFAULT_DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "aoe2_matches.db")


def get_db(db_path: str = None) -> sqlite3.Connection:
    """Get a database connection, creating tables if needed."""
    db_path = db_path or DEFAULT_DB
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    _create_tables(conn)
    return conn


def _create_tables(conn: sqlite3.Connection):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_hash TEXT UNIQUE,
            file_path TEXT,
            played_at TEXT,
            duration_secs REAL,
            map_name TEXT,
            map_id INTEGER,
            game_type TEXT,
            diplomacy TEXT,
            speed TEXT,
            pop_limit INTEGER,
            completed INTEGER,
            rated INTEGER,
            version TEXT,
            resign_player TEXT,
            ingested_at TEXT DEFAULT (datetime('now'))
        );
        
        CREATE TABLE IF NOT EXISTS match_players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_id INTEGER REFERENCES matches(id),
            name TEXT,
            number INTEGER,
            civ_id INTEGER,
            civ_name TEXT,
            color_id INTEGER,
            winner INTEGER,
            user_id INTEGER,
            elo INTEGER,
            eapm INTEGER,
            tc_idle_secs REAL
        );
        
        CREATE TABLE IF NOT EXISTS match_age_ups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_id INTEGER REFERENCES matches(id),
            player TEXT,
            age TEXT,
            timestamp_secs REAL
        );
        
        CREATE TABLE IF NOT EXISTS match_units (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_id INTEGER REFERENCES matches(id),
            player TEXT,
            unit TEXT,
            count INTEGER
        );
        
        CREATE TABLE IF NOT EXISTS match_researches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_id INTEGER REFERENCES matches(id),
            player TEXT,
            tech TEXT,
            timestamp_secs REAL
        );
        
        CREATE TABLE IF NOT EXISTS match_buildings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_id INTEGER REFERENCES matches(id),
            player TEXT,
            building TEXT,
            count INTEGER
        );
        
        CREATE INDEX IF NOT EXISTS idx_matches_played ON matches(played_at);
        CREATE INDEX IF NOT EXISTS idx_matches_hash ON matches(file_hash);
        CREATE INDEX IF NOT EXISTS idx_players_match ON match_players(match_id);
        CREATE INDEX IF NOT EXISTS idx_players_name ON match_players(name);
        CREATE INDEX IF NOT EXISTS idx_age_ups_match ON match_age_ups(match_id);
        CREATE INDEX IF NOT EXISTS idx_units_match ON match_units(match_id);
        CREATE INDEX IF NOT EXISTS idx_researches_match ON match_researches(match_id);
        CREATE INDEX IF NOT EXISTS idx_buildings_match ON match_buildings(match_id);
    """)
    conn.commit()
    
    # Migrations: add columns if missing (backward compatible)
    _migrate(conn)


def _migrate(conn: sqlite3.Connection):
    """Apply backward-compatible migrations (ALTER TABLE ADD COLUMN)."""
    # Check existing columns in match_players
    cursor = conn.execute("PRAGMA table_info(match_players)")
    existing_cols = {row[1] for row in cursor.fetchall()}
    
    migrations = [
        ("match_players", "estimated_idle_vill_time", "REAL"),
        ("match_players", "farm_gap_average", "REAL"),
        ("match_players", "military_timing_index", "REAL"),
        ("match_players", "tc_count_final", "INTEGER"),
        ("match_players", "opening_strategy", "TEXT"),
        ("match_players", "tc_idle_dark", "REAL"),
        ("match_players", "tc_idle_feudal", "REAL"),
        ("match_players", "tc_idle_castle", "REAL"),
        ("match_players", "tc_idle_imperial", "REAL"),
        ("match_players", "production_buildings_json", "TEXT"),
        ("match_players", "housed_count", "INTEGER"),
    ]
    
    for table, col, col_type in migrations:
        if col not in existing_cols:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}")
    
    conn.commit()


def insert_match(conn: sqlite3.Connection, match: dict) -> Optional[int]:
    """Insert a match and its players. Returns match_id or None if duplicate."""
    try:
        cur = conn.execute("""
            INSERT INTO matches (file_hash, file_path, played_at, duration_secs,
                                 map_name, map_id, game_type, diplomacy, speed,
                                 pop_limit, completed, rated, version, resign_player)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            match["file_hash"], match["file_path"], match["played_at"],
            match["duration_secs"], match["map_name"], match["map_id"],
            match["game_type"], match["diplomacy"], match["speed"],
            match["pop_limit"], 1 if match["completed"] else 0,
            1 if match.get("rated") else 0, match["version"],
            match.get("resign_player"),
        ))
        match_id = cur.lastrowid

        tc_idle_data = match.get("tc_idle", {})
        est_idle_data = match.get("estimated_idle_villager_time", {})
        metrics_data = match.get("metrics", {})
        openings_data = match.get("openings", {})
        tc_idle_by_age_data = match.get("tc_idle_by_age", {})
        production_buildings_data = match.get("production_buildings_by_age", {})
        housed_count_data = match.get("housed_count", {})
        
        for p in match["players"]:
            player_name = p["name"]
            tc_idle = tc_idle_data.get(player_name)
            est_idle = est_idle_data.get(player_name)
            
            # Extrair métricas do player
            player_metrics = metrics_data.get(player_name, {})
            farm_gap = player_metrics.get("farm_gap_average")
            mil_timing = player_metrics.get("military_timing_index")
            
            # TC count final (último valor da progressão)
            tc_prog = player_metrics.get("tc_count_progression")
            tc_count_final = tc_prog[-1][1] if tc_prog and len(tc_prog) > 0 else None
            
            # Opening strategy
            opening = openings_data.get(player_name)
            
            # TC idle by age
            tc_idle_by_age = tc_idle_by_age_data.get(player_name, {})
            tc_idle_dark = tc_idle_by_age.get("Dark")
            tc_idle_feudal = tc_idle_by_age.get("Feudal")
            tc_idle_castle = tc_idle_by_age.get("Castle")
            tc_idle_imperial = tc_idle_by_age.get("Imperial")
            
            # Production buildings by age + housed count
            import json
            prod_buildings = production_buildings_data.get(player_name, {})
            prod_buildings_json = json.dumps(prod_buildings) if prod_buildings else None
            housed_count = housed_count_data.get(player_name)
            
            conn.execute("""
                INSERT INTO match_players (match_id, name, number, civ_id, civ_name,
                                           color_id, winner, user_id, elo, eapm, tc_idle_secs,
                                           estimated_idle_vill_time, farm_gap_average,
                                           military_timing_index, tc_count_final,
                                           opening_strategy, tc_idle_dark, tc_idle_feudal,
                                           tc_idle_castle, tc_idle_imperial,
                                           production_buildings_json, housed_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                match_id, player_name, p["number"], p["civ_id"], p["civ_name"],
                p["color_id"], 1 if p["winner"] else 0, p["user_id"],
                p["elo"], p["eapm"], tc_idle, est_idle, farm_gap, mil_timing, tc_count_final,
                opening, tc_idle_dark, tc_idle_feudal, tc_idle_castle, tc_idle_imperial,
                prod_buildings_json, housed_count,
            ))

        # Insert detailed data if present
        for age_up in match.get("age_ups", []):
            conn.execute("""
                INSERT INTO match_age_ups (match_id, player, age, timestamp_secs)
                VALUES (?, ?, ?, ?)
            """, (match_id, age_up["player"], age_up["age"], age_up["timestamp_secs"]))
        
        for player, units in match.get("unit_production", {}).items():
            for unit, count in units.items():
                conn.execute("""
                    INSERT INTO match_units (match_id, player, unit, count)
                    VALUES (?, ?, ?, ?)
                """, (match_id, player, unit, count))
        
        for research in match.get("researches", []):
            conn.execute("""
                INSERT INTO match_researches (match_id, player, tech, timestamp_secs)
                VALUES (?, ?, ?, ?)
            """, (match_id, research["player"], research["tech"], research["timestamp_secs"]))
        
        for player, buildings in match.get("buildings", {}).items():
            for building, count in buildings.items():
                conn.execute("""
                    INSERT INTO match_buildings (match_id, player, building, count)
                    VALUES (?, ?, ?, ?)
                """, (match_id, player, building, count))

        conn.commit()
        return match_id

    except sqlite3.IntegrityError:
        # Duplicate file_hash
        return None


def get_last_match(conn: sqlite3.Connection) -> Optional[dict]:
    """Get the most recent match with players."""
    row = conn.execute(
        "SELECT * FROM matches ORDER BY played_at DESC LIMIT 1"
    ).fetchone()
    if not row:
        return None
    return _match_with_players(conn, dict(row))


def get_match_by_id(conn: sqlite3.Connection, match_id: int) -> Optional[dict]:
    """Get a match by ID with players."""
    row = conn.execute(
        "SELECT * FROM matches WHERE id = ?", (match_id,)
    ).fetchone()
    if not row:
        return None
    return _match_with_players(conn, dict(row))


def get_player_stats(conn: sqlite3.Connection, player_name: str) -> dict:
    """Get aggregate stats for a player."""
    rows = conn.execute("""
        SELECT mp.*, m.duration_secs, m.map_name, m.played_at
        FROM match_players mp
        JOIN matches m ON mp.match_id = m.id
        WHERE mp.name = ?
        ORDER BY m.played_at DESC
    """, (player_name,)).fetchall()

    if not rows:
        return {"name": player_name, "matches": 0}

    total = len(rows)
    wins = sum(1 for r in rows if r["winner"])
    elos = [r["elo"] for r in rows if r["elo"]]
    # Filter out eAPM outliers from ultra-short games (drops inflate eAPM absurdly)
    eapms = [r["eapm"] for r in rows if r["eapm"] and r["eapm"] < 100]
    
    # Civ stats
    civ_counts = {}
    for r in rows:
        c = r["civ_name"]
        if c not in civ_counts:
            civ_counts[c] = {"played": 0, "won": 0}
        civ_counts[c]["played"] += 1
        if r["winner"]:
            civ_counts[c]["won"] += 1

    return {
        "name": player_name,
        "matches": total,
        "wins": wins,
        "losses": total - wins,
        "winrate": wins / total * 100 if total else 0,
        "elo_current": elos[0] if elos else None,
        "elo_min": min(elos) if elos else None,
        "elo_max": max(elos) if elos else None,
        "avg_eapm": sum(eapms) / len(eapms) if eapms else None,
        "civs": civ_counts,
    }


def count_matches(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) FROM matches").fetchone()[0]


def get_all_matches(conn: sqlite3.Connection, player_name: str = None, limit: int = 50) -> list[dict]:
    """Get all matches, optionally filtered by player name, ordered by date DESC."""
    if player_name:
        # Filter matches where the player participated
        rows = conn.execute("""
            SELECT DISTINCT m.*
            FROM matches m
            JOIN match_players mp ON mp.match_id = m.id
            WHERE mp.name = ?
            ORDER BY m.played_at DESC
            LIMIT ?
        """, (player_name, limit)).fetchall()
    else:
        rows = conn.execute("""
            SELECT * FROM matches
            ORDER BY played_at DESC
            LIMIT ?
        """, (limit,)).fetchall()
    
    matches = []
    for row in rows:
        match = dict(row)
        match = _match_with_players(conn, match)
        matches.append(match)
    
    return matches


def _match_with_players(conn: sqlite3.Connection, match: dict) -> dict:
    """Fetch players and detailed data for a match."""
    players = conn.execute(
        "SELECT * FROM match_players WHERE match_id = ? ORDER BY number",
        (match["id"],)
    ).fetchall()
    match["players"] = [dict(p) for p in players]
    
    # Fetch age-ups
    age_ups = conn.execute(
        "SELECT player, age, timestamp_secs FROM match_age_ups WHERE match_id = ? ORDER BY timestamp_secs",
        (match["id"],)
    ).fetchall()
    match["age_ups"] = [dict(a) for a in age_ups]
    
    # Fetch unit production
    units = conn.execute(
        "SELECT player, unit, count FROM match_units WHERE match_id = ?",
        (match["id"],)
    ).fetchall()
    unit_production = {}
    for u in units:
        player = u["player"]
        if player not in unit_production:
            unit_production[player] = {}
        unit_production[player][u["unit"]] = u["count"]
    match["unit_production"] = unit_production
    
    # Fetch researches
    researches = conn.execute(
        "SELECT player, tech, timestamp_secs FROM match_researches WHERE match_id = ? ORDER BY timestamp_secs",
        (match["id"],)
    ).fetchall()
    match["researches"] = [dict(r) for r in researches]
    
    # Fetch buildings
    buildings = conn.execute(
        "SELECT player, building, count FROM match_buildings WHERE match_id = ?",
        (match["id"],)
    ).fetchall()
    building_counts = {}
    for b in buildings:
        player = b["player"]
        if player not in building_counts:
            building_counts[player] = {}
        building_counts[player][b["building"]] = b["count"]
    match["buildings"] = building_counts
    
    # Reconstruct helper data structures for metrics
    # tc_idle dict from match_players.tc_idle_secs
    tc_idle = {}
    estimated_idle = {}
    for player in match["players"]:
        pname = player["name"]
        if player.get("tc_idle_secs") is not None:
            tc_idle[pname] = player["tc_idle_secs"]
        if player.get("estimated_idle_vill_time") is not None:
            estimated_idle[pname] = player["estimated_idle_vill_time"]
    
    match["tc_idle"] = tc_idle
    match["estimated_idle_villager_time"] = estimated_idle
    
    # Reconstruct vill_queue_timestamps from unit production (approximate)
    # We don't have exact timestamps, so metrics that need this will return None
    # This is OK - they'll compute correctly if replay is re-parsed
    match["vill_queue_timestamps"] = {}
    
    # Reconstruct enriched data (for farm_gap, military_timing, tc_progression)
    # These are NOT in DB, so metrics depending on them will return None
    # unless we re-parse the replay file
    match["_farm_build_timestamps"] = {}
    match["_first_military_timestamp"] = {}
    match["_tc_build_timestamps"] = {}
    
    # Reconstruct production_buildings_by_age and housed_count
    import json
    production_buildings_by_age = {}
    housed_count = {}
    for player in match["players"]:
        pname = player["name"]
        if player.get("production_buildings_json"):
            try:
                production_buildings_by_age[pname] = json.loads(player["production_buildings_json"])
            except:
                production_buildings_by_age[pname] = {}
        if player.get("housed_count") is not None:
            housed_count[pname] = player["housed_count"]
    
    match["production_buildings_by_age"] = production_buildings_by_age
    match["housed_count"] = housed_count
    
    # Reconstruct metrics for each player
    # Use stored values from DB columns where available, compute rest
    from .metrics import compute_all_metrics
    metrics_by_player = {}
    for player in match["players"]:
        player_name = player["name"]
        
        # Start with stored metric values
        stored_metrics = {
            "tc_idle_percent": None,
            "farm_gap_average": player.get("farm_gap_average"),
            "military_timing_index": player.get("military_timing_index"),
            "tc_count_progression": None,
            "estimated_idle_villager_time": player.get("estimated_idle_vill_time"),
            "villager_production_rate_by_age": None,
            "resource_collection_efficiency": None,
        }
        
        # Compute metrics that can be derived from available data
        computed = compute_all_metrics(match, player_name)
        
        # Merge: prefer stored values, fall back to computed
        for key in computed:
            if stored_metrics.get(key) is None:
                stored_metrics[key] = computed[key]
        
        # Build tc_count_progression from stored tc_count_final if available
        if player.get("tc_count_final") and stored_metrics["tc_count_progression"] is None:
            # Basic progression: start with 1, end with final count
            # This is approximate without timestamps
            tc_final = player["tc_count_final"]
            stored_metrics["tc_count_progression"] = [(0.0, 1)]
            if tc_final > 1:
                # Approximate: assume TCs built evenly spaced (very rough)
                duration = match.get("duration_secs", 0)
                if duration > 0:
                    for i in range(2, tc_final + 1):
                        # Rough estimate: TCs built after Castle Age (50% of game)
                        ts = duration * (0.5 + (i - 2) * 0.1)
                        stored_metrics["tc_count_progression"].append((ts, i))
        
        metrics_by_player[player_name] = stored_metrics
    
    match["metrics"] = metrics_by_player
    
    # Build action_log (formatted text of all actions for deep coach)
    action_log_lines = []
    
    # Age-ups
    for age_up in match["age_ups"]:
        t = age_up["timestamp_secs"]
        action_log_lines.append(
            f"[{int(t)//60:02d}:{int(t)%60:02d}] {age_up['player']} → {age_up['age']}"
        )
    
    # Researches (sorted by time)
    for research in sorted(match["researches"], key=lambda x: x["timestamp_secs"]):
        t = research["timestamp_secs"]
        action_log_lines.append(
            f"[{int(t)//60:02d}:{int(t)%60:02d}] {research['player']} researched {research['tech']}"
        )
    
    match["action_log"] = action_log_lines
    
    return match
