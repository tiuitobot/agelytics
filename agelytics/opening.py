# Opening detection logic inspired by AgeAlyser (https://github.com/byrnesy924/AgeAlyser_2)
# by byrnesy924, MIT License. Adapted without pandas/Factory pattern for Agelytics.

"""
Classify player opening strategies based on early game unit production,
building construction, and age-up timings.
"""

from typing import Optional


def detect_opening(match_data: dict, player_name: str) -> str:
    """
    Detect the opening strategy for a given player.
    
    Returns one of:
    - "Drush", "Pre-Mill Drush", "M@A" (Dark Age strategies)
    - "Scout Rush", "Straight Archers", "Archers+Skirms", "Scouts→Archers", "Full Feudal"
    - "Drush→FC", "Fast Castle", "Tower Rush"
    - "Unknown"
    """
    
    # Extract relevant data
    age_ups = match_data.get("age_ups", [])
    unit_production = match_data.get("unit_production", {}).get(player_name, {})
    researches = match_data.get("researches", [])
    buildings = match_data.get("buildings", {}).get(player_name, {})
    
    # Get player age-up times
    feudal_time = None
    castle_time = None
    for age_up in age_ups:
        if age_up["player"] == player_name:
            if age_up["age"] == "Feudal Age":
                feudal_time = age_up["timestamp_secs"]
            elif age_up["age"] == "Castle Age":
                castle_time = age_up["timestamp_secs"]
    
    # Check for Militia production in Dark Age
    militia_produced = unit_production.get("Militia", 0)
    man_at_arms_researched = any(
        r["player"] == player_name and r["tech"] == "Man-at-Arms" 
        for r in researches
    )
    
    # Dark Age analysis
    dark_age_strategy = None
    if militia_produced > 0:
        # Check if drush or pre-mill drush
        # Pre-Mill Drush: militia before first mill (farm)
        # Simple heuristic: if militia > 3, likely pre-mill drush
        if militia_produced >= 4:
            dark_age_strategy = "Pre-Mill Drush"
        else:
            dark_age_strategy = "Drush"
        
        # Check for M@A upgrade
        if man_at_arms_researched:
            dark_age_strategy = "M@A"
    
    # Feudal Age analysis
    feudal_strategy = None
    
    # Get first military building in Feudal
    # Assume buildings built after Feudal time are Feudal buildings
    archery_range_count = buildings.get("Archery Range", 0)
    stable_count = buildings.get("Stable", 0)
    barracks_count = buildings.get("Barracks", 0)
    
    # Units produced in Feudal (heuristic: count after feudal time)
    archer_count = unit_production.get("Archer", 0)
    skirmisher_count = unit_production.get("Skirmisher", 0)
    scout_count = unit_production.get("Scout Cavalry", 0)
    spearman_count = unit_production.get("Spearman", 0)
    
    # Determine Feudal strategy based on military buildings and units
    if stable_count > 0 and scout_count > 0:
        # Check if transitioned to archers later
        if archery_range_count > 0 and archer_count > scout_count:
            feudal_strategy = "Scouts→Archers"
        else:
            feudal_strategy = "Scout Rush"
    elif archery_range_count > 0:
        if skirmisher_count > 0 and archer_count > 0:
            feudal_strategy = "Archers+Skirms"
        elif archer_count > 0:
            feudal_strategy = "Straight Archers"
        else:
            feudal_strategy = "Full Feudal"
    elif barracks_count > 0 and spearman_count > 0:
        feudal_strategy = "Full Feudal"
    
    # Check for Fast Castle
    # Heuristic: feudal time > 650s (very late feudal) or castle time < feudal_time + 200s
    is_fast_castle = False
    if feudal_time and castle_time:
        feudal_castle_gap = castle_time - feudal_time
        if feudal_castle_gap < 200 or feudal_time > 650:
            is_fast_castle = True
    
    # Check for Tower Rush
    tower_count = buildings.get("Watch Tower", 0) + buildings.get("Guard Tower", 0)
    is_tower_rush = tower_count >= 2  # At least 2 towers is a tower rush
    
    # Combine strategies to determine opening
    if is_tower_rush:
        return "Tower Rush"
    
    if is_fast_castle:
        if dark_age_strategy == "Drush":
            return "Drush→FC"
        else:
            return "Fast Castle"
    
    # Combine dark age + feudal
    if dark_age_strategy and feudal_strategy:
        return f"{dark_age_strategy}→{feudal_strategy}"
    elif dark_age_strategy:
        return dark_age_strategy
    elif feudal_strategy:
        return feudal_strategy
    
    # If we have no clear strategy, return Unknown
    if feudal_time is None or (archery_range_count == 0 and stable_count == 0 and barracks_count == 0):
        return "Unknown"
    
    return "Unknown"


def opening_summary(match_data: dict) -> dict:
    """
    Generate opening strategy summary for all players.
    
    Returns dict mapping player names to their opening strategies.
    """
    players = match_data.get("players", [])
    openings = {}
    
    for player in players:
        player_name = player["name"]
        opening = detect_opening(match_data, player_name)
        openings[player_name] = opening
    
    return openings
