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
    # --- Franks vs all remaining civs ---
    ("Franks", "Armenians"): ("Slight Franks", "Franks Paladin power overwhelms; Armenians versatile but lack a hard counter"),
    ("Franks", "Aztecs"): ("Even", "Aztecs monks and Eagles threaten Paladins; Franks need to avoid extended monk wars"),
    ("Franks", "Bengalis"): ("Slight Franks", "Bengalis elephants too slow; Franks Paladin raids before Bengalis mass up"),
    ("Franks", "Bohemians"): ("Franks favored", "Bohemians no cavalry and slow; Franks Paladin overwhelms before gunpowder mass"),
    ("Franks", "Bulgarians"): ("Even", "Bulgarians Konniks and cheap upgrades trade well; Franks raw Paladin HP edges it"),
    ("Franks", "Burmese"): ("Slight Franks", "Burmese infantry decent but Franks cavalry too mobile and strong"),
    ("Franks", "Byzantines"): ("Slight Franks", "Byzantines cheap camels and halbs slow Franks but lack killing power"),
    ("Franks", "Celts"): ("Slight Franks", "Celts siege dangerous but Franks cavalry raids before mass siege arrives"),
    ("Franks", "Chinese"): ("Even", "Chinese versatility and strong eco can match Franks; map dependent"),
    ("Franks", "Cumans"): ("Even", "Cumans 2nd TC feudal pressure is strong; Franks Castle age Paladin power counters"),
    ("Franks", "Dravidians"): ("Franks favored", "Dravidians no cavalry and weak vs Paladin; Medical Corps not enough"),
    ("Franks", "Georgians"): ("Even", "Georgians defensive bonuses and cavalry compete; Franks raw stats edge slightly"),
    ("Franks", "Huns"): ("Slight Franks", "Both cavalry civs but Franks Paladin HP wins head-to-head engagements"),
    ("Franks", "Incas"): ("Slight Franks", "Incas Eagles and Kamayuks dangerous but Franks eco and Paladin push through"),
    ("Franks", "Indians"): ("Even", "Indians camels strong vs cavalry; Franks need to avoid camel fights"),
    ("Franks", "Italians"): ("Slight Franks", "Genoese Crossbows counter but Franks faster Castle age timing overwhelms"),
    ("Franks", "Japanese"): ("Slight Franks", "Japanese halbs cheap but Franks mix in Hand Cannoneers and Paladin dominates"),
    ("Franks", "Khmer"): ("Even", "Khmer Ballista Elephants and Scorpions threaten; Franks mobility advantage"),
    ("Franks", "Magyars"): ("Slight Franks", "Magyars versatile cavalry but Franks Paladin HP wins the cavalry war"),
    ("Franks", "Malay"): ("Franks favored", "Malay cheap age-ups but no answer to Paladin; forced into trash wars too early"),
    ("Franks", "Malians"): ("Even", "Malians pierce armor infantry and Farimba cavalry trade evenly with Paladins"),
    ("Franks", "Portuguese"): ("Slight Franks", "Portuguese gold discount nice but too slow; Franks pressure before Organ Guns mass"),
    ("Franks", "Romans"): ("Slight Franks", "Romans versatile but Franks Paladin timing too strong to answer cleanly"),
    ("Franks", "Saracens"): ("Even", "Saracens camels and Mamelukes counter cavalry; Franks need to diversify"),
    ("Franks", "Tatars"): ("Even", "Tatars cavalry archers kite Paladins; Franks need to close the gap"),
    ("Franks", "Vietnamese"): ("Slight Franks", "Vietnamese archers tanky but Franks Paladin push too strong to hold"),
    # --- Top 20 civs matchups (missing pairs) ---
    ("Aztecs", "Britons"): ("Slight Aztecs", "Aztecs Eagles and monks pressure Britons; Britons need mass before Eagles arrive"),
    ("Aztecs", "Berbers"): ("Even", "Berbers cavalry mobility vs Aztecs monks and Eagles; tempo dependent"),
    ("Aztecs", "Chinese"): ("Even", "Both versatile; Aztecs monks and eco vs Chinese tech tree breadth"),
    ("Aztecs", "Ethiopians"): ("Even", "Both strong archers and eco bonuses; Aztecs monks vs Ethiopians firing speed"),
    ("Aztecs", "Goths"): ("Slight Aztecs", "Aztecs Eagles and Jaguar Warriors counter Goth infantry; monks add value"),
    ("Aztecs", "Hindustanis"): ("Even", "Aztecs Eagles strong vs Hindustanis; Ghulams counter Eagles back"),
    ("Aztecs", "Huns"): ("Slight Aztecs", "Aztecs monks counter Huns cavalry; Eagles trade well vs cavalry archers"),
    ("Aztecs", "Lithuanians"): ("Slight Lithuanians", "Lithuanians Paladin with relics overwhelms; Aztecs monks contest relics"),
    ("Aztecs", "Malians"): ("Even", "Both strong infantry civs; Malians pierce armor vs Aztecs raw damage"),
    ("Aztecs", "Mongols"): ("Even", "Aztecs monks vs Mongols aggression; Eagles vs Mangudai micro-dependent"),
    ("Aztecs", "Poles"): ("Even", "Poles Obuch strips armor from Eagles; Aztecs monks counter cavalry"),
    ("Aztecs", "Portuguese"): ("Slight Aztecs", "Aztecs pressure too fast; Portuguese need time to mass gunpowder"),
    ("Aztecs", "Spanish"): ("Slight Aztecs", "Aztecs faster eco and monks; Spanish Conqs dangerous but expensive"),
    ("Aztecs", "Teutons"): ("Slight Aztecs", "Aztecs monks destroy slow Teuton army; Eagles dodge heavy cavalry"),
    ("Aztecs", "Vikings"): ("Even", "Both strong eco and infantry; Vikings free wheelbarrow vs Aztecs military speed"),
    ("Berbers", "Britons"): ("Even", "Berbers Camel Archers tanky vs Britons range; Berbers need to close"),
    ("Berbers", "Chinese"): ("Even", "Both versatile; Berbers cheap cavalry vs Chinese broad tech tree"),
    ("Berbers", "Ethiopians"): ("Even", "Berbers Camel Archers vs Ethiopians fast-firing archers; mobility vs DPS"),
    ("Berbers", "Goths"): ("Slight Berbers", "Berbers cavalry overwhelms before Goth spam; Huskarls irrelevant vs cavalry"),
    ("Berbers", "Hindustanis"): ("Slight Hindustanis", "Hindustanis camels with armor counter Berbers cavalry line hard"),
    ("Berbers", "Huns"): ("Even", "Both cavalry civs; Berbers cheaper cavalry vs Huns no-house eco"),
    ("Berbers", "Japanese"): ("Slight Berbers", "Berbers cavalry mobility overwhelms Japanese infantry-focused play"),
    ("Berbers", "Lithuanians"): ("Even", "Both strong cavalry; Lithuanians relics vs Berbers cost efficiency"),
    ("Berbers", "Malians"): ("Even", "Both African civs with cavalry; Malians pierce armor infantry vs Berbers mobility"),
    ("Berbers", "Mayans"): ("Even", "Mayan archers vs Berbers Camel Archers; Eagles vs cheap cavalry"),
    ("Berbers", "Mongols"): ("Even", "Both mobile civs; Mongols Mangudai vs Berbers Camel Archers"),
    ("Berbers", "Poles"): ("Even", "Both cavalry civs; Obuch armor strip vs Berbers cost efficiency"),
    ("Berbers", "Portuguese"): ("Slight Berbers", "Berbers aggression too fast; Portuguese slow to mass"),
    ("Berbers", "Spanish"): ("Even", "Both Iberian civs; Spanish Conqs vs Berbers cheap cavalry"),
    ("Berbers", "Teutons"): ("Slight Berbers", "Berbers mobility kites Teutons slow army; Camel Archers key"),
    ("Berbers", "Vikings"): ("Even", "Berbers cavalry vs Vikings eco and infantry; map dependent"),
    ("Britons", "Chinese"): ("Even", "Both strong archer play; Chinese versatility vs Britons raw range"),
    ("Britons", "Hindustanis"): ("Slight Britons", "Britons outrange; Hindustanis Ghulams help but need to close"),
    ("Britons", "Huns"): ("Slight Britons", "Britons range counters cav archers; Huns need to raid and avoid archer mass"),
    ("Britons", "Japanese"): ("Slight Britons", "Britons range dominates; Japanese need to close with infantry"),
    ("Britons", "Lithuanians"): ("Even", "Lithuanians Paladin threatens Britons; Britons range keeps distance"),
    ("Britons", "Malians"): ("Slight Malians", "Malian infantry pierce armor counters Britons archers"),
    ("Britons", "Mongols"): ("Even", "Mangudai outmicro Longbows; Britons range keeps Mongols honest"),
    ("Britons", "Poles"): ("Slight Britons", "Britons outrange; Poles cavalry needs to close gap against archer mass"),
    ("Britons", "Portuguese"): ("Even", "Both archer civs; Portuguese gold discount vs Britons range advantage"),
    ("Britons", "Spanish"): ("Slight Britons", "Britons outrange Conqs; Spanish need to close with cavalry"),
    ("Britons", "Vikings"): ("Even", "Britons range vs Vikings eco and Berserks; infantry push can overwhelm"),
    ("Chinese", "Ethiopians"): ("Even", "Both versatile archer civs; Chinese broader options vs Ethiopians firing rate"),
    ("Chinese", "Goths"): ("Slight Chinese", "Chinese versatile response to Goth spam; Chu Ko Nu shreds infantry"),
    ("Chinese", "Hindustanis"): ("Even", "Chinese tech tree breadth vs Hindustanis camel power"),
    ("Chinese", "Huns"): ("Even", "Chinese versatile defense vs Huns aggression; start penalty matters"),
    ("Chinese", "Japanese"): ("Even", "Both East Asian civs; Chinese eco vs Japanese military bonuses"),
    ("Chinese", "Lithuanians"): ("Even", "Both strong civs; Lithuanians cavalry vs Chinese versatile counters"),
    ("Chinese", "Malians"): ("Even", "Chinese range vs Malians pierce armor infantry; both flexible"),
    ("Chinese", "Mongols"): ("Slight Mongols", "Mongols faster aggression; Chinese versatile but slower start"),
    ("Chinese", "Poles"): ("Even", "Chinese versatility vs Poles cavalry and Folwark eco"),
    ("Chinese", "Portuguese"): ("Slight Chinese", "Chinese faster eco and broader options; Portuguese too slow"),
    ("Chinese", "Spanish"): ("Even", "Chinese versatility vs Spanish Conqs and gunpowder"),
    ("Chinese", "Teutons"): ("Slight Chinese", "Chinese range and versatility kites Teutons slow army"),
    ("Chinese", "Vikings"): ("Even", "Both top eco civs; Chinese versatility vs Vikings infantry power"),
    ("Ethiopians", "Goths"): ("Slight Goths", "Huskarls hard counter Ethiopian archers; Shotels help but gold intensive"),
    ("Ethiopians", "Hindustanis"): ("Even", "Ethiopians archers vs Hindustanis camels; Ghulams threaten archers"),
    ("Ethiopians", "Huns"): ("Even", "Ethiopians fast-firing archers vs Huns cavalry archer mobility"),
    ("Ethiopians", "Japanese"): ("Even", "Both versatile military civs; Ethiopians range vs Japanese infantry"),
    ("Ethiopians", "Lithuanians"): ("Slight Lithuanians", "Lithuanians Paladin with relics too strong; Ethiopians need halbs"),
    ("Ethiopians", "Malians"): ("Even", "Both African civs; Ethiopians archers vs Malians pierce armor infantry"),
    ("Ethiopians", "Mayans"): ("Even", "Both top archer civs; Ethiopians firing speed vs Mayans cheaper archers"),
    ("Ethiopians", "Mongols"): ("Even", "Both aggressive civs; Ethiopians archers vs Mongols Mangudai"),
    ("Ethiopians", "Poles"): ("Even", "Ethiopians archers vs Poles cavalry; Obuch dangerous if they close"),
    ("Ethiopians", "Portuguese"): ("Slight Ethiopians", "Ethiopians faster tempo; Portuguese gold discount not enough early"),
    ("Ethiopians", "Spanish"): ("Even", "Ethiopians archers vs Spanish Conqs; both have strong unique units"),
    ("Ethiopians", "Teutons"): ("Ethiopians favored", "Ethiopians outrange and kite slow Teutons; no Bracer hurts Teutons"),
    ("Ethiopians", "Vikings"): ("Even", "Both strong eco; Ethiopians archers vs Vikings infantry and eco"),
    ("Goths", "Hindustanis"): ("Slight Hindustanis", "Hindustanis Ghulams and Hand Cannoneers shred Goth infantry"),
    ("Goths", "Huns"): ("Slight Huns", "Huns cavalry overwhelms before Goth spam; Huskarls useless vs cavalry"),
    ("Goths", "Japanese"): ("Even", "Japanese infantry bonus vs Goth flood; both infantry focused"),
    ("Goths", "Lithuanians"): ("Lithuanians favored", "Lithuanians Paladin crushes Goth infantry; Goths lack anti-cavalry"),
    ("Goths", "Malians"): ("Even", "Both infantry civs; Malians pierce armor helps vs Goth ranged support"),
    ("Goths", "Mongols"): ("Slight Mongols", "Mongols Mangudai shred Goth infantry from range; aggression too fast"),
    ("Goths", "Poles"): ("Slight Poles", "Poles cavalry and Obuch destroy Goth infantry; Folwark eco sustains"),
    ("Goths", "Portuguese"): ("Slight Goths", "Goth flood overwhelms slow Portuguese; Organ Guns help but not enough"),
    ("Goths", "Spanish"): ("Even", "Spanish gunpowder and Conqs vs Goth flood; timing dependent"),
    ("Goths", "Teutons"): ("Slight Teutons", "Teutons melee armor and strong infantry beat Goth spam head-to-head"),
    ("Goths", "Vikings"): ("Slight Goths", "Goth infantry flood overwhelms Vikings; Berserks trade OK but outnumbered"),
    ("Hindustanis", "Huns"): ("Slight Hindustanis", "Hindustanis camels destroy Huns cavalry; Ghulams handle cav archers"),
    ("Hindustanis", "Japanese"): ("Even", "Hindustanis camels vs Japanese versatile military; halbs trade well"),
    ("Hindustanis", "Lithuanians"): ("Even", "Hindustanis camels vs Lithuanians cavalry; both strong in different ways"),
    ("Hindustanis", "Malians"): ("Even", "Both have strong camels; Malians infantry vs Hindustanis gunpowder"),
    ("Hindustanis", "Mayans"): ("Even", "Hindustanis Ghulams counter Eagles; Mayan archers pressure camels"),
    ("Hindustanis", "Mongols"): ("Even", "Both aggressive civs; camels vs cavalry archers; micro dependent"),
    ("Hindustanis", "Poles"): ("Slight Hindustanis", "Hindustanis camels counter Poles cavalry focus hard"),
    ("Hindustanis", "Portuguese"): ("Even", "Both gold-efficient civs; Hindustanis aggression vs Portuguese defense"),
    ("Hindustanis", "Spanish"): ("Even", "Hindustanis camels vs Spanish cavalry; both have gunpowder options"),
    ("Hindustanis", "Teutons"): ("Slight Hindustanis", "Hindustanis camels and range destroy slow Teutons army"),
    ("Hindustanis", "Vikings"): ("Even", "Hindustanis camels vs Vikings infantry eco; both strong compositions"),
    ("Huns", "Japanese"): ("Slight Huns", "Huns cavalry mobility overwhelms Japanese infantry-focused play"),
    ("Huns", "Lithuanians"): ("Slight Lithuanians", "Lithuanians better cavalry with relics; Huns need early aggression"),
    ("Huns", "Malians"): ("Even", "Huns cavalry vs Malians pierce armor infantry; Farimba cavalry trades"),
    ("Huns", "Mayans"): ("Even", "Huns cavalry archers vs Mayan archers and Eagles; micro intensive"),
    ("Huns", "Poles"): ("Even", "Both cavalry civs; Huns speed vs Poles Folwark eco and Obuch"),
    ("Huns", "Portuguese"): ("Huns favored", "Huns aggression too fast for slow Portuguese to set up"),
    ("Huns", "Spanish"): ("Even", "Huns aggression vs Spanish Conqs; both need Castle age timing"),
    ("Huns", "Teutons"): ("Slight Huns", "Huns mobility kites slow Teutons; cav archers avoid infantry"),
    ("Huns", "Vikings"): ("Even", "Huns cavalry vs Vikings eco and infantry; aggressive mirror tempo"),
    ("Japanese", "Lithuanians"): ("Slight Lithuanians", "Lithuanians cavalry overwhelms Japanese infantry in open maps"),
    ("Japanese", "Malians"): ("Even", "Both strong infantry; Japanese attack speed vs Malians pierce armor"),
    ("Japanese", "Mayans"): ("Even", "Japanese versatile military vs Mayan archers and Eagles"),
    ("Japanese", "Mongols"): ("Slight Mongols", "Mongols mobility and Mangudai kite Japanese infantry"),
    ("Japanese", "Poles"): ("Even", "Japanese halbs counter Poles cavalry; Obuch dangerous in melee"),
    ("Japanese", "Portuguese"): ("Even", "Both versatile; Japanese aggression vs Portuguese gold efficiency"),
    ("Japanese", "Spanish"): ("Even", "Both versatile civs; Japanese military bonuses vs Spanish Conqs"),
    ("Japanese", "Teutons"): ("Even", "Both strong infantry; Japanese speed vs Teutons armor"),
    ("Japanese", "Vikings"): ("Even", "Both infantry civs; Vikings eco vs Japanese attack speed"),
    ("Lithuanians", "Malians"): ("Slight Lithuanians", "Lithuanians Paladin with relics overwhelms; Malians need Farimba cavalry"),
    ("Lithuanians", "Mayans"): ("Even", "Lithuanians cavalry vs Mayan archers and Eagles; relics key"),
    ("Lithuanians", "Mongols"): ("Even", "Both aggressive civs; Lithuanians cavalry vs Mongols Mangudai"),
    ("Lithuanians", "Portuguese"): ("Slight Lithuanians", "Lithuanians cavalry pressure too fast for Portuguese to set up"),
    ("Lithuanians", "Spanish"): ("Slight Lithuanians", "Lithuanians Paladin with relics stronger; Spanish Conqs need mass"),
    ("Lithuanians", "Teutons"): ("Even", "Both strong cavalry and infantry; Lithuanians speed vs Teutons armor"),
    ("Lithuanians", "Vikings"): ("Even", "Lithuanians cavalry vs Vikings eco and infantry; map dependent"),
    ("Malians", "Mayans"): ("Even", "Malians pierce armor infantry tanks Mayan archers; Eagles vs Champskarls"),
    ("Malians", "Mongols"): ("Even", "Malians infantry tanks archer fire; Mongols mobility counters"),
    ("Malians", "Poles"): ("Even", "Both have cavalry; Malians infantry vs Poles Obuch in melee wars"),
    ("Malians", "Portuguese"): ("Slight Malians", "Malians aggression and pierce armor overwhelm slow Portuguese"),
    ("Malians", "Spanish"): ("Even", "Both have cavalry and unique strengths; Malians infantry vs Spanish gunpowder"),
    ("Malians", "Teutons"): ("Even", "Both tanky infantry civs; Malians pierce armor vs Teutons melee armor"),
    ("Malians", "Vikings"): ("Even", "Both strong eco; Malians infantry vs Vikings infantry; pierce armor key"),
    ("Mayans", "Poles"): ("Slight Mayans", "Mayan archers kite Poles cavalry; Eagles handle siege"),
    ("Mayans", "Portuguese"): ("Slight Mayans", "Mayans faster tempo and cheaper archers; Portuguese too slow to mass"),
    ("Mayans", "Spanish"): ("Slight Mayans", "Mayan archers outproduce; Spanish Conqs dangerous but Mayans eco wins"),
    ("Mayans", "Teutons"): ("Mayans favored", "Mayans kite slow Teutons all game; no Bracer cripples Teutons"),
    ("Mayans", "Vikings"): ("Even", "Mayans archers vs Vikings eco and infantry; both top-tier civs"),
    ("Mongols", "Poles"): ("Even", "Mongols mobility vs Poles cavalry and eco; Mangudai vs Obuch"),
    ("Mongols", "Portuguese"): ("Mongols favored", "Mongols aggression overwhelms slow Portuguese before they mass up"),
    ("Mongols", "Spanish"): ("Slight Mongols", "Mongols faster and more mobile; Spanish Conqs trade but Mongols tempo wins"),
    ("Mongols", "Teutons"): ("Mongols favored", "Mongols kite slow Teutons all game; Mangudai untouchable"),
    ("Mongols", "Vikings"): ("Even", "Both aggressive civs; Mongols mobility vs Vikings eco and infantry"),
    ("Poles", "Portuguese"): ("Slight Poles", "Poles cavalry pressure too fast; Portuguese gold discount not enough early"),
    ("Poles", "Spanish"): ("Even", "Both cavalry civs; Poles Folwark eco vs Spanish Conqs and gunpowder"),
    ("Poles", "Teutons"): ("Even", "Both Central European civs; Obuch armor strip vs Teutons melee armor"),
    ("Poles", "Vikings"): ("Even", "Poles cavalry vs Vikings infantry eco; Folwark vs free wheelbarrow"),
    ("Portuguese", "Spanish"): ("Even", "Iberian derby; Portuguese gold discount vs Spanish faster building and Conqs"),
    ("Portuguese", "Teutons"): ("Even", "Both slow civs; Portuguese range vs Teutons melee power"),
    ("Portuguese", "Vikings"): ("Slight Vikings", "Vikings faster eco and aggression; Portuguese too slow to set up"),
    ("Spanish", "Teutons"): ("Even", "Both strong cavalry and infantry; Spanish Conqs vs Teutons armor"),
    ("Spanish", "Vikings"): ("Even", "Spanish Conqs and gunpowder vs Vikings eco and infantry"),
    ("Teutons", "Vikings"): ("Slight Vikings", "Vikings superior eco and mobility; Teutons too slow without Bracer"),
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
