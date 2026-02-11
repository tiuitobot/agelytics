"""Deterministic scouting reports from parsed replays."""

import statistics
from collections import Counter, defaultdict
from typing import Optional

from .replay_parser import parse_opponent_replays


# Civ ID to name mapping (subset - extend as needed)
CIV_NAMES = {
    1: "Britons", 2: "Franks", 3: "Goths", 4: "Teutons", 5: "Japanese",
    6: "Chinese", 7: "Byzantines", 8: "Persians", 9: "Saracens", 10: "Turks",
    11: "Vikings", 12: "Mongols", 13: "Celts", 14: "Spanish", 15: "Aztecs",
    16: "Mayans", 17: "Huns", 18: "Koreans", 19: "Italians", 20: "Indians",
    21: "Incas", 22: "Magyars", 23: "Slavs", 24: "Portuguese", 25: "Ethiopians",
    26: "Malians", 27: "Berbers", 28: "Khmer", 29: "Malay", 30: "Burmese",
    31: "Vietnamese", 32: "Bulgarians", 33: "Tatars", 34: "Cumans", 35: "Lithuanians",
    36: "Burgundians", 37: "Sicilians", 38: "Poles", 39: "Bohemians", 40: "Dravidians",
    41: "Bengalis", 42: "Gurjaras", 43: "Romans", 44: "Armenians", 45: "Georgians",
}


def get_civ_name(civ_id: int) -> str:
    """Get civilization name from ID."""
    return CIV_NAMES.get(civ_id, f"Civ {civ_id}")


def format_time(seconds: Optional[int]) -> str:
    """Format seconds as MM:SS."""
    if seconds is None:
        return "N/A"
    mins = seconds // 60
    secs = seconds % 60
    return f"{mins}:{secs:02d}"


def winsorized_mean(values: list[float], pct: float = 0.1) -> Optional[float]:
    """Winsorized mean: clip tails to percentile boundaries before averaging."""
    clean = sorted(v for v in values if v is not None)
    if not clean:
        return None
    if len(clean) < 3:
        return statistics.mean(clean)

    k = int(len(clean) * pct)
    if k <= 0:
        return statistics.mean(clean)

    low = clean[k]
    high = clean[-k - 1]
    clipped = [min(max(v, low), high) for v in clean]
    return statistics.mean(clipped)


def single_match_report(parsed_match: dict, opponent_name: str) -> str:
    """Generate text report for a single parsed match.
    
    Shows: map, duration, civs, winner, age-up times, key stats.
    Format: clean text, suitable for terminal or overlay display.
    
    Args:
        parsed_match: Parsed replay dict from replay_parser
        opponent_name: Name of the opponent
        
    Returns:
        Formatted text report
    """
    match_id = parsed_match["match_id"]
    map_name = parsed_match["map_name"]
    duration = parsed_match["duration_secs"]
    game_type = parsed_match["game_type"]
    
    # Find opponent and self
    opponent = None
    self_player = None
    for player in parsed_match["players"]:
        if player["name"] == opponent_name:
            opponent = player
        else:
            self_player = player
    
    if not opponent:
        return f"⚠️  Opponent '{opponent_name}' not found in match {match_id}"
    
    # Build report
    lines = []
    lines.append(f"Match {match_id} • {map_name} • {format_time(duration)}")
    lines.append(f"Tipo: {game_type}")
    lines.append("")
    
    # Players
    if self_player:
        lines.append(f"Você: {get_civ_name(self_player['civ'])} • {'✓ Vitória' if self_player['winner'] else '✗ Derrota'}")
    lines.append(f"{opponent_name}: {get_civ_name(opponent['civ'])} • {'✓ Vitória' if opponent['winner'] else '✗ Derrota'}")
    lines.append(f"Rating: {opponent['rating']}")
    
    # Age-up times
    age_times = parsed_match.get("age_up_times", {}).get(opponent["user_id"])
    if age_times:
        lines.append("")
        lines.append("Tempos de avanço:")
        if age_times.get("feudal") is not None:
            lines.append(f"  Feudal: {format_time(age_times['feudal'])}")
        if age_times.get("castle") is not None:
            lines.append(f"  Castelo: {format_time(age_times['castle'])}")
        if age_times.get("imperial") is not None:
            lines.append(f"  Imperial: {format_time(age_times['imperial'])}")
    
    return "\n".join(lines)


def aggregate_scouting_report(parsed_matches: list[dict], opponent_name: str,
                                opponent_profile_id: int) -> str:
    """Generate aggregate scouting report from multiple parsed replays.
    
    MUST include:
    - Total matches analyzed (and note if team games were included due to n<5 1v1)
    - Civ preferences: most played civs with win rates, frequency
    - Map preferences: most played maps
    - Average age-up times (feudal, castle, imperial) with std dev
    - Win rate overall and by civ
    - Trends: are age-up times getting faster/slower over recent games?
    - Evolution: rating progression if available
    - Any patterns detectable from the data
    
    All deterministic — no AI interpretation. Just stats and numbers.
    
    Data source tagging rule:
    - If 1v1 sample >= 5: use only 1v1 data
    - If 1v1 sample < 5: include team game data, tag with "⚠️ Inclui dados TG (amostra 1v1: n=X)"
    
    Args:
        parsed_matches: List of parsed replay dicts
        opponent_name: Name of the opponent
        opponent_profile_id: Profile ID of opponent
        
    Returns:
        Formatted aggregate scouting report
    """
    if not parsed_matches:
        return "⚠️  Nenhum replay encontrado"
    
    # Separate 1v1 and team games
    matches_1v1 = [m for m in parsed_matches if m["game_type"] == "1v1"]
    matches_tg = [m for m in parsed_matches if m["game_type"] != "1v1"]
    
    # Determine data source
    use_1v1_only = len(matches_1v1) >= 5
    if use_1v1_only:
        data_source = matches_1v1
        source_tag = f"Fonte de dados: {len(matches_1v1)} partidas 1v1"
    else:
        data_source = parsed_matches
        source_tag = f"⚠️ Inclui dados TG (amostra 1v1: n={len(matches_1v1)})"
    
    total_matches = len(data_source)
    
    # Extract opponent data from each match
    opponent_data = []
    for match in data_source:
        for player in match["players"]:
            if player["user_id"] == opponent_profile_id:
                opponent_data.append({
                    "match_id": match["match_id"],
                    "civ": player["civ"],
                    "winner": player["winner"],
                    "rating": player["rating"],
                    "map": match["map_name"],
                    "game_type": match["game_type"],
                    "age_times": match.get("age_up_times", {}).get(opponent_profile_id),
                })
                break
    
    if not opponent_data:
        return "⚠️  Nenhum dado do oponente encontrado"
    
    # Calculate stats
    # Win rate
    wins = sum(1 for d in opponent_data if d["winner"])
    win_rate = (wins / total_matches) * 100 if total_matches > 0 else 0
    
    # Civ preferences
    civ_counter = Counter(d["civ"] for d in opponent_data)
    civ_wins = defaultdict(int)
    civ_total = defaultdict(int)
    for d in opponent_data:
        civ_total[d["civ"]] += 1
        if d["winner"]:
            civ_wins[d["civ"]] += 1
    
    civ_stats = []
    for civ_id, count in civ_counter.most_common():
        wr = (civ_wins[civ_id] / civ_total[civ_id]) * 100
        civ_stats.append((get_civ_name(civ_id), count, wr))
    
    # Map preferences
    map_counter = Counter(d["map"] for d in opponent_data)
    
    # Rating progression
    ratings = [d["rating"] for d in opponent_data if d["rating"] is not None]
    ratings.reverse()  # Oldest to newest
    
    # Age-up times
    feudal_times = []
    castle_times = []
    imperial_times = []
    
    for d in opponent_data:
        age_times = d.get("age_times")
        if age_times:
            if age_times.get("feudal") is not None:
                feudal_times.append(age_times["feudal"])
            if age_times.get("castle") is not None:
                castle_times.append(age_times["castle"])
            if age_times.get("imperial") is not None:
                imperial_times.append(age_times["imperial"])
    
    # Build report
    lines = []
    lines.append("=" * 60)
    lines.append(f"RELATÓRIO DE SCOUTING: {opponent_name}")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"Total de partidas analisadas: {total_matches}")
    lines.append(source_tag)
    lines.append("Agregações: média winsorizada (10%)")
    lines.append(f"1v1: {len(matches_1v1)} | Team Games: {len(matches_tg)}")
    lines.append("")
    
    # Win rate
    lines.append(f"📊 TAXA DE VITÓRIA GERAL: {win_rate:.1f}% ({wins}/{total_matches})")
    lines.append("")
    
    # Civ preferences
    lines.append("🏛️  PREFERÊNCIAS DE CIV:")
    for civ_name, count, wr in civ_stats[:5]:  # Top 5
        freq = (count / total_matches) * 100
        lines.append(f"  {civ_name}: {count}x ({freq:.0f}%) • WR {wr:.0f}%")
    lines.append("")
    
    # Map preferences
    lines.append("🗺️  MAPAS MAIS JOGADOS:")
    for map_name, count in map_counter.most_common(5):
        freq = (count / total_matches) * 100
        lines.append(f"  {map_name}: {count}x ({freq:.0f}%)")
    lines.append("")
    
    # Age-up times
    if feudal_times or castle_times or imperial_times:
        lines.append("⏱️  TEMPOS DE AVANÇO (média ± std):")
        
        if feudal_times:
            avg_f = winsorized_mean(feudal_times) or statistics.mean(feudal_times)
            std_f = statistics.stdev(feudal_times) if len(feudal_times) > 1 else 0
            lines.append(f"  Feudal: {format_time(int(avg_f))} ± {std_f:.0f}s (n={len(feudal_times)})")
        
        if castle_times:
            avg_c = winsorized_mean(castle_times) or statistics.mean(castle_times)
            std_c = statistics.stdev(castle_times) if len(castle_times) > 1 else 0
            lines.append(f"  Castelo: {format_time(int(avg_c))} ± {std_c:.0f}s (n={len(castle_times)})")
        
        if imperial_times:
            avg_i = winsorized_mean(imperial_times) or statistics.mean(imperial_times)
            std_i = statistics.stdev(imperial_times) if len(imperial_times) > 1 else 0
            lines.append(f"  Imperial: {format_time(int(avg_i))} ± {std_i:.0f}s (n={len(imperial_times)})")
        
        lines.append("")
    
    # Rating progression
    if len(ratings) >= 2:
        lines.append("📈 EVOLUÇÃO DE RATING:")
        lines.append(f"  Inicial: {ratings[0]} → Atual: {ratings[-1]} (Δ {ratings[-1] - ratings[0]:+d})")
        avg_rating = winsorized_mean(ratings) or statistics.mean(ratings)
        lines.append(f"  Média: {avg_rating:.0f} | Min: {min(ratings)} | Max: {max(ratings)}")
        lines.append("")
    
    # Trends (recent vs older age-up times)
    if len(feudal_times) >= 6:
        recent_feudal = feudal_times[-3:]
        older_feudal = feudal_times[:3]
        recent_avg = statistics.mean(recent_feudal)
        older_avg = statistics.mean(older_feudal)
        delta = recent_avg - older_avg
        
        lines.append("📉 TENDÊNCIAS:")
        lines.append(f"  Tempos de Feudal: {format_time(int(older_avg))} → {format_time(int(recent_avg))} (Δ {delta:+.0f}s)")
        if delta < -10:
            lines.append("  ⚡ Ficando mais rápido!")
        elif delta > 10:
            lines.append("  🐌 Ficando mais lento")
        else:
            lines.append("  ➡️  Estável")
        lines.append("")
    
    # Patterns
    lines.append("🔍 PADRÕES DETECTADOS:")
    
    # Check for civ loyalty
    if civ_stats:
        top_civ_name, top_civ_count, _ = civ_stats[0]
        loyalty = (top_civ_count / total_matches) * 100
        if loyalty >= 40:
            lines.append(f"  • Alta lealdade a {top_civ_name} ({loyalty:.0f}%)")
        elif len(civ_stats) >= 3:
            top3_freq = sum(c for _, c, _ in civ_stats[:3]) / total_matches
            if top3_freq < 0.60:  # If top 3 civs account for <60%, pool is diverse
                lines.append(f"  • Pool diverso de civs ({len(civ_stats)} diferentes)")
    
    # Check win rate by game type
    if len(matches_1v1) >= 3 and len(matches_tg) >= 3:
        wr_1v1 = sum(1 for m in matches_1v1 if any(p["user_id"] == opponent_profile_id and p["winner"] for p in m["players"])) / len(matches_1v1) * 100
        wr_tg = sum(1 for m in matches_tg if any(p["user_id"] == opponent_profile_id and p["winner"] for p in m["players"])) / len(matches_tg) * 100
        diff = abs(wr_1v1 - wr_tg)
        if diff >= 20:
            better_mode = "1v1" if wr_1v1 > wr_tg else "TG"
            lines.append(f"  • Performance melhor em {better_mode} ({wr_1v1:.0f}% vs {wr_tg:.0f}%)")
    
    lines.append("")
    lines.append("=" * 60)
    
    return "\n".join(lines)


if __name__ == "__main__":
    """Test with Urubu replays."""
    # Parse all Urubu replays and generate both reports
    opponent_id = 19012079
    opponent_name = "Urubu"
    
    parsed = parse_opponent_replays("replays", opponent_id)
    
    if not parsed:
        print("⚠️  Nenhum replay parseado com sucesso")
        exit(1)
    
    # Single match report (latest)
    print("=" * 60)
    print("RELATÓRIO DE PARTIDA ÚNICA (mais recente)")
    print("=" * 60)
    print(single_match_report(parsed[0], opponent_name))
    print()
    
    # Aggregate report
    print()
    print("=" * 60)
    print("RELATÓRIO AGREGADO DE SCOUTING")
    print("=" * 60)
    print(aggregate_scouting_report(parsed, opponent_name, opponent_id))
