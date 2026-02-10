"""
Production building simulation to track when military units actually complete,
accounting for queue times and production delays.
"""

from collections import defaultdict
from typing import Optional


# Standard unit production times (in seconds)
UNIT_TRAIN_TIMES = {
    # Archery Range
    "Archer": 35,
    "Skirmisher": 22,
    "Cavalry Archer": 34,
    "Hand Cannoneer": 34,
    
    # Barracks
    "Militia": 21,
    "Man-at-Arms": 21,
    "Long Swordsman": 21,
    "Two-Handed Swordsman": 21,
    "Champion": 21,
    "Spearman": 22,
    "Pikeman": 22,
    "Halberdier": 22,
    "Eagle Scout": 60,
    "Eagle Warrior": 60,
    "Elite Eagle Warrior": 60,
    
    # Stable
    "Scout Cavalry": 30,
    "Light Cavalry": 30,
    "Hussar": 30,
    "Knight": 30,
    "Cavalier": 30,
    "Paladin": 30,
    "Camel Rider": 22,
    "Heavy Camel Rider": 22,
    "Battle Elephant": 31,
    
    # Siege Workshop
    "Battering Ram": 36,
    "Capped Ram": 36,
    "Siege Ram": 36,
    "Mangonel": 46,
    "Onager": 46,
    "Siege Onager": 46,
    "Scorpion": 30,
    "Heavy Scorpion": 30,
    "Bombard Cannon": 56,
    
    # Castle
    "Trebuchet": 50,
    "Petard": 25,
    
    # Other
    "Villager": 25,
    "Trade Cart": 51,
    "Trade Cog": 36,
    "Fishing Ship": 40,
    "Transport Ship": 45,
}


def simulate_production(match_data: dict, player_name: str) -> list[dict]:
    """
    Simulate production queues for a player's military buildings.
    
    Returns list of dicts with:
    - unit: unit type
    - queued_at: timestamp when unit was queued (seconds)
    - completed_at: timestamp when unit finished training (seconds)
    - building_id: building object ID
    - building_type: building type (Archery Range, Stable, etc.)
    """
    
    # Extract queue events from match inputs
    inputs = match_data.get("_raw_inputs")
    if not inputs:
        # Try to get from match.inputs if available
        try:
            from mgz.summary import Summary
            # This would require re-parsing, which we can't do here
            # Return empty list if raw inputs not available
            return []
        except:
            return []
    
    # Group queue events by building
    building_queues = defaultdict(list)
    
    for inp in inputs:
        try:
            # Check if this is a queue event from our player
            if inp.type != "Queue":
                continue
            
            pname = inp.player.name if hasattr(inp.player, "name") else None
            if pname != player_name:
                continue
            
            payload = inp.payload if hasattr(inp, "payload") else {}
            if not payload:
                continue
            
            unit = payload.get("unit")
            amount = payload.get("amount", 1)
            building_id = payload.get("building_id")  # May not always be available
            object_ids = payload.get("object_ids", [])
            
            if not unit or not UNIT_TRAIN_TIMES.get(unit):
                continue
            
            # Use building_id or first object_id
            bid = building_id or (object_ids[0] if object_ids else None)
            if not bid:
                continue
            
            timestamp = inp.timestamp.total_seconds() if hasattr(inp.timestamp, "total_seconds") else 0
            
            # Determine building type from unit
            building_type = _get_building_type(unit)
            
            # Add to queue for this building
            for _ in range(amount):
                building_queues[bid].append({
                    "unit": unit,
                    "queued_at": timestamp,
                    "building_type": building_type,
                })
        
        except Exception:
            continue
    
    # Simulate production for each building
    all_productions = []
    
    for building_id, queue in building_queues.items():
        # Sort by queue time
        queue.sort(key=lambda x: x["queued_at"])
        
        # Simulate production
        current_time = 0.0
        
        for item in queue:
            unit = item["unit"]
            queued_at = item["queued_at"]
            building_type = item["building_type"]
            train_time = UNIT_TRAIN_TIMES.get(unit, 30)
            
            # If queued before current production finishes, it waits
            start_time = max(queued_at, current_time)
            completed_at = start_time + train_time
            
            all_productions.append({
                "unit": unit,
                "queued_at": queued_at,
                "completed_at": completed_at,
                "building_id": building_id,
                "building_type": building_type,
            })
            
            current_time = completed_at
    
    # Sort by completion time
    all_productions.sort(key=lambda x: x["completed_at"])
    
    return all_productions


def _get_building_type(unit: str) -> Optional[str]:
    """Determine which building produces a given unit."""
    
    archery_units = {"Archer", "Skirmisher", "Cavalry Archer", "Hand Cannoneer"}
    barracks_units = {
        "Militia", "Man-at-Arms", "Long Swordsman", "Two-Handed Swordsman", "Champion",
        "Spearman", "Pikeman", "Halberdier", "Eagle Scout", "Eagle Warrior", "Elite Eagle Warrior"
    }
    stable_units = {
        "Scout Cavalry", "Light Cavalry", "Hussar", "Knight", "Cavalier", "Paladin",
        "Camel Rider", "Heavy Camel Rider", "Battle Elephant"
    }
    siege_units = {
        "Battering Ram", "Capped Ram", "Siege Ram", "Mangonel", "Onager", "Siege Onager",
        "Scorpion", "Heavy Scorpion", "Bombard Cannon"
    }
    
    if unit in archery_units:
        return "Archery Range"
    elif unit in barracks_units:
        return "Barracks"
    elif unit in stable_units:
        return "Stable"
    elif unit in siege_units:
        return "Siege Workshop"
    elif unit == "Trebuchet" or unit == "Petard":
        return "Castle"
    elif unit == "Villager":
        return "Town Center"
    
    return None


def production_summary(match_data: dict) -> dict:
    """
    Generate production simulation summary for all players.
    
    Returns dict mapping player names to their production timelines.
    """
    players = match_data.get("players", [])
    productions = {}
    
    for player in players:
        player_name = player["name"]
        production = simulate_production(match_data, player_name)
        productions[player_name] = production
    
    return productions
