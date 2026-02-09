"""AoE2 DE static data mappings."""

# Civilization ID → Name (DE, patch 101.103)
CIVILIZATIONS = {
    0: "Gaia",
    1: "Britons", 2: "Franks", 3: "Goths", 4: "Teutons",
    5: "Japanese", 6: "Chinese", 7: "Byzantines", 8: "Persians",
    9: "Saracens", 10: "Turks", 11: "Vikings", 12: "Mongols",
    13: "Celts", 14: "Spanish", 15: "Aztecs", 16: "Mayans",
    17: "Huns", 18: "Koreans", 19: "Italians", 20: "Indians",
    21: "Incas", 22: "Magyars", 23: "Slavs", 24: "Portuguese",
    25: "Ethiopians", 26: "Malians", 27: "Berbers", 28: "Khmer",
    29: "Malay", 30: "Burmese", 31: "Vietnamese", 32: "Bulgarians",
    33: "Tatars", 34: "Cumans", 35: "Lithuanians", 36: "Burgundians",
    37: "Sicilians", 38: "Poles", 39: "Bohemians", 40: "Dravidians",
    41: "Bengalis", 42: "Gurjaras", 43: "Romans", 44: "Armenians",
    45: "Georgians",
}

# Map type ID → Name (common ones)
MAP_TYPES = {
    9: "Arabia", 10: "Archipelago", 11: "Baltic", 12: "Black Forest",
    13: "Coastal", 14: "Continental", 15: "Crater Lake", 16: "Fortress",
    17: "Gold Rush", 18: "Highland", 19: "Islands", 20: "Mediterranean",
    21: "Migration", 22: "Rivers", 23: "Team Islands", 24: "Full Random",
    25: "Scandinavia", 26: "Mongolia", 27: "Yucatan", 28: "Salt Marsh",
    29: "Arena", 31: "Oasis", 32: "Ghost Lake", 33: "Nomad",
    49: "Acropolis", 50: "Budapest", 51: "Cenotes", 52: "City of Lakes",
    53: "Golden Pit", 55: "Hideout", 56: "Hill Fort", 57: "Lombardia",
    58: "Megarandom", 59: "Steppe", 60: "Valley", 62: "MegaRandom",
    67: "Runestones", 71: "African Clearing", 72: "Amazon Tunnel",
    74: "Coastal Forest", 75: "African Clearing", 77: "Kilimanjaro",
    87: "Socotra", 139: "Four Lakes", 140: "Golden Swamp",
    142: "Land Nomad", 143: "Nile Delta", 147: "Atacama",
    148: "Ravines", 149: "Volcanic Island",
    # DE-specific maps
    166: "Wade", 167: "Canyon Lake",
}


def civ_name(civ_id: int) -> str:
    """Get civilization name from ID."""
    return CIVILIZATIONS.get(civ_id, f"Unknown ({civ_id})")


def map_name(map_id) -> str:
    """Get map name from ID or return string as-is."""
    if isinstance(map_id, int):
        return MAP_TYPES.get(map_id, f"Map {map_id}")
    if isinstance(map_id, str):
        return map_id
    return str(map_id) if map_id else "Unknown"
