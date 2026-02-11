"""Civilization knowledge base — static data for AoE2 DE civs."""

from typing import Optional

from .data import CIVILIZATIONS

# All civs from the game (for dropdown completeness)
ALL_CIVS = sorted([name for cid, name in CIVILIZATIONS.items() if cid > 0])


# Detailed civ data for the most popular civs
CIV_DATA: dict[str, dict] = {
    "Britons": {
        "pros": ["Longest range archers in game", "Cheap TCs", "Strong eco bonus (shepherds)"],
        "cons": ["Weak cavalry", "No Hussars", "Predictable strategy"],
        "unique_units": ["Longbowman"],
        "bonuses": "TC cost -50% wood. Shepherds work 25% faster. Archery ranges work 20% faster in Castle Age.",
    },
    "Franks": {
        "pros": ["Strong Paladins", "Free farm upgrades", "Forager bonus"],
        "cons": ["No Bracer", "Weak archers", "No Camels"],
        "unique_units": ["Throwing Axeman"],
        "bonuses": "Farm upgrades free. Foragers +15%. Cavalry +20% HP. Castles -25% cost.",
    },
    "Mayans": {
        "pros": ["Strongest archer civ", "Extra villager start", "Cheap archers"],
        "cons": ["No cavalry at all", "No gunpowder", "Weak siege"],
        "unique_units": ["Plumed Archer"],
        "bonuses": "Start +1 villager, -50 food. Resources last 15% longer. Archers cost -10/20/30% Feudal/Castle/Imp.",
    },
    "Aztecs": {
        "pros": ["Strong monks", "Powerful infantry", "Extra gold from relics"],
        "cons": ["No cavalry", "No gunpowder", "Limited late game options"],
        "unique_units": ["Jaguar Warrior"],
        "bonuses": "+5 carry capacity. Military creation +11%. Monks +5 HP per tech. Relics +33% gold.",
    },
    "Chinese": {
        "pros": ["Strong tech tree", "Cheap techs", "Versatile"],
        "cons": ["Hard start (-200 food)", "No Bombard Tower", "Learning curve"],
        "unique_units": ["Chu Ko Nu"],
        "bonuses": "Start with +3 villagers, -200 food. Techs -10/15/20% Feudal/Castle/Imp. Demo ships +50% HP.",
    },
    "Mongols": {
        "pros": ["Best Mangudai in game", "Fast scouts", "Strong hunt bonus"],
        "cons": ["No good infantry late game", "No Plate Barding", "Limited defenses"],
        "unique_units": ["Mangudai"],
        "bonuses": "Cavalry archers fire 25% faster. Light cav +30% HP. Hunters work +40%. Scout line +2 LOS.",
    },
    "Vikings": {
        "pros": ["Free Wheelbarrow/Hand Cart", "Strong infantry UU", "Good navy"],
        "cons": ["No cavalry armor upgrades", "Weak late-game cavalry", "No Fire Ship upgrades"],
        "unique_units": ["Berserk", "Longboat"],
        "bonuses": "Wheelbarrow/Hand Cart free. Infantry +20% HP. Warships -15/15/20% cost.",
    },
    "Huns": {
        "pros": ["No houses needed", "Cheap cavalry archers", "Fast Paladins"],
        "cons": ["No Stone Walls", "Weak defenses", "No Bombard Cannon"],
        "unique_units": ["Tarkan"],
        "bonuses": "No houses needed. Cavalry Archers -10/20% Castle/Imp. Stables work 20% faster.",
    },
    "Teutons": {
        "pros": ["Tanky units (extra armor)", "Strong castles", "Cheap farms"],
        "cons": ["Slow units", "No Bracer", "Weak to archers"],
        "unique_units": ["Teutonic Knight"],
        "bonuses": "Melee armor +1/+2 Castle/Imp. Towers garrison +5. Murder holes free. Farms -40% cost.",
    },
    "Persians": {
        "pros": ["Strong War Elephants", "Fast TC/Dock", "Good cavalry"],
        "cons": ["Slow UU", "No Bracer", "Expensive UU"],
        "unique_units": ["War Elephant"],
        "bonuses": "Start +50 food, +50 wood. TC/Dock 2x HP, work 10/15/20% faster.",
    },
    "Spanish": {
        "pros": ["Strong gunpowder", "Conqs are amazing", "Trade bonus"],
        "cons": ["No good eco bonus early", "No Crossbow", "Expensive UU"],
        "unique_units": ["Conquistador", "Missionary"],
        "bonuses": "Builders work 30% faster. Blacksmith upgrades no gold. Cannon Galleons benefit from Ballistics. Trade +25% gold.",
    },
    "Goths": {
        "pros": ["Insane infantry flood", "Cheap infantry", "Strong late game spam"],
        "cons": ["No Stone Walls", "Weak early game", "No plate armor"],
        "unique_units": ["Huskarl"],
        "bonuses": "Infantry -20/25/30/35% cost. Infantry +1 attack vs buildings. Population +10. Loom instant.",
    },
    "Byzantines": {
        "pros": ["Cheapest trash units", "Full tech tree nearly", "Strong defenses"],
        "cons": ["No eco bonus", "Jack of all trades master of none", "Weak early aggression"],
        "unique_units": ["Cataphract"],
        "bonuses": "Trash units -25% cost. Buildings +10/20/30/40% HP. Fire Ships +20% attack. Free Town Watch.",
    },
    "Lithuanians": {
        "pros": ["Relic bonus for cavalry", "Fast food", "Strong Leitis"],
        "cons": ["Dependent on relics", "Weak archers late game", "No Siege Ram"],
        "unique_units": ["Leitis"],
        "bonuses": "+150 food start. Monastery works 20% faster. Each relic gives knights +1 attack (max +4). Trash units +1/+2 armor Castle/Imp.",
    },
    "Hindustanis": {
        "pros": ["Strong camels", "Good gunpowder", "Villager discount"],
        "cons": ["No Knights", "No good cavalry late game besides camels", "Weak vs pure archer civs"],
        "unique_units": ["Ghulam"],
        "bonuses": "Villagers -10/15/20/25% cost. Camel Riders +1/+1 armor. Gunpowder units +1 range.",
    },
    "Poles": {
        "pros": ["Stone from gold mines", "Strong cavalry", "Obuch shreds armor"],
        "cons": ["Weak archers", "No Plate Barding", "No Paladin without Folwark"],
        "unique_units": ["Obuch"],
        "bonuses": "Folwark drops off 10% food on farm placement. Stone miners generate gold. Winged Hussar available. Knights +1 attack vs archers.",
    },
    "Gurjaras": {
        "pros": ["Strongest camels", "Shrivamsha dodges projectiles", "Mill food bonus"],
        "cons": ["No Knights/Cavalier/Paladin", "Complex to play", "Weak siege"],
        "unique_units": ["Shrivamsha Rider", "Chakram Thrower"],
        "bonuses": "Can garrison livestock in mill for food trickle. Mounted units deal +50% bonus damage. Docks/Barracks/Archery Range/Stable techs -25%.",
    },
}

# Matchup knowledge: (civ1, civ2) -> (favorability, note)
# Ordered alphabetically by key; checked both directions
_MATCHUPS: dict[tuple[str, str], tuple[str, str]] = {
    ("Britons", "Franks"): ("Slight Britons", "Britons outrange Franks; Franks need to close gap with Paladin push"),
    ("Britons", "Goths"): ("Goths favored", "Huskarls hard counter archers; Britons struggle vs infantry flood"),
    ("Britons", "Mayans"): ("Even", "Both archer civs; Britons range vs Mayans cheaper archers and Eagles"),
    ("Britons", "Teutons"): ("Britons favored", "Teutons lack Bracer, Britons outrange and kite"),
    ("Chinese", "Mongols"): ("Slight Mongols", "Mongols faster aggression; Chinese versatile but slower start"),
    ("Franks", "Goths"): ("Franks favored", "Franks cavalry overwhelms before Goth spam kicks in"),
    ("Franks", "Mayans"): ("Slight Franks", "Frank cavalry vs Mayan archers; Eagles good but Paladins dominate"),
    ("Franks", "Teutons"): ("Even", "Both cavalry civs; Teutons tankier, Franks faster production"),
    ("Franks", "Vikings"): ("Even", "Franks cavalry vs Vikings infantry + eco; map dependent"),
    ("Goths", "Mayans"): ("Even", "Eagles vs Huskarls; timing dependent — Goths stronger late"),
    ("Huns", "Mongols"): ("Even", "Both cavalry archer civs; Mongols Mangudai vs Huns speed"),
    ("Lithuanians", "Franks"): ("Even", "Both strong cavalry; Lithuanians with relics can surpass Franks"),
    ("Mayans", "Aztecs"): ("Slight Mayans", "Mayans cheaper archers; Aztecs monks and eagles also strong"),
    ("Mongols", "Franks"): ("Slight Franks", "Franks Paladin beats Mangudai if they close; Mongols need space"),
    ("Persians", "Byzantines"): ("Even", "Both flexible; Persians eco vs Byzantines cheap counter units"),
    ("Spanish", "Franks"): ("Slight Franks", "Franks stronger eco early; Spanish Conqs powerful but expensive"),
    ("Vikings", "Aztecs"): ("Even", "Both strong eco and infantry; Vikings free wheelbarrow vs Aztecs military speed"),
}


def get_civ_info(civ_name: str) -> Optional[dict]:
    """Get detailed info for a civilization.

    Returns dict with pros, cons, unique_units, bonuses.
    Returns None if civ not in knowledge base.
    """
    return CIV_DATA.get(civ_name)


def get_matchup(civ1: str, civ2: str) -> dict:
    """Get matchup favorability between two civs.

    Returns dict with: favorability, note, civ1_info, civ2_info.
    """
    # Normalize names
    civ1 = civ1.strip().title()
    civ2 = civ2.strip().title()

    # Check both orderings
    key1 = (civ1, civ2)
    key2 = (civ2, civ1)

    favorability = "Unknown"
    note = "No matchup data available for this pairing."

    if key1 in _MATCHUPS:
        favorability, note = _MATCHUPS[key1]
    elif key2 in _MATCHUPS:
        fav, note = _MATCHUPS[key2]
        # Flip favorability perspective
        if "Slight" in fav:
            other = fav.replace("Slight ", "")
            if other == civ2:
                favorability = f"Slight {civ2}"
            else:
                favorability = f"Slight {civ1}"
        else:
            favorability = fav

    return {
        "civ1": civ1,
        "civ2": civ2,
        "favorability": favorability,
        "note": note,
        "civ1_info": get_civ_info(civ1),
        "civ2_info": get_civ_info(civ2),
    }


def list_civs() -> list[str]:
    """Return list of all AoE2 DE civs."""
    return ALL_CIVS
