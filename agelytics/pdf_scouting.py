"""Rich PDF scouting reports with small multiples and KPI cards.

Uses pre-computed match statistics to generate comprehensive 4-page opponent analysis.
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


# ─── Helpers ─────────────────────────────────────────────────


def fmt(seconds):
    """Format seconds as MM:SS."""
    if seconds is None or seconds == 0 or pd.isna(seconds):
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


def safe_mean(values):
    """Calculate mean, filtering out None/NaN/0."""
    valid = [v for v in values if v is not None and not pd.isna(v) and v != 0]
    return sum(valid) / len(valid) if valid else None


def safe_avg_seconds(values):
    """Calculate average for time values in seconds."""
    avg = safe_mean(values)
    return fmt(avg) if avg else "--:--"


# ─── Player Extraction ────────────────────────────────────────


def extract_player_stats(match_data: dict, player_name: str) -> dict:
    """Flatten multi-player match data into a single-player view.

    Converts the parser's per-match dict (which contains data for all
    players) into the flat dict expected by the chart/KPI helpers.
    """
    # Find the player in the players list
    player_info = None
    for p in match_data.get("players", []):
        if p.get("name") == player_name:
            player_info = p
            break

    if player_info is None:
        return None

    # Age-up times for this player
    age_times = {}
    for au in match_data.get("age_ups", []):
        if au.get("player") == player_name:
            age_label = au.get("age", "")
            if "Feudal" in age_label:
                age_times["feudal"] = au["timestamp_secs"]
            elif "Castle" in age_label:
                age_times["castle"] = au["timestamp_secs"]
            elif "Imperial" in age_label:
                age_times["imperial"] = au["timestamp_secs"]

    # TC idle: may be a dict keyed by player or a flat number
    tc_idle_raw = match_data.get("tc_idle")
    if isinstance(tc_idle_raw, dict):
        tc_idle_val = tc_idle_raw.get(player_name, 0)
    elif tc_idle_raw is not None:
        tc_idle_val = tc_idle_raw
    else:
        tc_idle_val = 0

    # TC idle percent from metrics
    metrics = match_data.get("metrics", {})
    if isinstance(metrics, dict) and player_name in metrics:
        tc_idle_pct = metrics[player_name].get("tc_idle_percent")
    else:
        tc_idle_pct = None

    # Unit production for this player
    unit_prod = match_data.get("unit_production", {})
    if isinstance(unit_prod, dict) and player_name in unit_prod:
        units = unit_prod[player_name]
    else:
        units = unit_prod if not any(isinstance(v, dict) for v in unit_prod.values()) else {}

    # Opening for this player
    openings = match_data.get("openings", {})
    if isinstance(openings, dict) and player_name in openings:
        opening = openings[player_name]
    elif isinstance(openings, str):
        opening = openings
    else:
        opening = None

    return {
        "civ": player_info.get("civ_name"),
        "winner": player_info.get("winner", False),
        "eapm": player_info.get("eapm", 0),
        "elo": player_info.get("elo"),
        "feudal": age_times.get("feudal"),
        "castle": age_times.get("castle"),
        "imperial": age_times.get("imperial"),
        "tc_idle": tc_idle_val,
        "tc_idle_percent": tc_idle_pct,
        "duration": match_data.get("duration_secs", 0),
        "map": match_data.get("map_name", "Unknown"),
        "diplomacy": match_data.get("diplomacy"),
        "played_at": match_data.get("played_at"),
        "units": units,
        "opening": opening,
    }


# ─── Data Filtering & Processing ─────────────────────────────


def filter_stats(stats: list[dict]) -> tuple[list[dict], bool]:
    """Filter stats according to data source rule.
    
    Returns:
        (filtered_stats, tg_warning_flag)
    """
    stats_1v1 = [s for s in stats if s.get("diplomacy") == "1v1"]
    
    if len(stats_1v1) >= 5:
        return stats_1v1, False
    else:
        return stats, True


# ─── KPI Card Drawing ────────────────────────────────────────


def draw_kpi_card(pdf, x, y, w, h, label, value, color_rgb):
    """Draw a colored KPI card with big number."""
    # Draw colored box
    pdf.set_fill_color(*color_rgb)
    pdf.rect(x, y, w, h, 'F')
    
    # Draw white number
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("DejaVu", "B", 16)
    pdf.set_xy(x, y + h/2 - 5)
    pdf.cell(w, 6, str(value), align='C')
    
    # Draw label below
    pdf.set_text_color(44, 62, 80)
    pdf.set_font("DejaVu", "", 8)
    pdf.set_xy(x, y + h + 1)
    pdf.cell(w, 4, label, align='C')


# ─── Chart Generators ────────────────────────────────────────


def chart_civ_pie(stats: list[dict]):
    """Pie chart: civ distribution."""
    apply_style()
    
    civ_counts = Counter(s["civ"] for s in stats if s.get("civ"))
    
    if not civ_counts:
        return None
    
    labels = list(civ_counts.keys())
    sizes = list(civ_counts.values())
    
    fig, ax = plt.subplots(figsize=(6, 4))
    
    colors_palette = sns.color_palette("Set2", len(labels))
    
    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=labels,
        autopct='%1.1f%%',
        startangle=90,
        colors=colors_palette,
        textprops={'fontsize': 9, 'color': COLORS["text_primary"]}
    )
    
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
        autotext.set_fontsize(8)
    
    ax.set_title("Civilization Distribution", fontsize=12, fontweight='bold', 
                 color=COLORS["text_primary"], pad=10)
    
    return _save_fig(fig)


def chart_performance_grid(stats: list[dict]):
    """2x2 grid: age-ups, TC idle, eAPM, duration."""
    apply_style()
    
    fig, axes = plt.subplots(2, 2, figsize=(10, 7))
    
    # Top-left: Age-up times
    ax = axes[0, 0]
    
    indices = list(range(len(stats)))
    feudal_times = [s.get("feudal") for s in stats]
    castle_times = [s.get("castle") for s in stats]
    imperial_times = [s.get("imperial") for s in stats]
    diplomacies = [s.get("diplomacy", "1v1") for s in stats]
    
    # Plot lines with trend — use different markers for 1v1 vs TG
    for times, label, color in [
        (feudal_times, "Feudal", "blue"),
        (castle_times, "Castle", "orange"),
        (imperial_times, "Imperial", "green")
    ]:
        valid_idx = [i for i, t in enumerate(times) if t is not None and t != 0]
        valid_times = [times[i] for i in valid_idx]
        valid_markers = ['o' if diplomacies[i] == '1v1' else 'D' for i in valid_idx]
        
        if valid_times:
            # Plot 1v1 and TG separately for different markers
            for marker, mlabel in [('o', '1v1'), ('D', 'TG')]:
                m_idx = [vi for vi, vm in zip(valid_idx, valid_markers) if vm == marker]
                m_times = [valid_times[j] for j, vm in enumerate(valid_markers) if vm == marker]
                if m_times:
                    ax.scatter(m_idx, m_times, alpha=0.6, s=30, color=color, marker=marker)
            
            # Trend line
            if len(valid_times) >= 2:
                z = np.polyfit(valid_idx, valid_times, 1)
                p = np.poly1d(z)
                ax.plot(valid_idx, p(valid_idx), "--", alpha=0.5, color=color, linewidth=1)
    
    # Custom legend
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', markerfacecolor='blue', markersize=6, label='Feudal'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='orange', markersize=6, label='Castle'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='green', markersize=6, label='Imperial'),
        Line2D([0], [0], marker='D', color='w', markerfacecolor='gray', markersize=6, label='TG match'),
    ]
    ax.legend(handles=legend_elements, loc='best', fontsize=6)
    
    ax.set_xlabel("Match Index")
    ax.set_ylabel("Time (seconds)")
    ax.set_title("Age-up Times (◆=TG)", fontsize=10, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    ax.invert_yaxis()  # Faster at bottom
    
    # Top-right: TC idle per match
    ax = axes[0, 1]
    
    tc_idle = [s.get("tc_idle", 0) for s in stats]
    winners = [s.get("winner", False) for s in stats]
    diplomacies = [s.get("diplomacy", "1v1") for s in stats]
    colors = [COLORS["victory"] if w else COLORS["defeat"] for w in winners]
    
    bars = ax.bar(indices, tc_idle, color=colors, edgecolor='white', linewidth=0.5)
    # Mark TG matches with a diamond marker on top
    for i, (tc, dip) in enumerate(zip(tc_idle, diplomacies)):
        if dip == "TG":
            ax.plot(i, tc + max(tc_idle) * 0.03, marker='D', color='gray', markersize=4, alpha=0.7)
    ax.set_xlabel("Match Index")
    ax.set_ylabel("TC Idle (seconds)")
    ax.set_title("TC Idle Time per Match (◆=TG)", fontsize=10, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    
    # Bottom-left: eAPM per match with rolling average
    ax = axes[1, 0]
    
    eapm = [s.get("eapm", 0) for s in stats]
    
    # Plot with different markers for 1v1 vs TG
    for i, (e, dip) in enumerate(zip(eapm, diplomacies)):
        marker = 'o' if dip == '1v1' else 'D'
        ax.plot(i, e, marker=marker, markersize=4, color=COLORS["accent_orange"], alpha=0.6)
    ax.plot(indices, eapm, linewidth=1, color=COLORS["accent_orange"], alpha=0.3)
    
    # Rolling average
    if len(eapm) >= 5:
        rolling = pd.Series(eapm).rolling(window=5, min_periods=1).mean()
        ax.plot(indices, rolling, linewidth=2, color=COLORS["text_primary"], 
                label="Rolling Avg (5)")
    
    ax.set_xlabel("Match Index")
    ax.set_ylabel("eAPM")
    ax.set_title("eAPM per Match", fontsize=10, fontweight='bold')
    ax.legend(loc='best', fontsize=7)
    ax.grid(axis='y', alpha=0.3)
    
    # Bottom-right: Game duration per match
    ax = axes[1, 1]
    
    durations = [s.get("duration", 0) / 60 for s in stats]  # Convert to minutes
    
    bars = ax.bar(indices, durations, color=colors, edgecolor='white', linewidth=0.5)
    # Mark TG matches with diamond
    for i, (dur, dip) in enumerate(zip(durations, diplomacies)):
        if dip == "TG":
            ax.plot(i, dur + max(durations) * 0.03, marker='D', color='gray', markersize=4, alpha=0.7)
    ax.set_xlabel("Match Index")
    ax.set_ylabel("Duration (minutes)")
    ax.set_title("Game Duration per Match (◆=TG)", fontsize=10, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    return _save_fig(fig)


def chart_army_strategy_grid(stats: list[dict]):
    """2x2 grid: civ WR, openings, map WR, unit heatmap."""
    apply_style()
    
    fig, axes = plt.subplots(2, 2, figsize=(10, 7))
    
    # Top-left: Civ win rate
    ax = axes[0, 0]
    
    civ_data = defaultdict(lambda: {"wins": 0, "total": 0})
    
    for s in stats:
        civ = s.get("civ")
        if not civ:
            continue
        civ_data[civ]["total"] += 1
        if s.get("winner"):
            civ_data[civ]["wins"] += 1
    
    civ_wr = {civ: (data["wins"] / data["total"] * 100) if data["total"] > 0 else 0 
              for civ, data in civ_data.items()}
    
    sorted_civs = sorted(civ_wr.items(), key=lambda x: x[1], reverse=False)  # Ascending for horizontal
    
    civs = [c[0] for c in sorted_civs]
    wrs = [c[1] for c in sorted_civs]
    colors_civ = [COLORS["victory"] if wr > 50 else COLORS["defeat"] for wr in wrs]
    
    ax.barh(civs, wrs, color=colors_civ, edgecolor='white', linewidth=0.5)
    ax.set_xlabel("Win Rate (%)")
    ax.set_title("Civilization Win Rate", fontsize=10, fontweight='bold')
    ax.grid(axis='x', alpha=0.3)
    
    # Top-right: Opening tendencies
    ax = axes[0, 1]
    
    openings = [s.get("opening") for s in stats if s.get("opening") and s.get("opening") != "Unknown"]
    opening_counts = Counter(openings)
    
    if opening_counts:
        sorted_openings = sorted(opening_counts.items(), key=lambda x: x[1], reverse=False)
        
        op_names = [o[0][:20] for o in sorted_openings]  # Truncate long names
        op_counts = [o[1] for o in sorted_openings]
        
        ax.barh(op_names, op_counts, color=COLORS["accent_orange"], 
                edgecolor='white', linewidth=0.5)
        ax.set_xlabel("Count")
        ax.set_title("Opening Strategies", fontsize=10, fontweight='bold')
        ax.grid(axis='x', alpha=0.3)
    else:
        ax.text(0.5, 0.5, "No opening data", ha='center', va='center', 
                transform=ax.transAxes, fontsize=9, color=COLORS["text_secondary"])
        ax.set_xticks([])
        ax.set_yticks([])
    
    # Bottom-left: Map win rate
    ax = axes[1, 0]
    
    map_data = defaultdict(lambda: {"wins": 0, "total": 0})
    
    for s in stats:
        map_name = s.get("map", "Unknown")
        map_data[map_name]["total"] += 1
        if s.get("winner"):
            map_data[map_name]["wins"] += 1
    
    map_wr = {map_name: (data["wins"] / data["total"] * 100) if data["total"] > 0 else 0 
              for map_name, data in map_data.items()}
    
    sorted_maps = sorted(map_wr.items(), key=lambda x: x[1], reverse=False)
    
    maps = [m[0][:15] for m in sorted_maps]  # Truncate map names
    map_wrs = [m[1] for m in sorted_maps]
    colors_map = [COLORS["victory"] if wr > 50 else COLORS["defeat"] for wr in map_wrs]
    
    ax.barh(maps, map_wrs, color=colors_map, edgecolor='white', linewidth=0.5)
    ax.set_xlabel("Win Rate (%)")
    ax.set_title("Map Win Rate", fontsize=10, fontweight='bold')
    ax.grid(axis='x', alpha=0.3)
    
    # Bottom-right: Unit composition heatmap (top 5 units, last 10 matches)
    ax = axes[1, 1]
    
    # Collect all units (excluding Villager)
    unit_totals = Counter()
    
    for s in stats:
        units = s.get("units", {})
        for unit, count in units.items():
            if unit != "Villager":
                unit_totals[unit] += count
    
    # Top 5 units
    top_units = [u[0] for u in unit_totals.most_common(5)]
    
    if top_units and len(stats) > 0:
        # Last 10 matches
        recent_stats = stats[-10:]
        
        # Build matrix
        matrix = []
        for unit in top_units:
            row = [s.get("units", {}).get(unit, 0) for s in recent_stats]
            matrix.append(row)
        
        # Plot heatmap
        sns.heatmap(matrix, ax=ax, cmap="YlOrRd", annot=True, fmt='g', 
                    cbar_kws={'label': 'Count'}, linewidths=0.5,
                    yticklabels=[u[:10] for u in top_units],
                    xticklabels=[f"M{i+1}" for i in range(len(recent_stats))],
                    annot_kws={'fontsize': 7})
        
        ax.set_title("Unit Composition (Last 10)", fontsize=10, fontweight='bold')
        ax.set_xlabel("Match")
        ax.set_ylabel("Unit Type")
    else:
        ax.text(0.5, 0.5, "No unit data", ha='center', va='center', 
                transform=ax.transAxes, fontsize=9, color=COLORS["text_secondary"])
        ax.set_xticks([])
        ax.set_yticks([])
    
    plt.tight_layout()
    return _save_fig(fig)


def chart_elo_evolution(stats: list[dict]):
    """Full-width ELO evolution with trend line."""
    apply_style()
    
    elos = [s.get("elo") for s in stats if s.get("elo")]
    
    if len(elos) < 2:
        return None
    
    fig, ax = plt.subplots(figsize=(8, 3.5))
    
    indices = list(range(len(elos)))
    
    ax.plot(indices, elos, marker='o', markersize=5, linewidth=2, 
            color=COLORS["accent_orange"], label="ELO")
    
    # Trend line
    z = np.polyfit(indices, elos, 1)
    p = np.poly1d(z)
    ax.plot(indices, p(indices), "--", linewidth=2, 
            color=COLORS["text_secondary"], alpha=0.7, label="Trend")
    
    ax.set_xlabel("Match Index", fontsize=10, fontweight='bold')
    ax.set_ylabel("ELO Rating", fontsize=10, fontweight='bold')
    ax.set_title("ELO Evolution", fontsize=12, fontweight='bold', pad=10)
    ax.legend(loc='best', frameon=False)
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    return _save_fig(fig)


# ─── Main PDF Generator ──────────────────────────────────────


def generate_rich_scouting_pdf(stats: list[dict], opponent_name: str, output_path: str) -> str:
    """Generate rich multi-page scouting PDF with small multiples.
    
    Args:
        stats: List of per-match stat dicts (pre-computed)
        opponent_name: Name to display
        output_path: Where to save PDF
    
    Data source rule:
    - Count how many have diplomacy=="1v1"
    - If >=5: use only those
    - If <5: use all, add warning tag
    """
    # Flatten multi-player match data into per-player view
    flat_stats = []
    for match in stats:
        flat = extract_player_stats(match, opponent_name)
        if flat is not None:
            flat_stats.append(flat)

    # Filter stats
    filtered_stats, tg_warning = filter_stats(flat_stats)
    
    if not filtered_stats:
        raise ValueError("No stats to analyze")
    
    n_matches = len(filtered_stats)
    
    # Compute KPIs
    wins = sum(1 for s in filtered_stats if s.get("winner"))
    losses = n_matches - wins
    win_rate = (wins / n_matches * 100) if n_matches > 0 else 0
    
    # Feudal time average
    feudal_times = [s.get("feudal") for s in filtered_stats if s.get("feudal") and s.get("feudal") != 0]
    avg_feudal = safe_avg_seconds(feudal_times)
    
    # eAPM average
    eapms = [s.get("eapm") for s in filtered_stats if s.get("eapm") and s.get("eapm") != 0]
    avg_eapm = int(safe_mean(eapms)) if eapms else 0
    
    # Favorite civ
    civ_counts = Counter(s["civ"] for s in filtered_stats if s.get("civ"))
    favorite_civ = civ_counts.most_common(1)[0] if civ_counts else ("Unknown", 0)
    fav_civ_name = favorite_civ[0]
    fav_civ_pct = (favorite_civ[1] / n_matches * 100) if n_matches > 0 else 0
    
    # TC Idle average
    tc_idles = [s.get("tc_idle") for s in filtered_stats if s.get("tc_idle") is not None]
    avg_tc_idle = round(safe_mean(tc_idles)) if tc_idles else 0
    
    # Game duration average
    durations = [s.get("duration") for s in filtered_stats if s.get("duration") and s.get("duration") != 0]
    avg_duration = safe_avg_seconds(durations)
    avg_duration_min = safe_mean(durations) / 60 if durations else 0
    
    # Recent form (last 5)
    recent_results = [s.get("winner", False) for s in filtered_stats[-5:]]
    
    # ELO trend
    elos = [s.get("elo") for s in filtered_stats if s.get("elo")]
    current_elo = elos[-1] if elos else 0
    
    if len(elos) >= 2:
        elo_delta = elos[-1] - elos[0]
        if elo_delta > 20:
            elo_trend = "▲"
            elo_trend_text = f"▲ +{elo_delta}"
        elif elo_delta < -20:
            elo_trend = "▼"
            elo_trend_text = f"▼ {elo_delta}"
        else:
            elo_trend = "→"
            elo_trend_text = "→ Stable"
    else:
        elo_trend_text = "--"
    
    # Generate charts
    chart_civ_pie_path = chart_civ_pie(filtered_stats)
    chart_perf_grid_path = chart_performance_grid(filtered_stats)
    chart_army_grid_path = chart_army_strategy_grid(filtered_stats)
    chart_elo_path = chart_elo_evolution(filtered_stats)
    
    # Create PDF
    pdf = FPDF()
    pdf.set_auto_page_break(False)
    
    # Add Unicode font
    pdf.add_font("DejaVu", "", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", uni=True)
    pdf.add_font("DejaVu", "B", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", uni=True)
    
    # ─── Page 1: Overview Dashboard ─────────────────────────
    
    pdf.add_page()
    
    # Title
    pdf.set_font("DejaVu", "B", 20)
    pdf.set_text_color(44, 62, 80)
    pdf.cell(0, 14, f"SCOUTING REPORT: {opponent_name}", ln=True, align="C")
    
    # Subtitle
    pdf.set_font("DejaVu", "", 10)
    pdf.set_text_color(127, 140, 141)
    n_1v1 = sum(1 for s in filtered_stats if s.get("diplomacy") == "1v1")
    n_tg = n_matches - n_1v1
    subtitle = f"{n_matches} matches ({n_1v1} 1v1 / {n_tg} TG) | ELO: {current_elo}"
    if tg_warning:
        subtitle += " ⚠️ Includes TG data"
    pdf.cell(0, 6, subtitle, ln=True, align="C")
    
    pdf.ln(10)
    
    # KPI cards row 1
    card_w = 45
    card_h = 15
    spacing = 5
    start_x = 10
    y_pos = pdf.get_y()
    
    # Win Rate
    wr_color = (39, 174, 96) if win_rate >= 50 else (231, 76, 60)
    draw_kpi_card(pdf, start_x, y_pos, card_w, card_h, "Win Rate", f"{win_rate:.0f}%", wr_color)
    
    # Avg Feudal Time
    draw_kpi_card(pdf, start_x + card_w + spacing, y_pos, card_w, card_h, 
                  "Avg Feudal", avg_feudal, (41, 128, 185))
    
    # Avg eAPM
    draw_kpi_card(pdf, start_x + 2*(card_w + spacing), y_pos, card_w, card_h, 
                  "Avg eAPM", avg_eapm if avg_eapm else "--", (155, 89, 182))
    
    # Favorite Civ
    fav_text = f"{fav_civ_name[:8]} {fav_civ_pct:.0f}%"
    draw_kpi_card(pdf, start_x + 3*(card_w + spacing), y_pos, card_w, card_h, 
                  "Favorite Civ", fav_text, (230, 126, 34))
    
    pdf.ln(card_h + 10)
    
    # KPI cards row 2
    y_pos = pdf.get_y()
    
    # Avg TC Idle
    draw_kpi_card(pdf, start_x, y_pos, card_w, card_h, 
                  "Avg TC Idle", f"{avg_tc_idle}s" if avg_tc_idle else "--", (52, 152, 219))
    
    # Avg Duration
    draw_kpi_card(pdf, start_x + card_w + spacing, y_pos, card_w, card_h, 
                  "Avg Duration", avg_duration, (46, 204, 113))
    
    # Recent Form (last 5: W/L dots)
    pdf.set_xy(start_x + 2*(card_w + spacing), y_pos)
    pdf.set_fill_color(189, 195, 199)
    pdf.rect(start_x + 2*(card_w + spacing), y_pos, card_w, card_h, 'F')
    
    # Draw dots
    dot_start_x = start_x + 2*(card_w + spacing) + 5
    dot_y = y_pos + card_h/2 - 1.5
    for i, win in enumerate(recent_results):
        color = (39, 174, 96) if win else (231, 76, 60)
        pdf.set_fill_color(*color)
        pdf.circle(dot_start_x + i*7, dot_y, 1.5, 'F')
    
    pdf.set_text_color(44, 62, 80)
    pdf.set_font("DejaVu", "", 8)
    pdf.set_xy(start_x + 2*(card_w + spacing), y_pos + card_h + 1)
    pdf.cell(card_w, 4, "Recent Form (Last 5)", align='C')
    
    # ELO Trend
    draw_kpi_card(pdf, start_x + 3*(card_w + spacing), y_pos, card_w, card_h, 
                  "ELO Trend", elo_trend_text, (149, 165, 166))
    
    pdf.ln(card_h + 12)
    
    # Civ distribution pie chart
    if chart_civ_pie_path:
        pdf.image(chart_civ_pie_path, x=40, y=None, w=130)
    
    # Footer
    pdf.set_y(-20)
    pdf.set_font("DejaVu", "", 7)
    pdf.set_text_color(189, 195, 199)
    pdf.cell(0, 4, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align="C")
    pdf.cell(0, 4, "Agelytics — Opponent Scouting", ln=True, align="C")
    
    # ─── Page 2: Performance Metrics ─────────────────────────
    
    pdf.add_page()
    
    pdf.set_font("DejaVu", "B", 16)
    pdf.set_text_color(44, 62, 80)
    pdf.cell(0, 12, "Performance Metrics", ln=True, align="C")
    
    pdf.ln(4)
    
    if chart_perf_grid_path:
        pdf.image(chart_perf_grid_path, x=5, y=None, w=200)
    
    # Footer
    pdf.set_y(-20)
    pdf.set_font("DejaVu", "", 7)
    pdf.set_text_color(189, 195, 199)
    pdf.cell(0, 4, f"Page 2 of 4", ln=True, align="C")
    
    # ─── Page 3: Army & Strategy ─────────────────────────────
    
    pdf.add_page()
    
    pdf.set_font("DejaVu", "B", 16)
    pdf.set_text_color(44, 62, 80)
    pdf.cell(0, 12, "Army & Strategy", ln=True, align="C")
    
    pdf.ln(4)
    
    if chart_army_grid_path:
        pdf.image(chart_army_grid_path, x=5, y=None, w=200)
    
    # Footer
    pdf.set_y(-20)
    pdf.set_font("DejaVu", "", 7)
    pdf.set_text_color(189, 195, 199)
    pdf.cell(0, 4, f"Page 3 of 4", ln=True, align="C")
    
    # ─── Page 4: ELO & Trends ────────────────────────────────
    
    pdf.add_page()
    
    pdf.set_font("DejaVu", "B", 16)
    pdf.set_text_color(44, 62, 80)
    pdf.cell(0, 12, "ELO & Trends", ln=True, align="C")
    
    pdf.ln(4)
    
    # ELO evolution chart
    if chart_elo_path:
        pdf.image(chart_elo_path, x=15, y=None, w=180)
    else:
        pdf.set_font("DejaVu", "", 10)
        pdf.set_text_color(127, 140, 141)
        pdf.cell(0, 10, "Not enough ELO data", ln=True, align="C")
    
    pdf.ln(8)
    
    # Key Patterns section
    pdf.set_font("DejaVu", "B", 12)
    pdf.set_text_color(44, 62, 80)
    pdf.cell(0, 8, "Key Patterns", ln=True)
    
    pdf.set_font("DejaVu", "", 9)
    pdf.set_text_color(44, 62, 80)
    
    patterns = []
    
    # Civ pool size
    total_civs = len(civ_counts)
    if total_civs <= 3:
        patterns.append(f"• Plays only {total_civs} civ(s) — predictable pool")
    elif total_civs >= 8:
        patterns.append(f"• Plays {total_civs} civs — highly adaptable")
    else:
        patterns.append(f"• Civ pool: {total_civs} civilizations")
    
    # Civ loyalty
    if fav_civ_pct >= 40:
        patterns.append(f"• Heavily favors {fav_civ_name} ({fav_civ_pct:.0f}% of games)")
    
    # Strongest/weakest civ
    civ_wr_data = {}
    for s in filtered_stats:
        civ = s.get("civ")
        if not civ:
            continue
        if civ not in civ_wr_data:
            civ_wr_data[civ] = {"wins": 0, "total": 0}
        civ_wr_data[civ]["total"] += 1
        if s.get("winner"):
            civ_wr_data[civ]["wins"] += 1
    
    civ_wrs = {civ: (data["wins"] / data["total"] * 100) 
               for civ, data in civ_wr_data.items() if data["total"] >= 2}
    
    if civ_wrs:
        strongest = max(civ_wrs.items(), key=lambda x: x[1])
        weakest = min(civ_wrs.items(), key=lambda x: x[1])
        patterns.append(f"• Strongest civ: {strongest[0]} ({strongest[1]:.0f}% WR)")
        patterns.append(f"• Weakest civ: {weakest[0]} ({weakest[1]:.0f}% WR)")
    
    # Feudal times trend
    if len(feudal_times) >= 5:
        first_half = feudal_times[:len(feudal_times)//2]
        second_half = feudal_times[len(feudal_times)//2:]
        
        avg_first = safe_mean(first_half)
        avg_second = safe_mean(second_half)
        
        if avg_first and avg_second:
            diff = avg_second - avg_first
            if diff < -10:
                patterns.append(f"• Feudal times getting faster (improving)")
            elif diff > 10:
                patterns.append(f"• Feudal times getting slower")
    
    # TC discipline
    if avg_tc_idle == 0:
        patterns.append(f"• Perfect TC discipline (0s idle)")
    elif avg_tc_idle < 10:
        patterns.append(f"• Good TC discipline ({avg_tc_idle}s idle avg)")
    elif avg_tc_idle > 60:
        patterns.append(f"• Poor TC discipline ({avg_tc_idle}s idle avg)")
    else:
        patterns.append(f"• Average TC idle: {avg_tc_idle}s")
    
    # Aggression profile
    if avg_duration_min < 25:
        patterns.append(f"• Aggressive playstyle (avg {avg_duration_min:.0f}min games)")
    elif avg_duration_min > 35:
        patterns.append(f"• Boomer playstyle (avg {avg_duration_min:.0f}min games)")
    else:
        patterns.append(f"• Balanced game length (avg {avg_duration_min:.0f}min)")
    
    # Print patterns
    for pattern in patterns:
        pdf.multi_cell(0, 5, pattern)
        pdf.ln(0.5)
    
    # Footer
    pdf.set_y(-25)
    pdf.set_font("DejaVu", "", 7)
    pdf.set_text_color(189, 195, 199)
    
    data_source_text = "Data source: 1v1 only" if not tg_warning else "Data source: All ranked (includes TG)"
    pdf.cell(0, 4, data_source_text, ln=True, align="C")
    pdf.cell(0, 4, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align="C")
    pdf.cell(0, 4, "Page 4 of 4", ln=True, align="C")
    
    # Save PDF
    pdf.output(output_path)
    
    # Cleanup temp files
    for path in [chart_civ_pie_path, chart_perf_grid_path, chart_army_grid_path, chart_elo_path]:
        if path and os.path.exists(path):
            os.remove(path)
    
    return output_path


# ─── Test Block ──────────────────────────────────────────────


if __name__ == "__main__":
    import json
    
    with open('/tmp/urubu_stats.json') as f:
        stats = json.load(f)
    
    generate_rich_scouting_pdf(stats, "Urubu", "/tmp/urubu_scouting_v2.pdf")
    print("Done!")
