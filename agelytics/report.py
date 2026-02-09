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
    lines.append(f"  📅 {match.get('played_at', '?')[:16].replace('T', ' ')}")
    lines.append(f"  🗺️  {match.get('map_name', '?')}")
    lines.append(f"  ⏱️  {format_duration(match.get('duration_secs', 0))}")
    lines.append(f"  🎮 {match.get('diplomacy', '?')} | {match.get('game_type', '?')} | {match.get('speed', '?')}")
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
