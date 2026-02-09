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
            eapm INTEGER
        );
        
        CREATE INDEX IF NOT EXISTS idx_matches_played ON matches(played_at);
        CREATE INDEX IF NOT EXISTS idx_matches_hash ON matches(file_hash);
        CREATE INDEX IF NOT EXISTS idx_players_match ON match_players(match_id);
        CREATE INDEX IF NOT EXISTS idx_players_name ON match_players(name);
    """)
    conn.commit()


def insert_match(conn: sqlite3.Connection, match: dict) -> Optional[int]:
    """Insert a match and its players. Returns match_id or None if duplicate."""
    try:
        cur = conn.execute("""
            INSERT INTO matches (file_hash, file_path, played_at, duration_secs,
                                 map_name, map_id, game_type, diplomacy, speed,
                                 pop_limit, completed, rated, version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            match["file_hash"], match["file_path"], match["played_at"],
            match["duration_secs"], match["map_name"], match["map_id"],
            match["game_type"], match["diplomacy"], match["speed"],
            match["pop_limit"], 1 if match["completed"] else 0,
            1 if match.get("rated") else 0, match["version"],
        ))
        match_id = cur.lastrowid

        for p in match["players"]:
            conn.execute("""
                INSERT INTO match_players (match_id, name, number, civ_id, civ_name,
                                           color_id, winner, user_id, elo, eapm)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                match_id, p["name"], p["number"], p["civ_id"], p["civ_name"],
                p["color_id"], 1 if p["winner"] else 0, p["user_id"],
                p["elo"], p["eapm"],
            ))

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
    eapms = [r["eapm"] for r in rows if r["eapm"]]
    
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
    players = conn.execute(
        "SELECT * FROM match_players WHERE match_id = ? ORDER BY number",
        (match["id"],)
    ).fetchall()
    match["players"] = [dict(p) for p in players]
    return match
