"""PDF scouting reports for opponent analysis.

Two report types:
1. Single match report - overview of one 1v1 match
2. Aggregate scouting report - multi-page analysis across all matches
"""

import os
import tempfile
from collections import Counter, defaultdict
from datetime import datetime

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import seaborn as sns
from fpdf import FPDF

from .pdf_style import apply_style, COLORS, get_player_colors
from .scouting_report import CIV_NAMES, get_civ_name


# ─── Helpers ─────────────────────────────────────────────────


def fmt(seconds):
    """Format seconds as MM:SS."""
    if seconds is None or seconds == 0:
        return "--:--"
    m, s = divmod(int(seconds), 60)
    return f"{m}:{s:02d}"


def _save_fig(fig):
    """Save figure to temp PNG and close."""
    fd, path = tempfile.mkstemp(suffix=".png", prefix="scout_")
    os.close(fd)
    fig.savefig(path, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def _get_opponent_player(parsed_match: dict, opponent_profile_id: int = None) -> dict:
    """Extract opponent player data from parsed match.
    
    If opponent_profile_id provided, filter by user_id.
    Otherwise return first player.
    """
    players = parsed_match.get("players", [])
    if not players:
        return {}
    
    if opponent_profile_id:
        for p in players:
            if p.get("user_id") == opponent_profile_id:
                return p
    
    return players[0]


# ─── Data Aggregation ────────────────────────────────────────


def aggregate_stats(parsed_matches: list[dict], opponent_profile_id: int) -> dict:
    """Aggregate statistics across all matches for the opponent.
    
    Returns:
        Dict with aggregated stats:
        - total_matches: int
        - wins: int
        - losses: int
        - win_rate: float
        - civ_stats: {civ_id: {games, wins, losses, win_rate}}
        - map_stats: {map_name: count}
        - ratings: [(match_idx, rating), ...]
        - game_types: {type: count}
        - avg_rating: float
        - rating_trend: str ("up", "down", "stable")
        - favorite_civ: (civ_id, games_played)
    """
    total_matches = len(parsed_matches)
    wins = 0
    losses = 0
    civ_counter = Counter()
    civ_wins = defaultdict(int)
    civ_losses = defaultdict(int)
    map_counter = Counter()
    game_type_counter = Counter()
    ratings = []
    
    for idx, match in enumerate(parsed_matches):
        opponent = _get_opponent_player(match, opponent_profile_id)
        
        if not opponent:
            continue
        
        # Win/loss
        if opponent.get("winner"):
            wins += 1
            civ_wins[opponent["civ"]] += 1
        else:
            losses += 1
            civ_losses[opponent["civ"]] += 1
        
        # Civ frequency
        civ_counter[opponent["civ"]] += 1
        
        # Map frequency
        map_counter[match.get("map_name", "Unknown")] += 1
        
        # Game type
        game_type_counter[match.get("game_type", "Unknown")] += 1
        
        # Rating
        if opponent.get("rating"):
            ratings.append((idx, opponent["rating"]))
    
    # Calculate win rate
    win_rate = (wins / total_matches * 100) if total_matches > 0 else 0
    
    # Build civ stats
    civ_stats = {}
    for civ_id, games in civ_counter.items():
        civ_wins_count = civ_wins.get(civ_id, 0)
        civ_losses_count = civ_losses.get(civ_id, 0)
        civ_wr = (civ_wins_count / games * 100) if games > 0 else 0
        
        civ_stats[civ_id] = {
            "games": games,
            "wins": civ_wins_count,
            "losses": civ_losses_count,
            "win_rate": civ_wr,
        }
    
    # Average rating
    avg_rating = int(sum(r for _, r in ratings) / len(ratings)) if ratings else 0
    
    # Rating trend (compare first half vs second half)
    rating_trend = "stable"
    if len(ratings) >= 4:
        mid = len(ratings) // 2
        first_half_avg = sum(r for _, r in ratings[:mid]) / mid
        second_half_avg = sum(r for _, r in ratings[mid:]) / (len(ratings) - mid)
        diff = second_half_avg - first_half_avg
        
        if diff > 30:
            rating_trend = "up"
        elif diff < -30:
            rating_trend = "down"
    
    # Favorite civ
    favorite_civ = civ_counter.most_common(1)[0] if civ_counter else (0, 0)
    
    return {
        "total_matches": total_matches,
        "wins": wins,
        "losses": losses,
        "win_rate": win_rate,
        "civ_stats": civ_stats,
        "map_stats": dict(map_counter),
        "ratings": ratings,
        "game_types": dict(game_type_counter),
        "avg_rating": avg_rating,
        "rating_trend": rating_trend,
        "favorite_civ": favorite_civ,
    }


# ─── Chart Generators ────────────────────────────────────────


def chart_civ_distribution_pie(civ_stats: dict):
    """Pie chart: civ distribution."""
    apply_style()
    
    if not civ_stats:
        return None
    
    # Sort by games played
    sorted_civs = sorted(civ_stats.items(), key=lambda x: x[1]["games"], reverse=True)
    
    labels = [get_civ_name(civ_id) for civ_id, _ in sorted_civs]
    sizes = [stats["games"] for _, stats in sorted_civs]
    
    fig, ax = plt.subplots(figsize=(6, 4))
    
    # Use a nice color palette
    colors_palette = sns.color_palette("Set2", len(labels))
    
    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=labels,
        autopct='%1.1f%%',
        startangle=90,
        colors=colors_palette,
        textprops={'fontsize': 9, 'color': COLORS["text_primary"]}
    )
    
    # Make percentage text bold
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
        autotext.set_fontsize(8)
    
    ax.set_title("Civilization Distribution", fontsize=12, fontweight='bold', 
                 color=COLORS["text_primary"], pad=10)
    
    return _save_fig(fig)


def chart_civ_frequency_bars(civ_stats: dict):
    """Horizontal bar chart: civs played (frequency) with win rate color coding."""
    apply_style()
    
    if not civ_stats:
        return None
    
    # Build dataframe
    rows = []
    for civ_id, stats in civ_stats.items():
        rows.append({
            "Civilization": get_civ_name(civ_id),
            "Games": stats["games"],
            "Win Rate": stats["win_rate"],
        })
    
    df = pd.DataFrame(rows)
    df = df.sort_values("Games", ascending=True)  # Ascending for horizontal bars
    
    fig, ax = plt.subplots(figsize=(7, max(4, len(df) * 0.35)))
    
    # Color bars by win rate (green > 50%, red < 50%, gray = 50%)
    def get_bar_color(wr):
        if wr > 50:
            return COLORS["victory"]
        elif wr < 50:
            return COLORS["defeat"]
        else:
            return COLORS["text_secondary"]
    
    colors = [get_bar_color(wr) for wr in df["Win Rate"]]
    
    bars = ax.barh(df["Civilization"], df["Games"], color=colors, edgecolor="white", linewidth=0.5)
    
    # Add win rate labels on bars
    for i, (games, wr) in enumerate(zip(df["Games"], df["Win Rate"])):
        ax.text(games + 0.15, i, f'{wr:.0f}%', 
                va='center', fontsize=8, color=COLORS["text_secondary"])
    
    ax.set_xlabel("Games Played", fontsize=10, fontweight='bold')
    ax.set_title("Civilization Frequency & Win Rate", fontsize=12, fontweight='bold', pad=10)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    return _save_fig(fig)


def chart_map_frequency(map_stats: dict):
    """Bar chart: map frequency."""
    apply_style()
    
    if not map_stats:
        return None
    
    # Sort by frequency
    sorted_maps = sorted(map_stats.items(), key=lambda x: x[1], reverse=True)
    
    # Take top 10 maps
    sorted_maps = sorted_maps[:10]
    
    map_names = [name for name, _ in sorted_maps]
    counts = [count for _, count in sorted_maps]
    
    fig, ax = plt.subplots(figsize=(7, max(3.5, len(map_names) * 0.3)))
    
    bars = ax.barh(map_names, counts, color=COLORS["accent_orange"], 
                   edgecolor="white", linewidth=0.5)
    
    # Add count labels
    for i, count in enumerate(counts):
        ax.text(count + 0.1, i, str(count), 
                va='center', fontsize=8, color=COLORS["text_secondary"])
    
    ax.set_xlabel("Games Played", fontsize=10, fontweight='bold')
    ax.set_title("Map Distribution", fontsize=12, fontweight='bold', pad=10)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    return _save_fig(fig)


def chart_rating_evolution(ratings: list):
    """Line chart: rating evolution over matches."""
    apply_style()
    
    if not ratings or len(ratings) < 2:
        return None
    
    fig, ax = plt.subplots(figsize=(7, 3.5))
    
    indices = [idx for idx, _ in ratings]
    rating_values = [rating for _, rating in ratings]
    
    # Plot line
    ax.plot(indices, rating_values, marker='o', markersize=4, 
            linewidth=2, color=COLORS["accent_orange"], label="Rating")
    
    # Add trend line
    if len(ratings) >= 3:
        z = np.polyfit(indices, rating_values, 1)
        p = np.poly1d(z)
        ax.plot(indices, p(indices), "--", linewidth=1.5, 
                color=COLORS["text_secondary"], alpha=0.7, label="Trend")
    
    ax.set_xlabel("Match Number (Recent → Older)", fontsize=10, fontweight='bold')
    ax.set_ylabel("Rating", fontsize=10, fontweight='bold')
    ax.set_title("Rating Evolution", fontsize=12, fontweight='bold', pad=10)
    ax.legend(loc='best', frameon=False)
    ax.grid(axis='y', alpha=0.3)
    
    return _save_fig(fig)


# ─── PDF Generation ──────────────────────────────────────────


def generate_match_pdf(parsed_match: dict, opponent_name: str, output_path: str) -> str:
    """Generate PDF for a single 1v1 match from parsed replay data.
    
    Args:
        parsed_match: Parsed replay dict from replay_parser
        opponent_name: Name of the opponent
        output_path: Path to save PDF
        
    Returns:
        Path to generated PDF
    """
    # Only generate for 1v1 matches
    if parsed_match.get("game_type") != "1v1":
        raise ValueError(f"Only 1v1 matches supported, got: {parsed_match.get('game_type')}")
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(False)
    
    # Add Unicode font support
    pdf.add_font("DejaVu", "", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", uni=True)
    pdf.add_font("DejaVu", "B", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", uni=True)
    pdf.add_font("DejaVu", "I", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf", uni=True)
    
    # Header
    pdf.set_font("DejaVu", "B", 18)
    pdf.set_text_color(44, 62, 80)  # COLORS["text_primary"]
    pdf.cell(0, 12, f"MATCH REPORT: {opponent_name}", ln=True, align="C")
    
    pdf.set_font("DejaVu", "", 10)
    pdf.set_text_color(127, 140, 141)  # COLORS["text_secondary"]
    pdf.cell(0, 6, f"Match ID: {parsed_match.get('match_id', 'Unknown')}", ln=True, align="C")
    
    pdf.ln(8)
    
    # Match overview box
    pdf.set_font("DejaVu", "B", 11)
    pdf.set_text_color(44, 62, 80)
    pdf.cell(0, 8, "Match Overview", ln=True)
    
    pdf.set_font("DejaVu", "", 10)
    pdf.set_text_color(127, 140, 141)
    
    # Map and duration
    map_name = parsed_match.get("map_name", "Unknown")
    duration = fmt(parsed_match.get("duration_secs", 0))
    completed = "Yes" if parsed_match.get("completed") else "No"
    
    pdf.cell(0, 6, f"Map: {map_name}", ln=True)
    pdf.cell(0, 6, f"Duration: {duration}", ln=True)
    pdf.cell(0, 6, f"Completed: {completed}", ln=True)
    
    pdf.ln(6)
    
    # Players
    pdf.set_font("DejaVu", "B", 11)
    pdf.set_text_color(44, 62, 80)
    pdf.cell(0, 8, "Players", ln=True)
    
    players = parsed_match.get("players", [])
    
    for i, player in enumerate(players):
        pdf.set_font("DejaVu", "B", 10)
        
        # Winner gets green, loser gets red
        if player.get("winner"):
            pdf.set_text_color(39, 174, 96)  # COLORS["victory"]
            status = "WINNER"
        else:
            pdf.set_text_color(231, 76, 60)  # COLORS["defeat"]
            status = "LOSER"
        
        player_name = player.get("name", "Unknown")
        civ_name = get_civ_name(player.get("civ", 0))
        rating = player.get("rating")
        rating_str = f" ({rating} ELO)" if rating else ""
        
        pdf.cell(0, 6, f"{status}: {player_name}{rating_str}", ln=True)
        
        pdf.set_font("DejaVu", "", 9)
        pdf.set_text_color(127, 140, 141)
        pdf.cell(0, 5, f"   Civilization: {civ_name}", ln=True)
        
        pdf.ln(2)
    
    # Footer
    pdf.set_y(-30)
    pdf.set_font("DejaVu", "I", 8)
    pdf.set_text_color(189, 195, 199)
    pdf.cell(0, 6, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align="C")
    pdf.cell(0, 6, "Agelytics - Age of Empires II Analytics", ln=True, align="C")
    
    pdf.output(output_path)
    return output_path


def generate_scouting_pdf(parsed_matches: list[dict], opponent_name: str, 
                           opponent_profile_id: int, output_path: str) -> str:
    """Generate aggregate scouting PDF from multiple parsed replays.
    
    Data source rule:
    - If 1v1 sample >= 5: use only 1v1
    - If 1v1 sample < 5: use all ranked + tag warning
    
    Args:
        parsed_matches: List of parsed replay dicts
        opponent_name: Name of the opponent
        opponent_profile_id: Profile ID of the opponent
        output_path: Path to save PDF
        
    Returns:
        Path to generated PDF
    """
    # Data source filtering
    matches_1v1 = [m for m in parsed_matches if m.get("game_type") == "1v1"]
    
    if len(matches_1v1) >= 5:
        data_source = "1v1 only"
        matches_to_use = matches_1v1
        include_tg_warning = False
    else:
        data_source = "All ranked matches (includes TG)"
        matches_to_use = parsed_matches
        include_tg_warning = True
    
    if not matches_to_use:
        raise ValueError("No matches to analyze")
    
    # Aggregate stats
    stats = aggregate_stats(matches_to_use, opponent_profile_id)
    
    # Generate charts
    chart_paths = {}
    
    chart_paths["civ_pie"] = chart_civ_distribution_pie(stats["civ_stats"])
    chart_paths["civ_bars"] = chart_civ_frequency_bars(stats["civ_stats"])
    chart_paths["map_freq"] = chart_map_frequency(stats["map_stats"])
    chart_paths["rating_evo"] = chart_rating_evolution(stats["ratings"])
    
    # Create PDF
    pdf = FPDF()
    pdf.set_auto_page_break(False)
    
    # Add Unicode font support
    pdf.add_font("DejaVu", "", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", uni=True)
    pdf.add_font("DejaVu", "B", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", uni=True)
    pdf.add_font("DejaVu", "I", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf", uni=True)
    
    # ─── Page 1: Overview Dashboard ─────────────────────────
    
    pdf.add_page()
    
    # Header
    pdf.set_font("DejaVu", "B", 20)
    pdf.set_text_color(44, 62, 80)
    pdf.cell(0, 14, f"SCOUTING REPORT: {opponent_name}", ln=True, align="C")
    
    pdf.set_font("DejaVu", "", 10)
    pdf.set_text_color(127, 140, 141)
    pdf.cell(0, 6, f"Profile ID: {opponent_profile_id} | Total Matches: {stats['total_matches']}", 
             ln=True, align="C")
    
    # Data source tag
    if include_tg_warning:
        pdf.set_font("DejaVu", "B", 9)
        pdf.set_text_color(243, 156, 18)  # COLORS["warning"]
        pdf.cell(0, 6, "WARNING: Includes TG data (insufficient 1v1 sample)", ln=True, align="C")
    
    pdf.ln(8)
    
    # KPI boxes
    pdf.set_font("DejaVu", "B", 10)
    pdf.set_text_color(44, 62, 80)
    
    # Row 1: Win Rate, Matches Played
    pdf.cell(95, 8, "Win Rate", border=1, align="C")
    pdf.cell(95, 8, "Matches Played", border=1, align="C", ln=True)
    
    pdf.set_font("DejaVu", "", 18)
    pdf.set_text_color(39, 174, 96) if stats["win_rate"] >= 50 else pdf.set_text_color(231, 76, 60)
    pdf.cell(95, 12, f"{stats['win_rate']:.1f}%", border=1, align="C")
    
    pdf.set_text_color(44, 62, 80)
    pdf.cell(95, 12, f"{stats['total_matches']}", border=1, align="C", ln=True)
    
    pdf.ln(4)
    
    # Row 2: Favorite Civ, Rating Trend
    pdf.set_font("DejaVu", "B", 10)
    pdf.cell(95, 8, "Favorite Civilization", border=1, align="C")
    pdf.cell(95, 8, "Rating Trend", border=1, align="C", ln=True)
    
    pdf.set_font("DejaVu", "", 12)
    fav_civ_name = get_civ_name(stats["favorite_civ"][0])
    fav_civ_games = stats["favorite_civ"][1]
    pdf.cell(95, 12, f"{fav_civ_name} ({fav_civ_games} games)", border=1, align="C")
    
    # Rating trend
    trend_map = {"up": "^ Rising", "down": "v Falling", "stable": "-> Stable"}
    trend_text = trend_map.get(stats["rating_trend"], "-")
    pdf.cell(95, 12, trend_text, border=1, align="C", ln=True)
    
    pdf.ln(8)
    
    # Pie chart: Civ distribution
    if chart_paths["civ_pie"]:
        pdf.image(chart_paths["civ_pie"], x=30, y=None, w=150)
    
    # Footer
    pdf.set_y(-30)
    pdf.set_font("DejaVu", "I", 8)
    pdf.set_text_color(189, 195, 199)
    pdf.cell(0, 6, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align="C")
    pdf.cell(0, 6, "Agelytics — Opponent Scouting Report", ln=True, align="C")
    
    # ─── Page 2: Civ Analysis ───────────────────────────────
    
    pdf.add_page()
    
    pdf.set_font("DejaVu", "B", 16)
    pdf.set_text_color(44, 62, 80)
    pdf.cell(0, 12, "Civilization Analysis", ln=True, align="C")
    
    pdf.ln(6)
    
    # Bar chart
    if chart_paths["civ_bars"]:
        pdf.image(chart_paths["civ_bars"], x=15, y=None, w=180)
    
    pdf.ln(6)
    
    # Table: civ name | games | wins | losses | win rate
    pdf.set_font("DejaVu", "B", 9)
    pdf.set_text_color(44, 62, 80)
    
    col_widths = [70, 25, 25, 25, 35]
    pdf.cell(col_widths[0], 8, "Civilization", border=1, align="C")
    pdf.cell(col_widths[1], 8, "Games", border=1, align="C")
    pdf.cell(col_widths[2], 8, "Wins", border=1, align="C")
    pdf.cell(col_widths[3], 8, "Losses", border=1, align="C")
    pdf.cell(col_widths[4], 8, "Win Rate", border=1, align="C", ln=True)
    
    pdf.set_font("DejaVu", "", 8)
    
    # Sort civs by games played
    sorted_civs = sorted(stats["civ_stats"].items(), 
                         key=lambda x: x[1]["games"], reverse=True)
    
    for civ_id, civ_data in sorted_civs:
        civ_name = get_civ_name(civ_id)
        games = civ_data["games"]
        wins = civ_data["wins"]
        losses = civ_data["losses"]
        wr = civ_data["win_rate"]
        
        pdf.cell(col_widths[0], 7, civ_name, border=1)
        pdf.cell(col_widths[1], 7, str(games), border=1, align="C")
        pdf.cell(col_widths[2], 7, str(wins), border=1, align="C")
        pdf.cell(col_widths[3], 7, str(losses), border=1, align="C")
        pdf.cell(col_widths[4], 7, f"{wr:.1f}%", border=1, align="C", ln=True)
    
    # Footer
    pdf.set_y(-30)
    pdf.set_font("DejaVu", "I", 8)
    pdf.set_text_color(189, 195, 199)
    pdf.cell(0, 6, f"Data source: {data_source}", ln=True, align="C")
    pdf.cell(0, 6, f"Page 2 of 4", ln=True, align="C")
    
    # ─── Page 3: Maps & Trends ───────────────────────────────
    
    pdf.add_page()
    
    pdf.set_font("DejaVu", "B", 16)
    pdf.set_text_color(44, 62, 80)
    pdf.cell(0, 12, "Maps & Performance Trends", ln=True, align="C")
    
    pdf.ln(4)
    
    # Map frequency chart
    if chart_paths["map_freq"]:
        pdf.image(chart_paths["map_freq"], x=15, y=None, w=180)
    
    pdf.ln(6)
    
    # Rating evolution chart
    if chart_paths["rating_evo"]:
        pdf.image(chart_paths["rating_evo"], x=15, y=None, w=180)
    else:
        pdf.set_font("DejaVu", "I", 10)
        pdf.set_text_color(127, 140, 141)
        pdf.cell(0, 10, "Not enough rating data to show trend", ln=True, align="C")
    
    # Footer
    pdf.set_y(-30)
    pdf.set_font("DejaVu", "I", 8)
    pdf.set_text_color(189, 195, 199)
    pdf.cell(0, 6, f"Data source: {data_source}", ln=True, align="C")
    pdf.cell(0, 6, f"Page 3 of 4", ln=True, align="C")
    
    # ─── Page 4: Summary & Patterns ──────────────────────────
    
    pdf.add_page()
    
    pdf.set_font("DejaVu", "B", 16)
    pdf.set_text_color(44, 62, 80)
    pdf.cell(0, 12, "Summary & Key Takeaways", ln=True, align="C")
    
    pdf.ln(6)
    
    # Detected patterns
    pdf.set_font("DejaVu", "B", 12)
    pdf.set_text_color(44, 62, 80)
    pdf.cell(0, 10, "Detected Patterns", ln=True)
    
    pdf.set_font("DejaVu", "", 9)
    pdf.set_text_color(44, 62, 80)
    
    patterns = []
    
    # Civ loyalty check
    total_civs_played = len(stats["civ_stats"])
    if total_civs_played <= 3:
        patterns.append(f"• CIV LOYALTY: Plays only {total_civs_played} civilization(s) — predictable civ pool")
    elif total_civs_played >= 8:
        patterns.append(f"• DIVERSE POOL: Plays {total_civs_played} different civilizations — adaptable")
    else:
        patterns.append(f"• MODERATE VARIETY: Plays {total_civs_played} civilizations")
    
    # Favorite civ dominance
    fav_civ_pct = (stats["favorite_civ"][1] / stats["total_matches"] * 100)
    if fav_civ_pct >= 40:
        patterns.append(f"• COMFORT PICK: {fav_civ_name} is heavily favored ({fav_civ_pct:.0f}% of games)")
    
    # Win rate analysis
    if stats["win_rate"] >= 60:
        patterns.append(f"• STRONG PLAYER: {stats['win_rate']:.1f}% win rate")
    elif stats["win_rate"] <= 40:
        patterns.append(f"• STRUGGLING: {stats['win_rate']:.1f}% win rate — exploitable")
    
    # Rating trend
    if stats["rating_trend"] == "up":
        patterns.append("• IMPROVING: Rating trending upward")
    elif stats["rating_trend"] == "down":
        patterns.append("• DECLINING: Rating trending downward")
    
    # Game type mix (if TG data included)
    if include_tg_warning:
        game_types = stats["game_types"]
        if "TG" in game_types or "Team Game" in game_types:
            tg_count = game_types.get("TG", 0) + game_types.get("Team Game", 0)
            patterns.append(f"• TEAM GAME DATA: {tg_count} TG matches included in analysis")
    
    # Print patterns
    for pattern in patterns:
        pdf.multi_cell(0, 5, pattern)
        pdf.ln(1)
    
    pdf.ln(4)
    
    # Key takeaways
    pdf.set_font("DejaVu", "B", 12)
    pdf.set_text_color(44, 62, 80)
    pdf.cell(0, 10, "Key Takeaways", ln=True)
    
    pdf.set_font("DejaVu", "", 9)
    
    takeaways = []
    
    # Build recommendation based on data
    if fav_civ_pct >= 40:
        fav_wr = stats["civ_stats"][stats["favorite_civ"][0]]["win_rate"]
        if fav_wr >= 60:
            takeaways.append(f"• Expect {fav_civ_name} — they excel with it ({fav_wr:.0f}% WR)")
        elif fav_wr <= 40:
            takeaways.append(f"• Expect {fav_civ_name} — but they struggle ({fav_wr:.0f}% WR)")
    
    # Map preparation
    top_maps = sorted(stats["map_stats"].items(), key=lambda x: x[1], reverse=True)[:3]
    map_list = ", ".join([m[0] for m in top_maps])
    takeaways.append(f"• Most played maps: {map_list}")
    
    # Sample size note
    takeaways.append(f"• Analysis based on {stats['total_matches']} matches")
    
    # Print takeaways
    for takeaway in takeaways:
        pdf.multi_cell(0, 5, takeaway)
        pdf.ln(1)
    
    pdf.ln(4)
    
    # Data source disclaimer
    pdf.set_font("DejaVu", "I", 9)
    pdf.set_text_color(127, 140, 141)
    pdf.multi_cell(0, 5, 
        f"Data source: {data_source}. Statistics are deterministic and based on available "
        f"replay data. Player behavior may vary in different contexts."
    )
    
    # Footer
    pdf.set_y(-30)
    pdf.set_font("DejaVu", "I", 8)
    pdf.set_text_color(189, 195, 199)
    pdf.cell(0, 6, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align="C")
    pdf.cell(0, 6, f"Page 4 of 4", ln=True, align="C")
    
    # Save PDF
    pdf.output(output_path)
    
    # Cleanup temp chart files
    for path in chart_paths.values():
        if path and os.path.exists(path):
            os.remove(path)
    
    return output_path


# ─── Test Block ──────────────────────────────────────────────


if __name__ == "__main__":
    from .replay_parser import parse_opponent_replays
    
    opponent_id = 19012079
    opponent_name = "Urubu"
    
    print(f"Parsing replays for {opponent_name} (ID: {opponent_id})...")
    parsed = parse_opponent_replays("replays", opponent_id)
    
    if not parsed:
        print("❌ No replays found or parsed")
        exit(1)
    
    # Debug: print game types
    game_types = set(m.get("game_type", "Unknown") for m in parsed)
    print(f"Game types found: {game_types}")
    
    # Only generate 1v1 match PDF if we have 1v1 matches
    matches_1v1 = [m for m in parsed if m.get("game_type") == "1v1"]
    
    if matches_1v1:
        print(f"\n📄 Generating single match PDF (1v1)...")
        try:
            path1 = generate_match_pdf(matches_1v1[0], opponent_name, "/tmp/urubu_match.pdf")
            print(f"✅ Match PDF: {path1}")
        except Exception as e:
            print(f"⚠️  Match PDF failed: {e}")
    else:
        print("⚠️  No 1v1 matches found, skipping single match PDF")
    
    # Aggregate scouting PDF (always)
    print(f"\n📊 Generating aggregate scouting PDF...")
    try:
        path2 = generate_scouting_pdf(parsed, opponent_name, opponent_id, "/tmp/urubu_scouting.pdf")
        print(f"✅ Scouting PDF: {path2}")
    except Exception as e:
        print(f"❌ Scouting PDF failed: {e}")
        import traceback
        traceback.print_exc()
