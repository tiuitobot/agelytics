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
        for p in match["players"]:
            tc_idle = tc_idle_data.get(p["name"])
            est_idle = est_idle_data.get(p["name"])
            conn.execute("""
                INSERT INTO match_players (match_id, name, number, civ_id, civ_name,
                                           color_id, winner, user_id, elo, eapm, tc_idle_secs,
                                           estimated_idle_vill_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                match_id, p["name"], p["number"], p["civ_id"], p["civ_name"],
                p["color_id"], 1 if p["winner"] else 0, p["user_id"],
                p["elo"], p["eapm"], tc_idle, est_idle,
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
    
    return match
