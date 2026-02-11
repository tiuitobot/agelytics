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
    "Armenians": {
        "pros": ["Strong defensive buildings", "Flexible tech tree", "Composite Bowman is versatile"],
        "cons": ["No Paladin", "Mediocre eco bonuses", "Lacks strong late-game cavalry"],
        "unique_units": ["Composite Bowman"],
        "bonuses": "Infantry and cavalry repair siege. Mule Cart replaces Market for mobile drop-off. Team bonus: Galley line +2 LOS.",
    },
    "Bengalis": {
        "pros": ["Elephant civs with strong eco", "Ratha is versatile ranged/melee switch", "Cheap villagers in Castle+"],
        "cons": ["Weak early aggression", "No Knight line", "Elephants countered by halbs/monks"],
        "unique_units": ["Ratha"],
        "bonuses": "Town Centers spawn 2 villagers. Elephant units resist conversion. Ships regenerate 15 HP/min.",
    },
    "Berbers": {
        "pros": ["Cheap cavalry", "Strong Camel Archers", "Good navy"],
        "cons": ["No Siege Engineers", "Mediocre infantry", "No Paladin"],
        "unique_units": ["Camel Archer", "Genitour"],
        "bonuses": "Villagers move 10% faster. Stable units -15/20% cost Castle/Imp. Ships move 10% faster.",
    },
    "Bulgarians": {
        "pros": ["Free Militia-line upgrades", "Strong Konniks", "Krepost is cheap castle"],
        "cons": ["No Crossbow", "Weak archers overall", "Limited navy"],
        "unique_units": ["Konnik"],
        "bonuses": "Militia-line upgrades free. Krepost available (mini-castle). Town Centers +5 garrison. Blacksmith/Siege Workshop techs 50% faster.",
    },
    "Burgundians": {
        "pros": ["Early eco upgrades", "Strong Paladins with Flemish Revolution", "Coustillier charge attack"],
        "cons": ["Weak archers", "Flemish Revolution is all-in", "No Bracer"],
        "unique_units": ["Coustillier", "Flemish Militia"],
        "bonuses": "Eco upgrades available one age earlier. Cavalier upgrade available in Castle Age. Gunpowder units +25% attack.",
    },
    "Burmese": {
        "pros": ["Free lumber upgrades", "Strong infantry with Manipur Cavalry", "Good monks"],
        "cons": ["No Bracer or Arbalester", "Weak archers", "Battle Elephants vulnerable to monks"],
        "unique_units": ["Arambai"],
        "bonuses": "Lumber Camp upgrades free. Infantry +1/+2/+3 attack Feudal/Castle/Imp. Monastery techs -50% cost.",
    },
    "Celts": {
        "pros": ["Fastest infantry", "Strong siege", "Lumberjack bonus"],
        "cons": ["No Bracer", "Weak archers", "No Plate Barding Armor"],
        "unique_units": ["Woad Raider"],
        "bonuses": "Infantry move 15% faster. Lumberjacks work 15% faster. Siege fire 25% faster. Sheep cannot be stolen.",
    },
    "Cumans": {
        "pros": ["Feudal Age TC", "Fast cavalry", "Kipchak multi-arrow"],
        "cons": ["Weak defenses", "No Stone Walls until Castle", "Limited tech tree late game"],
        "unique_units": ["Kipchak"],
        "bonuses": "Can build 2nd TC in Feudal Age. Siege Workshop and Battering Ram available in Feudal. Cavalry move 5/10% faster Feudal/Castle.",
    },
    "Dravidians": {
        "pros": ["Strong infantry and navy", "Urumi Swordsman AoE", "Medical Corps heals elephants"],
        "cons": ["No cavalry at all", "Weak to mobile armies", "No Hussar or Knight line"],
        "unique_units": ["Urumi Swordsman", "Thirisadai"],
        "bonuses": "Fishermen and Farmers carry +15. Barracks techs 50% cost. Skirmishers and Elephant Archers fire 25% faster.",
    },
    "Ethiopians": {
        "pros": ["Strong archers with extra range", "Free Pikeman/Halberdier", "Royal Heirs for fast Shotel flood"],
        "cons": ["Weak cavalry", "Shotel Warriors fragile", "No Paladin or Hussar"],
        "unique_units": ["Shotel Warrior"],
        "bonuses": "+100 food/gold on Age-up. Archer-line fire 18% faster. Free Pikeman/Halberdier upgrades.",
    },
    "Georgians": {
        "pros": ["Strong defensive civ", "Monaspa cavalry regenerates", "Hill combat bonus"],
        "cons": ["Limited archer options", "No Arbalester", "Eco bonuses modest"],
        "unique_units": ["Monaspa"],
        "bonuses": "Cavalry receive -20% damage on hills. Fortified Church replaces Monastery. Mule Cart available for mobile drop-off.",
    },
    "Incas": {
        "pros": ["Strong infantry with Fabric Shields", "Versatile Eagles", "Villagers benefit from Blacksmith"],
        "cons": ["No cavalry", "No gunpowder", "Dependent on gold-heavy units"],
        "unique_units": ["Kamayuk", "Slinger"],
        "bonuses": "Villagers affected by Blacksmith infantry armor. Houses support 10 pop. Farms built instantly. Team bonus: Farms +1 LOS.",
    },
    "Japanese": {
        "pros": ["Fastest attacking infantry", "Strong fishing eco", "Versatile tech tree"],
        "cons": ["No Bloodlines", "Cavalry weaker than average", "No eco bonus on land maps"],
        "unique_units": ["Samurai"],
        "bonuses": "Fishing Ships 2x HP, +2 pierce armor, work 5/10/15/20% faster. Infantry attack 33% faster. Mills/Lumber/Mining free.",
    },
    "Khmer": {
        "pros": ["No building requirements", "Strong Ballista Elephants", "Farmers auto-drop food"],
        "cons": ["Slow units overall", "Elephants countered by halbs/monks", "Weak early game"],
        "unique_units": ["Ballista Elephant"],
        "bonuses": "No building requirements for advancing. Farmers drop food automatically. Battle Elephants +3 speed with Husbandry. Scorpions +1 range.",
    },
    "Koreans": {
        "pros": ["Strong towers and defensive play", "War Wagons are tanky", "Free armor upgrades"],
        "cons": ["Slow military", "Weak cavalry", "Predictable tower rush strategy"],
        "unique_units": ["War Wagon", "Turtle Ship"],
        "bonuses": "Archer armor upgrades free. Towers +1/+2 range Castle/Imp. Military buildings built 33% faster.",
    },
    "Malay": {
        "pros": ["Fastest age-up", "Cheap Battle Elephants", "Forced Levy (trash 2HS)"],
        "cons": ["Weak cavalry", "No Bloodlines", "Elephants still fragile despite cost"],
        "unique_units": ["Karambit Warrior"],
        "bonuses": "Age advances 66% faster. Fish traps unlimited food, cheap. Battle Elephants -30/40% cost. Forced Levy: 2H Swordsmen cost no gold.",
    },
    "Malians": {
        "pros": ["Extra pierce armor on infantry", "Strong Farimba cavalry", "Good eco with gold bonus"],
        "cons": ["No Bracer", "Weaker archers late game", "No Halberdier"],
        "unique_units": ["Gbeto"],
        "bonuses": "Infantry +1/+2/+3 pierce armor Feudal/Castle/Imp. Gold mines last 30% longer. Buildings built 15% faster (team).",
    },
    "Magyars": {
        "pros": ["Free forging line upgrades", "Cheap scouts", "Recurve Bow for cav archers"],
        "cons": ["Limited siege options", "No Bombard Cannon", "Infantry mediocre"],
        "unique_units": ["Magyar Huszar"],
        "bonuses": "Forging, Iron Casting, Blast Furnace free. Scout Cavalry line -15% cost. Villagers kill wolves in 1 hit.",
    },
    "Portuguese": {
        "pros": ["All units cost -20% gold", "Strong navy with Carrack", "Organ Guns shred infantry"],
        "cons": ["Slow gameplay style", "Weak cavalry", "Gold discount less impactful early"],
        "unique_units": ["Organ Gun", "Caravel"],
        "bonuses": "All units -20% gold cost. Ships +10% HP. Feitoria generates resources (infinite). Free Cartography.",
    },
    "Romans": {
        "pros": ["Cheap Scorpions and Galleys", "Centurion boosts infantry", "Strong infantry and siege"],
        "cons": ["No strong cavalry", "Limited cavalry archer options", "Dependent on infantry compositions"],
        "unique_units": ["Centurion", "Legionary"],
        "bonuses": "Infantry +5% move speed. Galley-line and Scorpions cost -25% gold. Villagers +5% work rate per age.",
    },
    "Saracens": {
        "pros": ["Market abuse for eco flexibility", "Strong Mamelukes", "Good camels and archers"],
        "cons": ["No eco bonus besides market", "Expensive Mameluke", "Jack of all trades issue"],
        "unique_units": ["Mameluke"],
        "bonuses": "Market buy/sell 5% better. Archers +3 attack vs buildings. Transport Ships 2x HP, +5 carry.",
    },
    "Sicilians": {
        "pros": ["50% bonus damage reduction", "Serjeant builds Donjons", "First Crusade for instant Serjeants"],
        "cons": ["No Bracer", "Weaker archers", "Bonus damage reduction nerfed in recent patches"],
        "unique_units": ["Serjeant"],
        "bonuses": "Land military units -50% bonus damage. Castle drop produces 7 Serjeants (First Crusade). Farm upgrades +100% food. TCs built 100% faster.",
    },
    "Slavs": {
        "pros": ["Strongest farming eco", "Cheap siege", "Boyar is tanky melee cavalry"],
        "cons": ["No Bracer", "Weak archers", "No Hussar in late game"],
        "unique_units": ["Boyar"],
        "bonuses": "Farmers work 10% faster. Siege Workshop units -15% cost. Tracking free. Military buildings +5 pop space (team).",
    },
    "Tatars": {
        "pros": ["Free Thumb Ring", "Strong cavalry archers", "Hill bonus damage"],
        "cons": ["No Halberdier", "Weak infantry", "Dependent on gold-heavy units"],
        "unique_units": ["Keshik"],
        "bonuses": "Herdables +50% food. Free Thumb Ring. Cavalry Archers +1/+1 armor Parthian Tactics. Units deal +25% damage from elevation.",
    },
    "Turks": {
        "pros": ["Strongest gunpowder", "Free Chemistry", "Gold miners work faster"],
        "cons": ["No Pikeman line", "Worst trash units in game", "No Elite Skirmisher"],
        "unique_units": ["Janissary"],
        "bonuses": "Gunpowder units +25% HP. Gold miners work 20% faster. Free Chemistry. Light Cavalry and Hussar upgrades free.",
    },
    "Vietnamese": {
        "pros": ["See enemy TC at start", "Extra HP archers", "Strong Rattan Archers"],
        "cons": ["Slow eco", "No Hussar", "Weak cavalry overall"],
        "unique_units": ["Rattan Archer"],
        "bonuses": "Reveal enemy positions at game start. Archery Range units +20% HP. Conscription free. Paper Money gives team gold.",
    },
    "Bohemians": {
        "pros": ["Strong gunpowder units", "Cheap Monasteries and techs", "Hussite unique units"],
        "cons": ["No cavalry", "Slow early game", "Dependent on gold"],
        "unique_units": ["Hussite Wagon", "Houfnice"],
        "bonuses": "Chemistry free. Monastery techs -50% cost. Mining Camp upgrades free. Spearmen +25% bonus damage.",
    },
    "Italians": {
        "pros": ["Cheaper age-ups", "Strong Genoese Crossbowmen (anti-cav)", "Gunpowder discount"],
        "cons": ["Weak cavalry", "No strong melee infantry", "Dependent on gold units"],
        "unique_units": ["Genoese Crossbowman", "Condottiero"],
        "bonuses": "Age advance -15% cost. Dock techs -50%. Gunpowder units -20% cost. Fishing Ships -15 wood.",
    },
    "Hindustanis": {
        "pros": ["Strong camels", "Good gunpowder", "Villager discount on food"],
        "cons": ["No Knights", "Weak siege", "Limited archer options late game"],
        "unique_units": ["Ghulam", "Imperial Camel Rider"],
        "bonuses": "Villagers -10/15/20/25% food cost per age. Camel Riders +1/+1 armor. Gunpowder units +1 range.",
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
    ("Britons", "Celts"): ("Slight Britons", "Britons outrange; Celts need to close with fast infantry and siege"),
    ("Britons", "Ethiopians"): ("Even", "Both top archer civs; Ethiopians faster firing vs Britons extra range"),
    ("Britons", "Vietnamese"): ("Slight Britons", "Britons range advantage; Vietnamese extra HP archers keep them competitive"),
    ("Celts", "Goths"): ("Slight Goths", "Goth infantry flood overwhelms; Celts siege helps but Huskarls close fast"),
    ("Celts", "Teutons"): ("Even", "Celts siege vs Teutons melee armor; Celts speed vs Teutons tankiness"),
    ("Chinese", "Mayans"): ("Even", "Both versatile with strong archers; Chinese broader tech tree vs Mayans eco"),
    ("Ethiopians", "Franks"): ("Slight Franks", "Franks Paladin overwhelms; Ethiopians need archers + halbs to hold"),
    ("Franks", "Berbers"): ("Even", "Franks Paladin vs Berbers cheap cavalry and Camel Archers"),
    ("Franks", "Burgundians"): ("Even", "Mirror cavalry civs; Burgundians early eco edge vs Franks HP bonus"),
    ("Franks", "Hindustanis"): ("Slight Hindustanis", "Hindustanis camels counter Franks cavalry hard"),
    ("Franks", "Lithuanians"): ("Even", "Both strong cavalry; Lithuanians with relics can surpass Franks"),
    ("Franks", "Persians"): ("Slight Franks", "Franks cheaper eco; Persians War Elephants too slow vs Paladin"),
    ("Franks", "Poles"): ("Even", "Both cavalry focused; Obuch armor strip dangerous for Paladins"),
    ("Gurjaras", "Franks"): ("Slight Gurjaras", "Gurjaras camels with bonus damage destroy Frank cavalry"),
    ("Gurjaras", "Hindustanis"): ("Even", "Both camel civs; Gurjaras bonus damage vs Hindustanis armor"),
    ("Huns", "Britons"): ("Slight Britons", "Britons range counters cav archers; Huns need to raid and avoid archer mass"),
    ("Huns", "Goths"): ("Slight Huns", "Huns cavalry overwhelms before Goth spam; Huskarls useless vs cavalry"),
    ("Japanese", "Aztecs"): ("Even", "Both strong infantry; Japanese faster attack vs Aztecs monks and eco"),
    ("Koreans", "Franks"): ("Slight Franks", "War Wagons tanky but Franks Paladins close gap; tower play delays"),
    ("Malians", "Britons"): ("Slight Malians", "Malian infantry pierce armor counters Britons archers"),
    ("Mayans", "Franks"): ("Slight Franks", "Frank cavalry vs Mayan archers; Eagles good but Paladins dominate"),
    ("Mongols", "Britons"): ("Even", "Mangudai outmicro Longbows; Britons range keeps Mongols honest"),
    ("Mongols", "Mayans"): ("Even", "Mongols aggression vs Mayans eco; both have strong ranged play"),
    ("Poles", "Lithuanians"): ("Even", "Both Eastern European cavalry civs; relic-dependent vs Folwark eco"),
    ("Sicilians", "Franks"): ("Slight Franks", "Bonus damage reduction helps but Franks raw Paladin power wins"),
    ("Slavs", "Franks"): ("Slight Franks", "Franks cavalry better; Slavs need siege to compensate"),
    ("Tatars", "Mongols"): ("Even", "Both cavalry archer civs; Tatars hill bonus vs Mongols Mangudai"),
    ("Turks", "Franks"): ("Even", "Turks gunpowder vs Franks cavalry; Turks struggle without gold"),
    ("Vikings", "Franks"): ("Even", "Vikings eco + infantry vs Franks cavalry; map dependent"),
    ("Vikings", "Japanese"): ("Even", "Both infantry civs; Vikings eco vs Japanese attack speed"),
    ("Vietnamese", "Mongols"): ("Slight Mongols", "Mongols aggression too fast; Vietnamese need to survive to Imperial"),
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

    favorability = None
    note = None

    if key1 in _MATCHUPS:
        favorability, note = _MATCHUPS[key1]
    elif key2 in _MATCHUPS:
        fav, n = _MATCHUPS[key2]
        note = n
        if "Slight" in fav:
            other = fav.replace("Slight ", "")
            if other == civ2:
                favorability = f"Slight {civ2}"
            else:
                favorability = f"Slight {civ1}"
        else:
            favorability = fav

    # Auto-generate note from pros/cons when no specific matchup exists
    if not favorability:
        info1 = CIV_DATA.get(civ1, {})
        info2 = CIV_DATA.get(civ2, {})
        if info1 and info2:
            pros1 = ", ".join(info1.get("pros", [])[:2])
            pros2 = ", ".join(info2.get("pros", [])[:2])
            favorability = "Even (estimated)"
            note = f"{civ1}: {pros1}. {civ2}: {pros2}. No specific data — check civ strengths."
        else:
            favorability = "Unknown"
            note = "No matchup data available for this pairing."

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
