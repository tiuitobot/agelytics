"""Parse AoE2 DE replay files using mgz."""

import os
import re
import hashlib
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Optional

from mgz.summary import Summary

from .data import civ_name, map_name


def parse_replay(filepath: str) -> Optional[dict]:
    """Parse a .aoe2record file and return structured match data.
    
    Returns None if the file can't be parsed or is not a multiplayer game.
    """
    filepath = str(filepath)
    
    try:
        with open(filepath, "rb") as f:
            s = Summary(f)
    except Exception as e:
        return None

    try:
        # Check if ranked
        rated = False
        try:
            rated = bool(s.match.rated)
        except Exception:
            pass

        players_raw = s.get_players() or []
        duration_ms = s.get_duration() or 0
        settings = s.get_settings() or {}
        completed = s.get_completed()
        
        # Extract map info
        map_data = s.get_map()
        map_id = None
        map_str = "Unknown"
        if isinstance(map_data, dict):
            # Try common keys for map name/id
            map_id = map_data.get("id") or map_data.get("type")
            map_str = map_data.get("name") or map_name(map_id)
            if not map_data.get("name") and map_id is None:
                map_str = "Unknown"
        elif isinstance(map_data, (list, tuple)) and len(map_data) >= 2:
            map_id, map_str = map_data[0], map_data[1]
        
        # Extract version
        version_raw = s.get_version()
        version = "Unknown"
        if isinstance(version_raw, (list, tuple)):
            version = str(version_raw[0]) if version_raw else "Unknown"
        elif version_raw:
            version = str(version_raw)

        # Diplomacy / game type
        diplomacy = settings.get("diplomacy_type", "Unknown")
        game_type_raw = settings.get("type", [None, "Unknown"])
        game_type = game_type_raw[1] if isinstance(game_type_raw, (list, tuple)) else str(game_type_raw)
        
        speed_raw = settings.get("speed", [None, "Unknown"])
        speed = speed_raw[1] if isinstance(speed_raw, (list, tuple)) else str(speed_raw)

        pop_limit = settings.get("population_limit", 200)

        # Duration
        duration_secs = duration_ms / 1000.0 if duration_ms else 0

        # File hash for dedup
        file_hash = _file_hash(filepath)

        # Timestamp from filename or file mtime
        played_at = _extract_timestamp(filepath)

        # Build players
        players = []
        human_count = 0
        for p in players_raw:
            if not p.get("human", False):
                continue
            human_count += 1
            players.append({
                "name": p.get("name", "Unknown"),
                "number": p.get("number", 0),
                "civ_id": p.get("civilization", 0),
                "civ_name": civ_name(p.get("civilization", 0)),
                "color_id": p.get("color_id", 0),
                "winner": p.get("winner", False),
                "user_id": p.get("user_id"),
                "elo": p.get("rate_snapshot"),
                "eapm": p.get("eapm"),
            })

        # Skip single-player (only 1 human)
        if human_count < 2:
            return None

        # Skip unranked
        if not rated:
            return None

        # Extract detailed action log data (graceful degradation)
        detailed_data = _extract_detailed_data(s, players)

        return {
            "file_path": filepath,
            "file_hash": file_hash,
            "played_at": played_at,
            "duration_secs": duration_secs,
            "map_name": map_str if map_str != "Unknown" else map_name(map_id),
            "map_id": map_id,
            "game_type": game_type,
            "diplomacy": diplomacy,
            "speed": speed,
            "pop_limit": pop_limit,
            "completed": completed,
            "rated": rated,
            "version": version,
            "players": players,
            **detailed_data,  # Merge detailed data (age_ups, units, etc.)
        }

    except Exception as e:
        return None


def _extract_detailed_data(summary: Summary, players: list) -> dict:
    """Extract detailed action log data from replay.
    
    Returns dict with age_ups, unit_production, researches, buildings, resign_player.
    Gracefully degrades if data unavailable.
    """
    result = {
        "age_ups": [],
        "unit_production": {},
        "researches": [],
        "buildings": {},
        "resign_player": None,
    }
    
    try:
        match = summary.match
        
        # Extract age-ups from match.uptimes
        # Format: "[0:10:02.212000] blzulian -> Age.FEUDAL_AGE"
        if hasattr(match, "uptimes") and match.uptimes:
            age_pattern = re.compile(r"\[(\d+):(\d+):(\d+)\.(\d+)\]\s+(.+?)\s+->\s+Age\.(.+)")
            for uptime_str in match.uptimes:
                m = age_pattern.match(str(uptime_str))
                if m:
                    hours, mins, secs, microsecs, player_name, age_enum = m.groups()
                    timestamp_secs = int(hours) * 3600 + int(mins) * 60 + int(secs) + int(microsecs) / 1000000.0
                    
                    # Convert age enum to readable name
                    age_map = {
                        "FEUDAL_AGE": "Feudal Age",
                        "CASTLE_AGE": "Castle Age",
                        "IMPERIAL_AGE": "Imperial Age",
                    }
                    age_name = age_map.get(age_enum, age_enum)
                    
                    result["age_ups"].append({
                        "player": player_name.strip(),
                        "age": age_name,
                        "timestamp_secs": timestamp_secs,
                    })
        
        # Extract inputs (units, researches, buildings, resigns)
        if hasattr(match, "inputs") and match.inputs:
            unit_counts = defaultdict(lambda: defaultdict(int))
            building_counts = defaultdict(lambda: defaultdict(int))
            
            for inp in match.inputs:
                try:
                    player_name = inp.player.name if hasattr(inp.player, "name") else None
                    if not player_name:
                        continue
                    
                    timestamp_secs = inp.timestamp.total_seconds() if hasattr(inp.timestamp, "total_seconds") else 0
                    
                    if inp.type == "Queue" and hasattr(inp, "payload") and inp.payload:
                        # Unit production
                        unit = inp.payload.get("unit")
                        amount = inp.payload.get("amount", 1)
                        if unit:
                            unit_counts[player_name][unit] += amount
                    
                    elif inp.type == "Research" and hasattr(inp, "payload") and inp.payload:
                        # Research
                        tech = inp.payload.get("technology")
                        if tech:
                            result["researches"].append({
                                "player": player_name,
                                "tech": tech,
                                "timestamp_secs": timestamp_secs,
                            })
                    
                    elif inp.type == "Build" and hasattr(inp, "payload") and inp.payload:
                        # Building
                        building = inp.payload.get("building")
                        if building:
                            building_counts[player_name][building] += 1
                    
                    elif inp.type == "Resign":
                        # Resignation (only record the first resign)
                        if not result["resign_player"]:
                            result["resign_player"] = player_name
                
                except Exception:
                    # Skip individual inputs that fail
                    continue
            
            # Convert defaultdicts to regular dicts
            result["unit_production"] = {
                player: dict(units) for player, units in unit_counts.items()
            }
            result["buildings"] = {
                player: dict(buildings) for player, buildings in building_counts.items()
            }
    
    except Exception:
        # If detailed extraction fails entirely, return empty data
        pass
    
    return result


def _file_hash(filepath: str) -> str:
    """Quick hash of first 64KB for dedup."""
    h = hashlib.md5()
    with open(filepath, "rb") as f:
        h.update(f.read(65536))
    return h.hexdigest()


def _extract_timestamp(filepath: str) -> str:
    """Try to extract timestamp from replay filename, fall back to mtime."""
    fname = Path(filepath).stem
    # Pattern: "MP Replay v101.103.31214.0 @2026.02.09 130249 (1)"
    try:
        if "@" in fname:
            ts_part = fname.split("@")[1].strip()
            # Remove trailing " (1)" etc
            ts_part = ts_part.split("(")[0].strip()
            dt = datetime.strptime(ts_part, "%Y.%m.%d %H%M%S")
            return dt.isoformat()
    except (ValueError, IndexError):
        pass
    
    # Fallback to file modification time
    mtime = os.path.getmtime(filepath)
    return datetime.fromtimestamp(mtime).isoformat()
