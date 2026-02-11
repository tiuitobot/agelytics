"""Replay parser for AoE2 .aoe2record files (ZIP format from MS servers)."""

import io
import os
import zipfile
from pathlib import Path
from typing import Optional

from mgz.summary import Summary


def parse_replay(replay_path: str) -> Optional[dict]:
    """Parse a single replay file (ZIP format from MS servers).
    
    Args:
        replay_path: Path to the .aoe2record file (actually a ZIP)
        
    Returns:
        Dict with replay data:
        - match_id: int
        - map_name: str
        - duration_secs: int
        - game_type: str (e.g. "1v1", "Team Game")
        - completed: bool
        - players: list of {name, civ, team, winner, user_id, rating}
        - age_up_times: {feudal, castle, imperial} per player (if available)
        
        Returns None if parse fails.
    """
    try:
        # Extract match_id from filename: {matchId}_{profileId}.aoe2record
        match_id = int(Path(replay_path).stem.split('_')[0])
        
        # Open ZIP and extract inner replay file
        with zipfile.ZipFile(replay_path) as z:
            inner_name = z.namelist()[0]  # Should be AgeIIDE_Replay_{matchId}.aoe2record
            replay_data = z.read(inner_name)
        
        # Parse with mgz
        summary = Summary(io.BytesIO(replay_data))
        
        # Extract map info
        map_data = summary.get_map()
        map_name = map_data.get("name", "Unknown")
        
        # Extract duration (convert from ms to seconds)
        duration_ms = summary.get_duration()
        duration_secs = int(duration_ms / 1000) if duration_ms else 0
        
        # Extract settings
        settings = summary.get_settings()
        game_type = settings.get("diplomacy_type", "Unknown")
        completed = summary.get_completed()
        
        # Extract players
        players_data = summary.get_players()
        teams_data = summary.get_teams()  # [[player_numbers_team1], [player_numbers_team2], ...]
        
        # Build player-to-team mapping
        player_to_team = {}
        for team_idx, team_players in enumerate(teams_data, 1):
            for player_num in team_players:
                player_to_team[player_num] = team_idx
        
        # Parse players
        players = []
        age_up_times = {}
        
        for player in players_data:
            player_num = player["number"]
            user_id = player.get("user_id")
            
            player_info = {
                "name": player["name"],
                "civ": player["civilization"],
                "team": player_to_team.get(player_num, 0),
                "winner": player.get("winner", False),
                "user_id": user_id,
                "rating": player.get("rate_snapshot"),
            }
            players.append(player_info)
            
            # Extract age-up times if available
            tech = player.get("achievements", {}).get("technology", {})
            feudal = tech.get("feudal_time")
            castle = tech.get("castle_time")
            imperial = tech.get("imperial_time")
            
            if user_id and (feudal is not None or castle is not None or imperial is not None):
                age_up_times[user_id] = {
                    "feudal": feudal,
                    "castle": castle,
                    "imperial": imperial,
                }
        
        return {
            "match_id": match_id,
            "map_name": map_name,
            "duration_secs": duration_secs,
            "game_type": game_type,
            "completed": completed,
            "players": players,
            "age_up_times": age_up_times,
        }
        
    except Exception as e:
        print(f"⚠️  Failed to parse {replay_path}: {e}")
        return None


def parse_opponent_replays(replay_dir: str, opponent_profile_id: int) -> list[dict]:
    """Parse all replays for an opponent in a directory.
    
    Files are named {matchId}_{profileId}.aoe2record
    Filters to only files matching opponent_profile_id.
    
    Args:
        replay_dir: Directory containing replay files
        opponent_profile_id: Profile ID to filter for
        
    Returns:
        List of parsed replay dicts, sorted by match_id (newest first).
    """
    replay_dir = Path(replay_dir)
    pattern = f"*_{opponent_profile_id}.aoe2record"
    
    replay_files = sorted(replay_dir.glob(pattern))
    print(f"Found {len(replay_files)} replay(s) for profile {opponent_profile_id}")
    
    parsed = []
    for replay_file in replay_files:
        result = parse_replay(str(replay_file))
        if result:
            parsed.append(result)
    
    print(f"Successfully parsed {len(parsed)}/{len(replay_files)} replays")
    
    # Sort by match_id descending (newest first)
    parsed.sort(key=lambda x: x["match_id"], reverse=True)
    
    return parsed
