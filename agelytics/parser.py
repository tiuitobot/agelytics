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
from .metrics import enrich_match_for_metrics, compute_all_metrics
from .opening import opening_summary
from .production import production_summary


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
        
        # Enriquecer dados para métricas determinísticas
        enriched = enrich_match_for_metrics(s)
        
        # Montar dict base da partida
        match_data = {
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
            **enriched,  # Merge enriched data (_farm_build_timestamps, etc.)
        }
        
        # Calcular métricas por jogador e armazenar em dicts separados
        metrics_by_player = {}
        for p in players:
            player_name = p["name"]
            metrics = compute_all_metrics(match_data, player_name)
            metrics_by_player[player_name] = metrics
        
        match_data["metrics"] = metrics_by_player
        
        # Detect opening strategies
        try:
            openings = opening_summary(match_data)
            match_data["openings"] = openings
        except Exception:
            match_data["openings"] = {}
        
        # Store raw inputs for TC idle calculation and production simulation
        try:
            if hasattr(s.match, "inputs"):
                match_data["_raw_inputs"] = s.match.inputs
        except Exception:
            pass
        
        # Calculate TC idle by era
        try:
            tc_idle_by_age = _calculate_tc_idle_by_age(match_data)
            match_data["tc_idle_by_age"] = tc_idle_by_age
        except Exception:
            match_data["tc_idle_by_age"] = {}
        
        return match_data

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
        "building_timestamps": {},  # NEW: {player: [{building, timestamp_secs}]}
        "resign_player": None,
        "tc_idle": {},
        "estimated_idle_villager_time": {},
        "vill_queue_timestamps": {},
        "production_buildings_by_age": {},  # NEW: {player: {age: {building: count}}}
        "housed_count": {},  # NEW: {player: count}
        "wall_tiles_by_age": {},  # NEW: {player: {age: count}}
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
        
        # Extract inputs (units, researches, buildings, resigns, walls)
        if hasattr(match, "inputs") and match.inputs:
            unit_counts = defaultdict(lambda: defaultdict(int))
            building_counts = defaultdict(lambda: defaultdict(int))
            building_timestamps = defaultdict(list)  # NEW: track building timestamps
            wall_events = defaultdict(list)  # NEW: track wall placements [{timestamp_secs, tiles}]
            
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
                            # NEW: Store timestamp for each building
                            building_timestamps[player_name].append({
                                "building": building,
                                "timestamp_secs": timestamp_secs,
                            })
                    
                    elif inp.type == "Wall" and hasattr(inp, "payload") and inp.payload:
                        # Walling - count tiles via Chebyshev distance
                        # Walling tile count via Chebyshev distance inspired by AgeAlyser (github.com/byrnesy924/AgeAlyser_2)
                        building_type = inp.payload.get("building")
                        if building_type in ("Palisade Wall", "Stone Wall"):
                            # Get start and end positions
                            start_x = None
                            start_y = None
                            if hasattr(inp, "position") and inp.position:
                                start_x = getattr(inp.position, "x", None)
                                start_y = getattr(inp.position, "y", None)
                            
                            end_x = inp.payload.get("x_end")
                            end_y = inp.payload.get("y_end")
                            
                            if start_x is not None and start_y is not None and end_x is not None and end_y is not None:
                                # Chebyshev distance = max(|x2-x1|, |y2-y1|)
                                tiles = max(abs(end_x - start_x), abs(end_y - start_y)) + 1
                                wall_events[player_name].append({
                                    "timestamp_secs": timestamp_secs,
                                    "tiles": tiles,
                                })
                    
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
            result["building_timestamps"] = dict(building_timestamps)
            
            # Calculate estimated idle villager time per player (PROXY)
            # Soma de gaps > 30s entre comandos econômicos (Move, Build, Queue Villager, etc.)
            # PROXY: replay só tem inputs, não estado real dos aldeões
            ECO_COMMAND_TYPES = {"Move", "Build", "Queue", "Waypoint", "Gather", "Repair"}
            eco_cmd_timestamps = defaultdict(list)
            vill_queue_timestamps = defaultdict(list)  # timestamps de Queue Villager por player
            for inp in match.inputs:
                try:
                    pname = inp.player.name if hasattr(inp.player, "name") else None
                    if not pname:
                        continue
                    ts = inp.timestamp.total_seconds() if hasattr(inp.timestamp, "total_seconds") else 0
                    
                    # Eco commands: Build, Queue Villager, Move (could be vill move), Gather, Repair
                    is_eco = False
                    if inp.type in ECO_COMMAND_TYPES:
                        if inp.type == "Queue" and hasattr(inp, "payload") and inp.payload:
                            if inp.payload.get("unit") == "Villager":
                                is_eco = True
                                vill_queue_timestamps[pname].append(ts)
                        elif inp.type == "Build":
                            is_eco = True
                        elif inp.type in ("Move", "Gather", "Repair", "Waypoint"):
                            is_eco = True
                    
                    if is_eco:
                        eco_cmd_timestamps[pname].append(ts)
                except Exception:
                    continue
            
            ECO_IDLE_THRESHOLD = 30  # seconds
            for pname, times in eco_cmd_timestamps.items():
                times.sort()
                total_idle = 0.0
                for i in range(1, len(times)):
                    gap = times[i] - times[i - 1]
                    if gap > ECO_IDLE_THRESHOLD:
                        total_idle += gap - ECO_IDLE_THRESHOLD
                result["estimated_idle_villager_time"][pname] = round(total_idle, 1)
            
            # Villager queue timestamps por player (para Villager Production Rate por Age)
            result["vill_queue_timestamps"] = dict(vill_queue_timestamps)
            
            # NEW: Calculate production buildings by age
            PRODUCTION_BUILDINGS = {"Archery Range", "Barracks", "Stable", "Siege Workshop"}
            production_by_age = {}
            
            for player_name, buildings_list in building_timestamps.items():
                production_by_age[player_name] = {"Dark": {}, "Feudal": {}, "Castle": {}, "Imperial": {}}
                player_age_times = {}
                for age_up in result["age_ups"]:
                    if age_up["player"] == player_name:
                        player_age_times[age_up["age"]] = age_up["timestamp_secs"]
                feudal_time = player_age_times.get("Feudal Age")
                castle_time = player_age_times.get("Castle Age")
                imperial_time = player_age_times.get("Imperial Age")
                for building_entry in buildings_list:
                    building = building_entry["building"]
                    timestamp = building_entry["timestamp_secs"]
                    if building not in PRODUCTION_BUILDINGS:
                        continue
                    age = "Dark"
                    if feudal_time and timestamp >= feudal_time:
                        age = "Feudal"
                    if castle_time and timestamp >= castle_time:
                        age = "Castle"
                    if imperial_time and timestamp >= imperial_time:
                        age = "Imperial"
                    if building not in production_by_age[player_name][age]:
                        production_by_age[player_name][age][building] = 0
                    production_by_age[player_name][age][building] += 1
            result["production_buildings_by_age"] = production_by_age
            
            # NEW: Calculate housed count
            housed_counts = {}
            HOUSE_BURST_THRESHOLD = 10  # seconds
            for player_name, buildings_list in building_timestamps.items():
                house_builds = sorted([b["timestamp_secs"] for b in buildings_list if b["building"] == "House"])
                housed = 0
                i = 0
                while i < len(house_builds):
                    burst_count = 1
                    j = i + 1
                    while j < len(house_builds) and house_builds[j] - house_builds[j-1] < HOUSE_BURST_THRESHOLD:
                        burst_count += 1
                        j += 1
                    if burst_count >= 2:
                        housed += 1
                        i = j
                    else:
                        i += 1
                housed_counts[player_name] = housed
            result["housed_count"] = housed_counts
            
            # NEW: Calculate wall tiles by age
            wall_tiles_by_age = {}
            for player_name, wall_list in wall_events.items():
                wall_tiles_by_age[player_name] = {"Dark": 0, "Feudal": 0, "Castle": 0, "Imperial": 0}
                
                # Get player's age-up times
                player_age_times = {}
                for age_up in result["age_ups"]:
                    if age_up["player"] == player_name:
                        player_age_times[age_up["age"]] = age_up["timestamp_secs"]
                
                feudal_time = player_age_times.get("Feudal Age")
                castle_time = player_age_times.get("Castle Age")
                imperial_time = player_age_times.get("Imperial Age")
                
                # Classify each wall event by age
                for wall_event in wall_list:
                    timestamp = wall_event["timestamp_secs"]
                    tiles = wall_event["tiles"]
                    
                    age = "Dark"
                    if feudal_time and timestamp >= feudal_time:
                        age = "Feudal"
                    if castle_time and timestamp >= castle_time:
                        age = "Castle"
                    if imperial_time and timestamp >= imperial_time:
                        age = "Imperial"
                    
                    wall_tiles_by_age[player_name][age] += tiles
            
            result["wall_tiles_by_age"] = wall_tiles_by_age
            
            # Calculate TC idle time per player (v3: queue simulation + research-aware + multi-TC)
            # Queue simulation concept inspired by AgeAlyser (https://github.com/byrnesy924/AgeAlyser_2)
            # by byrnesy924, MIT License. Simplified without pandas/Factory pattern.
            TC_RESEARCH_TIMES = {
                "Loom": 25, "Feudal Age": 130, "Castle Age": 160,
                "Imperial Age": 190, "Wheelbarrow": 75, "Hand Cart": 55,
                "Town Watch": 25, "Town Patrol": 40,
            }
            VILL_TRAIN_TIME = 25
            
            # Collect all TC-related events per player
            vill_events_tc = defaultdict(list)
            tc_research_events = defaultdict(list)  # [(start, end)]
            tc_build_times = defaultdict(list)
            for inp in match.inputs:
                try:
                    pname = inp.player.name if hasattr(inp.player, "name") else None
                    if not pname:
                        continue
                    ts = inp.timestamp.total_seconds() if hasattr(inp.timestamp, "total_seconds") else 0
                    if inp.type == "Queue" and hasattr(inp, "payload") and inp.payload:
                        if inp.payload.get("unit") == "Villager":
                            vill_events_tc[pname].append(ts)
                    elif inp.type == "Research" and hasattr(inp, "payload") and inp.payload:
                        tech = inp.payload.get("technology", "")
                        if tech in TC_RESEARCH_TIMES:
                            tc_research_events[pname].append((ts, TC_RESEARCH_TIMES[tech]))
                    elif inp.type == "Build" and hasattr(inp, "payload") and inp.payload:
                        if inp.payload.get("building") == "Town Center":
                            tc_build_times[pname].append(ts)
                except Exception:
                    continue
            
            for pname, times in vill_events_tc.items():
                times.sort()
                
                # Build TC count timeline
                tc_timeline = [(0, 1)]
                for tc_ts in sorted(tc_build_times.get(pname, [])):
                    tc_timeline.append((tc_ts + 150, tc_timeline[-1][1] + 1))
                
                def _tc_count_at(ts):
                    n = 1
                    for tc_ts, tc_n in tc_timeline:
                        if ts >= tc_ts:
                            n = tc_n
                    return max(n, 1)
                
                # Build sorted list of all TC tasks: vill production + researches
                # Each task: (click_time, duration, type)
                tasks = [(t, VILL_TRAIN_TIME, "vill") for t in times]
                for r_ts, r_dur in tc_research_events.get(pname, []):
                    tasks.append((r_ts, r_dur, "research"))
                tasks.sort(key=lambda x: x[0])
                
                # Simulate TC queue: track when TC becomes free
                # With multi-TC, distribute across TCs (simplified: single queue, divide by TC count)
                tc_free_at = 0.0  # when the TC queue finishes
                total_idle = 0.0
                
                # TC idle breakdown by gap category
                micro_idle = {"count": 0, "total": 0.0}   # 5-15s
                macro_idle = {"count": 0, "total": 0.0}   # 15-60s
                afk_idle = {"count": 0, "total": 0.0}     # 60s+
                
                for click_time, duration, task_type in tasks:
                    num_tcs = _tc_count_at(click_time)
                    
                    if click_time >= tc_free_at:
                        # TC was idle between tc_free_at and click_time
                        idle_gap = click_time - tc_free_at
                        if idle_gap > 5:
                            total_idle += idle_gap
                            # Categorize gap
                            if idle_gap < 15:
                                micro_idle["count"] += 1
                                micro_idle["total"] += idle_gap
                            elif idle_gap < 60:
                                macro_idle["count"] += 1
                                macro_idle["total"] += idle_gap
                            else:
                                afk_idle["count"] += 1
                                afk_idle["total"] += idle_gap
                        # Task starts now
                        tc_free_at = click_time + (duration / num_tcs)
                    else:
                        # TC still busy — task queues after current work
                        tc_free_at += (duration / num_tcs)
                
                result["tc_idle"][pname] = round(total_idle, 1)
                result.setdefault("tc_idle_breakdown", {})[pname] = {
                    "micro": {"count": micro_idle["count"], "total": round(micro_idle["total"], 1)},
                    "macro": {"count": macro_idle["count"], "total": round(macro_idle["total"], 1)},
                    "afk": {"count": afk_idle["count"], "total": round(afk_idle["total"], 1)},
                }
                
                # ──────────────────────────────────────────────────────────
                # LOWER BOUND: Heuristic housed time (gap-based)
                # ──────────────────────────────────────────────────────────
                house_times_p = sorted([
                    b["timestamp_secs"] for b in building_timestamps.get(pname, [])
                    if b["building"] == "House"
                ])
                
                housed_time_lower = 0.0
                vill_only = sorted([t for t, d, tt in tasks if tt == "vill"])
                for i in range(1, len(vill_only)):
                    gap = vill_only[i] - vill_only[i - 1]
                    if gap > VILL_TRAIN_TIME + 5:  # Gap longer than 1 vill train = suspicious
                        gap_start = vill_only[i - 1]
                        gap_end = vill_only[i]
                        # Count houses built during or shortly after this gap
                        houses_in_gap = sum(
                            1 for ht in house_times_p
                            if gap_start - 5 <= ht <= gap_end + 10
                        )
                        if houses_in_gap >= 2:
                            # Subtract normal vill train time — the excess is housed time
                            excess = gap - VILL_TRAIN_TIME
                            housed_time_lower += max(0, excess)
                
                result.setdefault("housed_time_lower", {})[pname] = round(housed_time_lower, 1)
                result.setdefault("tc_idle_effective_lower", {})[pname] = round(total_idle + housed_time_lower, 1)
                
                # Lower bound by era
                player_ages = []
                for au in result.get("age_ups", []):
                    if au.get("player") == pname:
                        player_ages.append((au["age"], au["timestamp_secs"]))
                
                era_boundaries = {"Dark": 0.0, "Feudal": None, "Castle": None, "Imperial": None}
                for age_name, ts in player_ages:
                    if "Feudal" in age_name: era_boundaries["Feudal"] = ts
                    elif "Castle" in age_name: era_boundaries["Castle"] = ts
                    elif "Imperial" in age_name: era_boundaries["Imperial"] = ts
                
                def _get_era(t):
                    if era_boundaries["Imperial"] and t >= era_boundaries["Imperial"]: return "Imperial"
                    if era_boundaries["Castle"] and t >= era_boundaries["Castle"]: return "Castle"
                    if era_boundaries["Feudal"] and t >= era_boundaries["Feudal"]: return "Feudal"
                    return "Dark"
                
                housed_lower_by_age = {"Dark": 0.0, "Feudal": 0.0, "Castle": 0.0, "Imperial": 0.0}
                for i in range(1, len(vill_only)):
                    gap = vill_only[i] - vill_only[i - 1]
                    if gap > VILL_TRAIN_TIME + 5:
                        gap_start = vill_only[i - 1]
                        gap_end = vill_only[i]
                        houses_in_gap = sum(1 for ht in house_times_p if gap_start - 5 <= ht <= gap_end + 10)
                        if houses_in_gap >= 2:
                            excess = max(0, gap - VILL_TRAIN_TIME)
                            era = _get_era((gap_start + gap_end) / 2)
                            housed_lower_by_age[era] += excess
                
                housed_lower_by_age = {k: round(v, 1) for k, v in housed_lower_by_age.items()}
                result.setdefault("housed_time_lower_by_age", {})[pname] = housed_lower_by_age
                
                # ──────────────────────────────────────────────────────────
                # UPPER BOUND: Pop timeline (deterministic)
                # ──────────────────────────────────────────────────────────
                UNIT_TRAIN_TIMES = {
                    "Villager": 25, "Militia": 21, "Man-at-Arms": 21, "Long Swordsman": 21,
                    "Two-Handed Swordsman": 21, "Champion": 21, "Archer": 35, "Crossbowman": 35,
                    "Arbalester": 35, "Skirmisher": 22, "Elite Skirmisher": 22, "Scout Cavalry": 30,
                    "Light Cavalry": 30, "Hussar": 30, "Spearman": 22, "Pikeman": 22, "Halberdier": 22,
                    "Knight": 30, "Cavalier": 30, "Paladin": 30, "Camel Rider": 22, "Heavy Camel Rider": 22,
                    "Battering Ram": 36, "Capped Ram": 36, "Siege Ram": 36, "Mangonel": 46,
                    "Onager": 46, "Siege Onager": 46, "Scorpion": 30, "Heavy Scorpion": 30,
                    "Bombard Cannon": 56, "Trebuchet": 50,
                }
                HOUSE_BUILD_TIME = 25
                TC_BUILD_TIME = 150
                
                # 1. Build capacity timeline
                capacity_events = [(0, 5)]  # Start with 5 (initial TC)
                
                # House completions
                for ht in house_times_p:
                    capacity_events.append((ht + HOUSE_BUILD_TIME, 5))
                
                # TC completions
                for tc_ts in sorted(tc_build_times.get(pname, [])):
                    capacity_events.append((tc_ts + TC_BUILD_TIME, 5))
                
                capacity_events.sort()
                
                # Build capacity(t) function
                def capacity_at(t):
                    cap = 5
                    for event_t, delta in capacity_events:
                        if event_t <= t:
                            cap += delta
                    return cap
                
                # 2. Build pop_produced timeline
                pop_produced_events = [(0, 4)]  # Start: scout(1) + vills(3) = 4
                
                # Track which object_ids are villagers (from Queue commands)
                villager_object_ids = set()
                
                # Collect all Queue commands to build pop timeline
                for inp in match.inputs:
                    try:
                        p = inp.player.name if hasattr(inp.player, "name") else None
                        if p != pname:
                            continue
                        ts = inp.timestamp.total_seconds() if hasattr(inp.timestamp, "total_seconds") else 0
                        
                        if inp.type == "Queue" and hasattr(inp, "payload") and inp.payload:
                            unit = inp.payload.get("unit")
                            if not unit:
                                continue
                            
                            train_time = UNIT_TRAIN_TIMES.get(unit, 30)
                            amount = inp.payload.get("amount", 1)
                            
                            # Track villager object_ids
                            if unit == "Villager":
                                obj_id = inp.payload.get("object_id")
                                if obj_id:
                                    villager_object_ids.add(obj_id)
                            
                            # Add completion events (stagger if amount > 1)
                            for i in range(amount):
                                completion_time = ts + train_time + (i * train_time)
                                pop_produced_events.append((completion_time, 1))
                    except Exception:
                        continue
                
                pop_produced_events.sort()
                
                # Build pop_produced(t) function
                def pop_produced_at(t):
                    pop = 4
                    for event_t, delta in pop_produced_events:
                        if event_t <= t:
                            pop += delta
                    return pop
                
                # 3. Build deaths timeline
                death_events = []
                
                # Collect Delete commands (exact deaths)
                for inp in match.inputs:
                    try:
                        p = inp.player.name if hasattr(inp.player, "name") else None
                        if p != pname:
                            continue
                        ts = inp.timestamp.total_seconds() if hasattr(inp.timestamp, "total_seconds") else 0
                        
                        if inp.type == "Delete":
                            death_events.append((ts, 1))
                    except Exception:
                        continue
                
                # Military death estimation (simplified)
                # Track last_action_time for non-villager objects
                object_last_action = {}
                
                # Get game duration
                game_end_time = 0
                try:
                    duration_ms = summary.get_duration() or 0
                    game_end_time = duration_ms / 1000.0 if duration_ms else 0
                except Exception:
                    # Fallback: find max timestamp from inputs
                    try:
                        all_timestamps = [inp.timestamp.total_seconds() for inp in match.inputs 
                                         if hasattr(inp, 'timestamp')]
                        game_end_time = max(all_timestamps) if all_timestamps else 0
                    except Exception:
                        game_end_time = 0
                
                for inp in match.inputs:
                    try:
                        p = inp.player.name if hasattr(inp.player, "name") else None
                        if p != pname:
                            continue
                        ts = inp.timestamp.total_seconds() if hasattr(inp.timestamp, "total_seconds") else 0
                        
                        # Track objects that receive action commands
                        obj_id = None
                        if hasattr(inp, "payload") and inp.payload:
                            obj_id = inp.payload.get("object_id")
                        
                        if obj_id and inp.type in ("Move", "Attack Move", "Target", "Stance"):
                            # Only track military (not villagers, not buildings)
                            if obj_id not in villager_object_ids:
                                object_last_action[obj_id] = ts
                    except Exception:
                        continue
                
                # Estimate military deaths: last_action_time >120s before game end
                for obj_id, last_ts in object_last_action.items():
                    if game_end_time - last_ts > 120:
                        death_events.append((last_ts + 60, 1))  # Grace period
                
                death_events.sort()
                
                # Build deaths(t) function
                def deaths_at(t):
                    d = 0
                    for event_t, delta in death_events:
                        if event_t <= t:
                            d += delta
                    return d
                
                # 4. Calculate housed periods (total + by era)
                # Sample timeline every second
                housed_seconds = 0.0
                housed_upper_by_age = {"Dark": 0.0, "Feudal": 0.0, "Castle": 0.0, "Imperial": 0.0}
                for t in range(0, int(game_end_time) + 1):
                    pop_alive = pop_produced_at(t) - deaths_at(t)
                    cap = capacity_at(t)
                    if pop_alive >= cap:
                        housed_seconds += 1.0
                        housed_upper_by_age[_get_era(t)] += 1.0
                
                housed_upper_by_age = {k: round(v, 1) for k, v in housed_upper_by_age.items()}
                result.setdefault("housed_time_upper", {})[pname] = round(housed_seconds, 1)
                result.setdefault("housed_time_upper_by_age", {})[pname] = housed_upper_by_age
                result.setdefault("tc_idle_effective_upper", {})[pname] = round(total_idle + housed_seconds, 1)
    
    except Exception:
        # If detailed extraction fails entirely, return empty data
        pass
    
    return result


def _calculate_tc_idle_by_age(match_data: dict) -> dict:
    """
    Break down TC idle time by age (Dark, Feudal, Castle, Imperial).
    
    Returns dict mapping player names to dicts with age breakdowns:
    {player_name: {"Dark": X, "Feudal": Y, "Castle": Z, "Imperial": W}}
    """
    result = {}
    
    # Get age-up times for each player
    age_ups = match_data.get("age_ups", [])
    players = match_data.get("players", [])
    duration = match_data.get("duration_secs", 0)
    
    # Build age timeline for each player
    player_ages = {}
    for player in players:
        pname = player["name"]
        player_ages[pname] = {
            "Dark": (0, None),
            "Feudal": (None, None),
            "Castle": (None, None),
            "Imperial": (None, None),
        }
    
    # Fill in age-up times
    for age_up in age_ups:
        pname = age_up["player"]
        age = age_up["age"]
        timestamp = age_up["timestamp_secs"]
        
        if pname not in player_ages:
            continue
        
        if age == "Feudal Age":
            player_ages[pname]["Dark"] = (0, timestamp)
            player_ages[pname]["Feudal"] = (timestamp, None)
        elif age == "Castle Age":
            feudal_start = player_ages[pname]["Feudal"][0]
            if feudal_start is not None:
                player_ages[pname]["Feudal"] = (feudal_start, timestamp)
            player_ages[pname]["Castle"] = (timestamp, None)
        elif age == "Imperial Age":
            castle_start = player_ages[pname]["Castle"][0]
            if castle_start is not None:
                player_ages[pname]["Castle"] = (castle_start, timestamp)
            player_ages[pname]["Imperial"] = (timestamp, duration)
    
    # Fill in any remaining None end times with game duration
    for pname in player_ages:
        for age in ["Dark", "Feudal", "Castle", "Imperial"]:
            start, end = player_ages[pname][age]
            if start is not None and end is None:
                player_ages[pname][age] = (start, duration)
    
    # Now calculate TC idle for each age (v3: queue simulation + research-aware + multi-TC)
    TC_RESEARCH_TIMES_BY_AGE = {
        "Loom": 25, "Feudal Age": 130, "Castle Age": 160,
        "Imperial Age": 190, "Wheelbarrow": 75, "Hand Cart": 55,
        "Town Watch": 25, "Town Patrol": 40,
    }
    VILL_TRAIN_TIME = 25
    
    try:
        raw_inputs = match_data.get("_raw_inputs")
        if not raw_inputs:
            for pname in [p["name"] for p in players]:
                result[pname] = {"Dark": 0.0, "Feudal": 0.0, "Castle": 0.0, "Imperial": 0.0}
            return result
        
        # Collect events
        vill_queues = defaultdict(list)
        tc_research_ev = defaultdict(list)
        tc_build_ev = defaultdict(list)
        for inp in raw_inputs:
            try:
                pname = inp.player.name if hasattr(inp.player, "name") else None
                if not pname:
                    continue
                ts = inp.timestamp.total_seconds() if hasattr(inp.timestamp, "total_seconds") else 0
                if inp.type == "Queue" and hasattr(inp, "payload") and inp.payload:
                    if inp.payload.get("unit") == "Villager":
                        vill_queues[pname].append(ts)
                elif inp.type == "Research" and hasattr(inp, "payload") and inp.payload:
                    tech = inp.payload.get("technology", "")
                    if tech in TC_RESEARCH_TIMES_BY_AGE:
                        tc_research_ev[pname].append((ts, TC_RESEARCH_TIMES_BY_AGE[tech]))
                elif inp.type == "Build" and hasattr(inp, "payload") and inp.payload:
                    if inp.payload.get("building") == "Town Center":
                        tc_build_ev[pname].append(ts)
            except Exception:
                continue
        
        for pname in [p["name"] for p in players]:
            times = sorted(vill_queues.get(pname, []))
            ages = player_ages.get(pname, {})
            
            # TC count timeline
            tc_timeline = [(0, 1)]
            for tc_ts in sorted(tc_build_ev.get(pname, [])):
                tc_timeline.append((tc_ts + 150, tc_timeline[-1][1] + 1))
            
            def _tc_count_at_age(ts):
                n = 1
                for tc_ts, tc_n in tc_timeline:
                    if ts >= tc_ts:
                        n = tc_n
                return max(n, 1)
            
            result[pname] = {"Dark": 0.0, "Feudal": 0.0, "Castle": 0.0, "Imperial": 0.0}
            
            # Build task list and simulate queue
            tasks = [(t, VILL_TRAIN_TIME, "vill") for t in times]
            for r_ts, r_dur in tc_research_ev.get(pname, []):
                tasks.append((r_ts, r_dur, "research"))
            tasks.sort(key=lambda x: x[0])
            
            tc_free_at = 0.0
            idle_gaps = []  # [(start, end)]
            
            for click_time, dur, task_type in tasks:
                num_tcs = _tc_count_at_age(click_time)
                if click_time >= tc_free_at:
                    idle_gap = click_time - tc_free_at
                    if idle_gap > 5:
                        idle_gaps.append((tc_free_at, click_time))
                    tc_free_at = click_time + (dur / num_tcs)
                else:
                    tc_free_at += (dur / num_tcs)
            
            # Distribute idle gaps across ages
            for gap_start, gap_end in idle_gaps:
                gap = gap_end - gap_start
                for age_name, (age_start, age_end) in ages.items():
                    if age_start is None or age_end is None:
                        continue
                    a_start = max(gap_start, age_start)
                    a_end = min(gap_end, age_end)
                    if a_start < a_end:
                        fraction = (a_end - a_start) / (gap_end - gap_start) if gap_end > gap_start else 0
                        result[pname][age_name] += gap * fraction
            
            for age_name in result[pname]:
                result[pname][age_name] = round(result[pname][age_name], 1)
    
    except Exception:
        for pname in [p["name"] for p in players]:
            result[pname] = {"Dark": 0.0, "Feudal": 0.0, "Castle": 0.0, "Imperial": 0.0}
    
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
