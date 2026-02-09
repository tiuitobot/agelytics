"""Generate text reports from match data."""

from datetime import timedelta


def format_duration(secs: float) -> str:
    """Format seconds as MM:SS or HH:MM:SS."""
    if not secs:
        return "0:00"
    td = timedelta(seconds=int(secs))
    total_secs = int(td.total_seconds())
    hours = total_secs // 3600
    minutes = (total_secs % 3600) // 60
    seconds = total_secs % 60
    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"


# Units to exclude from army composition (eco/starting units)
ECO_UNITS = {"Villager", "Scout Cavalry", "Trade Cart", "Trade Cog", "Fishing Ship", "Transport Ship"}

# Key military/age techs to show (filter out basic eco techs)
KEY_TECHS = {
    # Age advances
    "Feudal Age", "Castle Age", "Imperial Age",
    # Military upgrades
    "Cavalier", "Paladin", "Crossbowman", "Arbalester", "Heavy Scorpion", "Trebuchet",
    "Pikeman", "Halberdier", "Champion", "Two-Handed Swordsman", "Long Swordsman",
    "Heavy Cavalry Archer", "Hussar", "Heavy Camel Rider", "Imperial Camel Rider",
    "Elite Skirmisher", "Heavy Demolition Ship", "Fast Fire Ship", "Heavy Scorpion",
    "Capped Ram", "Siege Ram", "Onager", "Siege Onager",
    # Important techs
    "Ballistics", "Chemistry", "Siege Engineers", "Bloodlines", "Husbandry",
    "Thumb Ring", "Parthian Tactics", "Supplies", "Squires", "Arson",
    # Elite unique units (common ones)
    "Elite Cataphract", "Elite Chu Ko Nu", "Elite Longbowman", "Elite Mangudai",
    "Elite War Elephant", "Elite Mameluke", "Elite Janissary", "Elite Teutonic Knight",
    "Elite Samurai", "Elite Throwing Axeman", "Elite Huskarl", "Elite Conquistador",
    "Elite Tarkan", "Elite War Wagon", "Elite Turtle Ship", "Elite Jaguar Warrior",
    "Elite Eagle Warrior", "Elite Plumed Archer", "Elite Kamayuk", "Elite Elephant Archer",
    "Elite Genoese Crossbowman", "Elite Magyar Huszar", "Elite Boyar",
}


def match_report(match: dict, player_name: str = None) -> str:
    """Generate a text report for a single match.
    
    If player_name is given, perspective is from that player.
    """
    players = match.get("players", [])
    if not players:
        return "No player data available."

    # Find perspective player
    me = None
    opponents = []
    if player_name:
        for p in players:
            if p["name"].lower() == player_name.lower():
                me = p
            else:
                opponents.append(p)
    
    if not me and players:
        me = players[0]
        opponents = players[1:]

    # Result
    result = "🏆 VITÓRIA" if me and me.get("winner") else "❌ DERROTA"
    
    # Header
    lines = []
    lines.append(f"{'═' * 40}")
    lines.append(f"  AGELYTICS — Match Report")
    lines.append(f"{'═' * 40}")
    lines.append("")
    
    # Result line
    if me:
        opp_str = " vs ".join(f"{o['name']} ({o['civ_name']})" for o in opponents) or "?"
        lines.append(f"  {result}")
        lines.append(f"  {me['name']} ({me['civ_name']}) vs {opp_str}")
    else:
        lines.append("  " + " vs ".join(f"{p['name']} ({p['civ_name']})" for p in players))
    
    lines.append("")
    
    # Match details
    played_at = match.get('played_at', '?')[:16].replace('T', ' ')
    map_name = match.get('map_name', '?')
    duration = format_duration(match.get('duration_secs', 0))
    game_info = f"{match.get('game_type', '?')} | {match.get('speed', '?')} | Pop {match.get('pop_limit', 200)}"
    
    lines.append(f"  📅 {played_at} | 🗺️ {map_name} | ⏱️ {duration}")
    lines.append(f"  🎮 {game_info}")
    lines.append("")
    
    # Player details
    lines.append(f"  {'─' * 36}")
    lines.append(f"  Players:")
    for p in players:
        w = "👑" if p.get("winner") else "  "
        elo = f"ELO {p['elo']}" if p.get("elo") else "ELO ?"
        eapm = f"eAPM {p['eapm']}" if p.get("eapm") else ""
        marker = " ◄" if me and p["name"] == me["name"] else ""
        lines.append(f"  {w} {p['name']} — {p['civ_name']} ({elo}{', ' + eapm if eapm else ''}){marker}")
    
    # ELO diff
    if me and opponents and me.get("elo") and opponents[0].get("elo"):
        diff = opponents[0]["elo"] - me["elo"]
        sign = "+" if diff > 0 else ""
        lines.append(f"  📊 ELO gap: {sign}{diff} (opponent {'higher' if diff > 0 else 'lower'})")
    
    lines.append(f"  {'─' * 36}")
    
    # Age-up times
    age_ups = match.get("age_ups", [])
    if age_ups:
        lines.append("")
        lines.append("  ⏫ Age-Up Times:")
        
        # Group by player
        player_ages = {}
        for age_up in age_ups:
            player = age_up["player"]
            if player not in player_ages:
                player_ages[player] = {}
            player_ages[player][age_up["age"]] = age_up["timestamp_secs"]
        
        # Format as table
        ages = ["Feudal Age", "Castle Age", "Imperial Age"]
        age_labels = ["Feudal", "Castle", "Imperial"]
        
        # Header
        if len(players) == 2:
            p1_name = players[0]["name"]
            p2_name = players[1]["name"]
            lines.append(f"     Age          {p1_name[:12].ljust(12)} {p2_name[:12].ljust(12)}")
        
            for age, label in zip(ages, age_labels):
                p1_time = player_ages.get(p1_name, {}).get(age)
                p2_time = player_ages.get(p2_name, {}).get(age)
                p1_str = format_duration(p1_time) if p1_time else "—"
                p2_str = format_duration(p2_time) if p2_time else "—"
                lines.append(f"     {label.ljust(12)} {p1_str.ljust(12)} {p2_str.ljust(12)}")
    
    # Army composition
    unit_production = match.get("unit_production", {})
    if unit_production:
        lines.append("")
        lines.append("  ⚔️ Army Composition:")
        
        for player in [p["name"] for p in players]:
            units = unit_production.get(player, {})
            # Filter out eco units and sort by count
            army_units = [(unit, count) for unit, count in units.items() 
                          if unit not in ECO_UNITS and count > 0]
            army_units.sort(key=lambda x: x[1], reverse=True)
            
            if army_units:
                unit_str = ", ".join(f"{unit} ×{count}" for unit, count in army_units[:8])
                lines.append(f"     {player}: {unit_str}")
    
    # Economy
    if unit_production:
        lines.append("")
        lines.append("  🏠 Economy:")
        
        for player in [p["name"] for p in players]:
            units = unit_production.get(player, {})
            buildings = match.get("buildings", {}).get(player, {})
            
            villagers = units.get("Villager", 0)
            farms = buildings.get("Farm", 0)
            
            eco_parts = []
            if villagers > 0:
                eco_parts.append(f"{villagers} villagers produced")
            if farms > 0:
                eco_parts.append(f"{farms} farms")
            
            if eco_parts:
                lines.append(f"     {player}: {', '.join(eco_parts)}")
    
    # Key techs
    researches = match.get("researches", [])
    if researches:
        lines.append("")
        lines.append("  🔬 Key Techs:")
        
        # Group by player
        player_techs = {}
        for research in researches:
            player = research["player"]
            tech = research["tech"]
            timestamp = research["timestamp_secs"]
            
            if tech in KEY_TECHS:
                if player not in player_techs:
                    player_techs[player] = []
                player_techs[player].append((tech, timestamp))
        
        for player in [p["name"] for p in players]:
            techs = player_techs.get(player, [])
            if techs:
                # Sort by timestamp and show top 5
                techs.sort(key=lambda x: x[1])
                tech_str = ", ".join(f"{tech} ({format_duration(ts)})" for tech, ts in techs[:5])
                lines.append(f"     {player}: {tech_str}")
    
    # End game
    lines.append("")
    resign_player = match.get("resign_player")
    if resign_player:
        lines.append(f"  🏁 End: {resign_player} resigned at {duration}")
    else:
        lines.append(f"  🏁 End: Match completed at {duration}")
    
    lines.append(f"  {'─' * 36}")
    lines.append("")

    return "\n".join(lines)


def player_summary(stats: dict) -> str:
    """Generate a player evolution summary."""
    if stats["matches"] == 0:
        return f"No matches found for {stats['name']}."
    
    lines = []
    lines.append(f"{'═' * 40}")
    lines.append(f"  AGELYTICS — Player: {stats['name']}")
    lines.append(f"{'═' * 40}")
    lines.append("")
    lines.append(f"  Matches: {stats['matches']} ({stats['wins']}W / {stats['losses']}L)")
    lines.append(f"  Win rate: {stats['winrate']:.1f}%")
    
    if stats.get("elo_current"):
        lines.append(f"  ELO: {stats['elo_current']} (min {stats['elo_min']}, max {stats['elo_max']})")
    if stats.get("avg_eapm"):
        lines.append(f"  Avg eAPM: {stats['avg_eapm']:.0f}")
    
    lines.append("")
    lines.append(f"  Top civs:")
    sorted_civs = sorted(stats["civs"].items(), key=lambda x: x[1]["played"], reverse=True)[:5]
    for civ, data in sorted_civs:
        wr = data["won"] / data["played"] * 100 if data["played"] else 0
        lines.append(f"    {civ}: {data['played']} games ({wr:.0f}% WR)")
    
    lines.append("")
    return "\n".join(lines)


def matches_table(matches: list[dict], player_name: str = None) -> str:
    """Generate a compact table listing all matches.
    
    If player_name is given, shows result from that player's perspective.
    """
    if not matches:
        return "No matches found."
    
    lines = []
    lines.append("ID   Date        Map           Civ            vs Civ          ELO  Result  Duration")
    lines.append("─" * 90)
    
    for m in matches:
        players = m.get("players", [])
        if not players:
            continue
        
        # Find the player and opponent
        me = None
        opponent = None
        
        if player_name:
            for p in players:
                if p["name"].lower() == player_name.lower():
                    me = p
                else:
                    opponent = p
        
        if not me:
            me = players[0]
            opponent = players[1] if len(players) > 1 else None
        
        # Format fields
        match_id = str(m["id"]).ljust(4)
        date = m.get("played_at", "?")[:10]  # YYYY-MM-DD
        map_name = (m.get("map_name", "?")[:13]).ljust(13)
        my_civ = (me["civ_name"][:14]).ljust(14)
        opp_civ = (opponent["civ_name"][:14] if opponent else "?").ljust(14)
        elo = str(me.get("elo") or "?").ljust(4)
        result = "W" if me.get("winner") else "L"
        duration = format_duration(m.get("duration_secs", 0))
        
        lines.append(f"{match_id} {date}  {map_name} {my_civ} {opp_civ} {elo} {result}       {duration}")
    
    return "\n".join(lines)
