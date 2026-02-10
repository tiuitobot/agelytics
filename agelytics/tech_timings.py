"""Key technology research timing extraction and categorization."""

# Key technologies to track, organized by category
KEY_TECHS = {
    "Economy": {
        "Loom",
        "Double-Bit Axe",
        "Bow Saw",
        "Two-Man Saw",
        "Horse Collar",
        "Heavy Plow",
        "Crop Rotation",
        "Wheelbarrow",
        "Hand Cart",
        "Gold Mining",
        "Gold Shaft Mining",
        "Stone Mining",
        "Stone Shaft Mining",
    },
    "Military": {
        "Man-at-Arms",
        "Long Swordsman",
        "Two-Handed Swordsman",
        "Champion",
        "Fletching",
        "Bodkin Arrow",
        "Bracer",
        "Ballistics",
        "Husbandry",
        "Squires",
        "Thumb Ring",
        "Parthian Tactics",
        "Conscription",
        "Bloodlines",
        "Blast Furnace",
    },
    "Blacksmith": {
        "Forging",
        "Iron Casting",
        "Blast Furnace",
        "Scale Mail Armor",
        "Chain Mail Armor",
        "Plate Mail Armor",
        "Scale Barding Armor",
        "Chain Barding Armor",
        "Plate Barding Armor",
        "Padded Archer Armor",
        "Leather Archer Armor",
        "Ring Archer Armor",
    },
    "University": {
        "Masonry",
        "Architecture",
        "Fortified Wall",
        "Ballistics",
        "Chemistry",
        "Siege Engineers",
        "Heated Shot",
        "Murder Holes",
        "Treadmill Crane",
        "Arrowslits",
    },
}


def extract_key_techs(match_data: dict, player_name: str) -> list[dict]:
    """Extract key technology timings for a specific player.
    
    Args:
        match_data: Full match data dict from parser
        player_name: Name of the player to extract techs for
    
    Returns:
        List of dicts with {tech, timestamp_secs, category}, sorted by timestamp
    """
    researches = match_data.get("researches", [])
    
    # Filter researches for this player
    player_researches = [
        r for r in researches if r["player"] == player_name
    ]
    
    # Extract key techs with category
    key_tech_timings = []
    for research in player_researches:
        tech = research["tech"]
        timestamp = research["timestamp_secs"]
        
        # Find which category this tech belongs to
        category = None
        for cat_name, techs in KEY_TECHS.items():
            if tech in techs:
                category = cat_name
                break
        
        # Only include if it's a key tech
        if category:
            key_tech_timings.append({
                "tech": tech,
                "timestamp_secs": timestamp,
                "category": category,
            })
    
    # Sort by timestamp
    key_tech_timings.sort(key=lambda x: x["timestamp_secs"])
    
    return key_tech_timings


def format_timing(seconds: float) -> str:
    """Format timestamp as MM:SS."""
    minutes = int(seconds) // 60
    secs = int(seconds) % 60
    return f"{minutes:02d}:{secs:02d}"


def get_tech_benchmark(tech: str) -> dict:
    """Get benchmark timing for a technology.
    
    Returns dict with {good, average, poor} timings in seconds, or None if no benchmark.
    
    These are rough professional/high-level benchmarks for ranked 1v1.
    """
    benchmarks = {
        # Age-up related eco techs
        "Loom": {"good": 30, "average": 60, "poor": 120},
        "Double-Bit Axe": {"good": 480, "average": 600, "poor": 720},
        "Horse Collar": {"good": 540, "average": 660, "poor": 780},
        "Wheelbarrow": {"good": 600, "average": 720, "poor": 900},
        "Bow Saw": {"good": 900, "average": 1080, "poor": 1260},
        "Heavy Plow": {"good": 960, "average": 1140, "poor": 1320},
        "Hand Cart": {"good": 1200, "average": 1380, "poor": 1560},
        
        # Military upgrades
        "Man-at-Arms": {"good": 720, "average": 840, "poor": 960},
        "Fletching": {"good": 480, "average": 600, "poor": 720},
        "Bodkin Arrow": {"good": 900, "average": 1080, "poor": 1260},
        "Ballistics": {"good": 1020, "average": 1200, "poor": 1380},
        
        # Blacksmith
        "Forging": {"good": 600, "average": 720, "poor": 900},
        "Iron Casting": {"good": 900, "average": 1080, "poor": 1260},
        "Scale Mail Armor": {"good": 720, "average": 900, "poor": 1080},
    }
    
    return benchmarks.get(tech)


def assess_timing(tech: str, timestamp_secs: float) -> str:
    """Assess if a tech timing is good/average/poor compared to benchmark.
    
    Returns: "Good" | "Average" | "Poor" | "Unknown"
    """
    benchmark = get_tech_benchmark(tech)
    if not benchmark:
        return "Unknown"
    
    if timestamp_secs <= benchmark["good"]:
        return "Good"
    elif timestamp_secs <= benchmark["average"]:
        return "Average"
    else:
        return "Poor"
