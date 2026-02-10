"""Generate professional multi-page PDF reports for matches.

Page 1: Dashboard — KPIs + key charts (age-up, TC idle by era)
Page 2: Economy — vill rate, farm gap, resource efficiency, production buildings
Page 3: Military — army composition, tech timings, military timing index
Page 4: Infrastructure — buildings, walling, key techs

Uses seaborn + pandas for polished visualizations.
"""

import json
import os
import tempfile
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
    if seconds is None or seconds == 0:
        return "--:--"
    m, s = divmod(int(seconds), 60)
    return f"{m}:{s:02d}"


def _save_fig(fig):
    """Save figure to temp PNG and close."""
    fd, path = tempfile.mkstemp(suffix=".png", prefix="agely_")
    os.close(fd)
    fig.savefig(path, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def _match_to_players_df(match):
    """Extract player summary as DataFrame."""
    rows = []
    for p in match.get("players", []):
        row = {
            "Player": p["name"],
            "Civ": p.get("civ_name", "?"),
            "ELO": p.get("elo"),
            "Winner": bool(p.get("winner")),
            "eAPM": p.get("eapm"),
            "TC Idle (s)": p.get("tc_idle_secs", 0),
            "TC Idle Dark": p.get("tc_idle_dark", 0) or 0,
            "TC Idle Feudal": p.get("tc_idle_feudal", 0) or 0,
            "TC Idle Castle": p.get("tc_idle_castle", 0) or 0,
            "TC Idle Imperial": p.get("tc_idle_imperial", 0) or 0,
            "Opening": (p.get("opening_strategy")
                        or match.get("openings", {}).get(p["name"], "Unknown")),
            "Farm Gap": p.get("farm_gap_average"),
            "Mil Timing": p.get("military_timing_index"),
            "Housed": match.get("housed_count", {}).get(p["name"], 0),
            "Villagers": match.get("unit_production", {}).get(p["name"], {}).get("Villager", 0),
            "Farms": match.get("buildings", {}).get(p["name"], {}).get("Farm", 0),
            "TCs Final": p.get("tc_count_final", "?"),
            "Est Idle Vill": p.get("estimated_idle_vill_time"),
        }
        rows.append(row)
    return pd.DataFrame(rows)


# ─── Chart generators ────────────────────────────────────────


def chart_age_up(match):
    """Horizontal grouped bar: age-up times per player."""
    apply_style()
    age_ups = match.get("age_ups", [])
    if not age_ups:
        return None

    df = pd.DataFrame(age_ups)
    # Shorten age names
    df["age"] = df["age"].str.replace(" Age", "")
    age_order = ["Feudal", "Castle", "Imperial"]
    df = df[df["age"].isin(age_order)]
    if df.empty:
        return None

    df["age"] = pd.Categorical(df["age"], categories=age_order, ordered=True)
    colors = get_player_colors(df["player"].nunique())

    fig, ax = plt.subplots(figsize=(7.5, 2.8))
    sns.barplot(data=df, y="age", x="timestamp_secs", hue="player",
                palette=colors, orient="h", ax=ax, dodge=True, edgecolor="white", linewidth=0.5)

    # Add time labels on bars
    for container in ax.containers:
        for bar in container:
            w = bar.get_width()
            if w > 0:
                ax.text(w + 8, bar.get_y() + bar.get_height() / 2,
                        fmt(w), va="center", fontsize=8, color=COLORS["text_secondary"])

    ax.set_xlabel("Game Time (seconds)", fontsize=9)
    ax.set_ylabel("")
    ax.set_title("Age-Up Timeline", fontsize=12, fontweight="bold", pad=8)
    ax.legend(title="", fontsize=8, loc="lower right")
    sns.despine(left=True)
    fig.tight_layout()
    return _save_fig(fig)


def chart_tc_idle_by_era(match):
    """Grouped bar: TC idle seconds per era per player."""
    apply_style()
    players = match.get("players", [])
    if not players:
        return None

    rows = []
    for p in players:
        for era, field in [("Dark", "tc_idle_dark"), ("Feudal", "tc_idle_feudal"),
                           ("Castle", "tc_idle_castle"), ("Imperial", "tc_idle_imperial")]:
            val = p.get(field, 0) or 0
            rows.append({"Player": p["name"], "Era": era, "Idle (s)": val})

    df = pd.DataFrame(rows)
    if df["Idle (s)"].sum() == 0:
        return None

    df["Era"] = pd.Categorical(df["Era"], categories=["Dark", "Feudal", "Castle", "Imperial"], ordered=True)
    colors = get_player_colors(len(players))

    fig, ax = plt.subplots(figsize=(7.5, 3.5))
    sns.barplot(data=df, x="Era", y="Idle (s)", hue="Player",
                palette=colors, ax=ax, edgecolor="white", linewidth=0.5)

    # Always show labels — including "0:00" for zero bars
    for container in ax.containers:
        for bar in container:
            h = bar.get_height()
            label = fmt(h) if h > 0 else "0:00"
            y_pos = max(h, 2) + 3
            ax.text(bar.get_x() + bar.get_width() / 2, y_pos,
                    label, ha="center", va="bottom", fontsize=8,
                    color=COLORS["text_secondary"], fontweight="bold" if h > 60 else "normal")

    ax.set_ylabel("Idle Time (seconds)", fontsize=9)
    ax.set_xlabel("")
    ax.set_title("TC Idle Time by Era", fontsize=12, fontweight="bold", pad=8)
    ax.legend(title="", fontsize=8)
    sns.despine()
    fig.tight_layout()
    return _save_fig(fig)


def chart_army_composition(match):
    """Horizontal bar: army units per player (excluding eco)."""
    apply_style()
    unit_prod = match.get("unit_production", {})
    if not unit_prod:
        return None

    eco = {"Villager", "Trade Cart", "Fishing Ship", "Transport Ship"}
    rows = []
    for player, units in unit_prod.items():
        for unit, count in units.items():
            if unit not in eco and count > 0:
                rows.append({"Player": player, "Unit": unit, "Count": count})

    if not rows:
        return None

    df = pd.DataFrame(rows)
    # Sort units by total count
    unit_order = df.groupby("Unit")["Count"].sum().sort_values().index.tolist()
    df["Unit"] = pd.Categorical(df["Unit"], categories=unit_order, ordered=True)
    colors = get_player_colors(df["Player"].nunique())

    height = max(3, len(unit_order) * 0.45)
    fig, ax = plt.subplots(figsize=(7.5, height))
    sns.barplot(data=df, y="Unit", x="Count", hue="Player",
                palette=colors, orient="h", ax=ax, dodge=True,
                edgecolor="white", linewidth=0.5)

    ax.set_xlabel("Units Produced", fontsize=9)
    ax.set_ylabel("")
    ax.set_title("Army Composition", fontsize=12, fontweight="bold", pad=8)
    ax.legend(title="", fontsize=8, loc="lower right")
    sns.despine(left=True)
    fig.tight_layout()
    return _save_fig(fig)


def chart_walling(match):
    """Grouped bar: wall tiles by era."""
    apply_style()
    wall_data = match.get("wall_tiles_by_age", {})
    if not wall_data:
        return None

    rows = []
    for player, ages in wall_data.items():
        for era, tiles in ages.items():
            if tiles > 0:
                rows.append({"Player": player, "Era": era, "Tiles": tiles})

    if not rows:
        return None

    df = pd.DataFrame(rows)
    df["Era"] = pd.Categorical(df["Era"], categories=["Dark", "Feudal", "Castle", "Imperial"], ordered=True)
    colors = get_player_colors(df["Player"].nunique())

    fig, ax = plt.subplots(figsize=(6, 2.8))
    sns.barplot(data=df, x="Era", y="Tiles", hue="Player",
                palette=colors, ax=ax, edgecolor="white", linewidth=0.5)

    ax.set_ylabel("Wall Tiles", fontsize=9)
    ax.set_xlabel("")
    ax.set_title("Walling by Era", fontsize=12, fontweight="bold", pad=8)
    ax.legend(title="", fontsize=8)
    sns.despine()
    fig.tight_layout()
    return _save_fig(fig)


def chart_tech_timeline(match):
    """Horizontal point/strip chart of key tech timings."""
    apply_style()
    researches = match.get("researches", [])
    if not researches:
        return None

    key_set = {
        "Loom", "Wheelbarrow", "Hand Cart",
        "Double-Bit Axe", "Bow Saw", "Two-Man Saw",
        "Horse Collar", "Heavy Plow", "Crop Rotation",
        "Gold Mining", "Gold Shaft Mining",
        "Fletching", "Bodkin Arrow", "Bracer",
        "Forging", "Iron Casting", "Blast Furnace",
        "Scale Mail Armor", "Chain Mail Armor", "Plate Mail Armor",
        "Scale Barding Armor", "Chain Barding Armor", "Plate Barding Armor",
        "Ballistics", "Chemistry", "Conscription",
        "Murder Holes", "Masonry", "Architecture",
    }

    rows = [r for r in researches if r["tech"] in key_set]
    if not rows:
        return None

    df = pd.DataFrame(rows)
    # Sort techs by earliest research time
    tech_order = df.groupby("tech")["timestamp_secs"].min().sort_values(ascending=False).index.tolist()
    df["tech"] = pd.Categorical(df["tech"], categories=tech_order, ordered=True)
    colors = get_player_colors(df["player"].nunique())

    height = max(3, len(tech_order) * 0.28)
    fig, ax = plt.subplots(figsize=(7.5, height))
    sns.stripplot(data=df, y="tech", x="timestamp_secs", hue="player",
                  palette=colors, ax=ax, size=7, jitter=False,
                  dodge=True, marker="D", edgecolor="white", linewidth=0.5)

    # Add time labels
    for _, row in df.iterrows():
        ax.text(row["timestamp_secs"] + 15,
                tech_order.index(row["tech"]),
                fmt(row["timestamp_secs"]),
                va="center", fontsize=6, color=COLORS["text_secondary"])

    ax.set_xlabel("Game Time (seconds)", fontsize=9)
    ax.set_ylabel("")
    ax.set_title("Key Tech Timings", fontsize=12, fontweight="bold", pad=8)
    ax.legend(title="", fontsize=8, loc="lower right")
    sns.despine(left=True)
    fig.tight_layout()
    return _save_fig(fig)


# ─── PDF Class ────────────────────────────────────────────────


class MatchPDF(FPDF):
    """Custom PDF with header/footer."""

    def __init__(self, match, player_name=None):
        super().__init__()
        self.match = match
        self.player_name = player_name
        self.temp_images = []

    def header(self):
        self.set_font("Helvetica", "B", 20)
        self.set_text_color(44, 62, 80)
        self.cell(0, 8, "AGELYTICS", 0, 0, "L")
        self.set_font("Helvetica", "", 9)
        self.set_text_color(150, 150, 150)
        self.cell(0, 8, f"Page {self.page_no()}", 0, 1, "R")
        # Bold accent line
        self.set_draw_color(44, 62, 80)
        self.set_line_width(0.6)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(160, 160, 160)
        self.cell(0, 10,
                  f"Generated by Agelytics | github.com/tiuitobot/agelytics | {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                  0, 0, "C")

    def sep(self):
        self.set_draw_color(200, 200, 200)
        self.set_line_width(0.3)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)

    def section(self, title, emoji=""):
        self.ln(4)
        # Accent bar
        self.set_fill_color(44, 62, 80)
        self.rect(10, self.get_y(), 3, 8, "F")
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(44, 62, 80)
        self.set_x(16)
        self.cell(0, 8, f"{emoji}  {title}" if emoji else title, 0, 1, "L")
        self.ln(2)

    def subsection(self, title):
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(52, 73, 94)
        self.cell(0, 6, title, 0, 1, "L")
        self.ln(1)

    def txt(self, text, bold=False, color=None, size=10):
        self.set_font("Helvetica", "B" if bold else "", size)
        self.set_text_color(*(color or (50, 50, 50)))
        self.multi_cell(0, 5, self._sanitize(text))
        self.ln(1)

    def data_line(self, label, value, unit="", assessment=None):
        """Print a label: value line with the value in bold + color."""
        self.set_font("Helvetica", "", 10)
        self.set_text_color(80, 80, 80)
        self.cell(self.get_string_width(f"  {label}: ") + 2, 5, f"  {label}: ", 0, 0)
        # Value in bold + accent color
        if assessment == "good":
            val_color = (39, 174, 96)
        elif assessment == "bad":
            val_color = (192, 57, 43)
        elif assessment == "warn":
            val_color = (243, 156, 18)
        else:
            val_color = (44, 62, 80)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*val_color)
        self.cell(0, 5, self._sanitize(f"{value}{(' ' + unit) if unit else ''}"), 0, 1)
        self.ln(0.5)

    def kpi_row(self, kpis, y=None):
        """Draw KPI cards. kpis = [(label, value, bg_color_or_None), ...]"""
        if y is None:
            y = self.get_y()
        n = len(kpis)
        card_w = 190 / n
        gap = 2

        for i, (label, value, bg) in enumerate(kpis):
            x = 10 + i * card_w
            w = card_w - gap

            # Card background
            if bg:
                self.set_fill_color(*bg)
            else:
                self.set_fill_color(247, 248, 249)
            self.rect(x, y, w, 22, "F")

            # Subtle left accent
            if bg:
                self.set_fill_color(*bg)
            else:
                self.set_fill_color(44, 62, 80)
            self.rect(x, y, 2.5, 22, "F")

            # Value
            self.set_font("Helvetica", "B", 15)
            if bg:
                self.set_text_color(255, 255, 255)
            else:
                self.set_text_color(44, 62, 80)
            self.set_xy(x + 4, y + 2)
            val_str = self._sanitize(str(value)[:18])
            self.cell(w - 6, 9, val_str, 0, 0, "C")

            # Label
            self.set_font("Helvetica", "", 8)
            if bg:
                self.set_text_color(220, 220, 220)
            else:
                self.set_text_color(127, 140, 141)
            self.set_xy(x + 4, y + 13)
            self.cell(w - 6, 5, label, 0, 0, "C")

        self.set_y(y + 26)

    @staticmethod
    def _sanitize(text):
        """Replace non-latin1 chars for Helvetica compat."""
        replacements = {
            "\u2013": "-", "\u2014": "-", "\u2018": "'", "\u2019": "'",
            "\u201c": '"', "\u201d": '"', "\u2026": "...", "\u2022": "-",
            "\u2192": "->", "\u2190": "<-",
        }
        for k, v in replacements.items():
            text = text.replace(k, v)
        return text.encode("latin-1", errors="replace").decode("latin-1")

    def chart(self, img_path, width=175):
        if img_path is None:
            return
        if self.get_y() + 75 > 270:
            self.add_page()
        x = (210 - width) / 2
        self.image(img_path, x=x, w=width)
        self.ln(3)
        self.temp_images.append(img_path)

    def cleanup(self):
        for img in self.temp_images:
            try:
                os.unlink(img)
            except Exception:
                pass


# ─── Main generation ──────────────────────────────────────────


def generate_match_pdf(match, output_path, player_name=None):
    """Generate a complete multi-page match PDF report."""
    pdf = MatchPDF(match, player_name)
    players = match.get("players", [])
    if not players:
        return None

    focus = next((p for p in players if p["name"] == player_name), players[0])
    opp = next((p for p in players if p["name"] != focus["name"]), None)
    pdf_players = _match_to_players_df(match)

    # ═══════════════════════════════════════════════════════════
    # PAGE 1: DASHBOARD
    # ═══════════════════════════════════════════════════════════
    pdf.add_page()

    # Match headline
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(44, 62, 80)
    if opp:
        pdf.cell(0, 7,
                 f"{focus['name']} ({focus.get('civ_name', '?')})  vs  "
                 f"{opp['name']} ({opp.get('civ_name', '?')})",
                 0, 1, "L")
    else:
        pdf.cell(0, 7, focus["name"], 0, 1, "L")

    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(127, 140, 141)
    played = match.get("played_at", "?")
    map_name = match.get("map_name", "?")
    dur = fmt(match.get("duration_secs", 0))
    pdf.cell(0, 4.5,
             f"{played}  |  {map_name}  |  {dur}  |  {match.get('diplomacy', '1v1')}  |  "
             f"Pop {match.get('pop_limit', '?')}",
             0, 1, "L")
    pdf.ln(4)

    # KPI Row 1
    result = "VICTORY" if focus.get("winner") else "DEFEAT"
    result_bg = (39, 174, 96) if focus.get("winner") else (192, 57, 43)
    opening = (focus.get("opening_strategy")
               or match.get("openings", {}).get(focus["name"], "?"))
    elo_str = f"{focus.get('elo', '?')} vs {opp.get('elo', '?')}" if opp else str(focus.get("elo", "?"))

    pdf.kpi_row([
        ("Result", result, result_bg),
        ("Duration", dur, None),
        ("ELO", elo_str, None),
        ("Opening", opening, (52, 73, 94)),
    ])

    # KPI Row 2
    tc_idle = focus.get("tc_idle_secs", 0) or 0
    housed = match.get("housed_count", {}).get(focus["name"], 0)
    eapm = focus.get("eapm", "?")
    fg = focus.get("farm_gap_average")
    fg_str = f"{fg:.1f}s" if fg is not None else "N/A"
    housed_bg = (192, 57, 43) if housed >= 5 else (243, 156, 18) if housed >= 3 else None

    pdf.kpi_row([
        ("TC Idle", fmt(tc_idle), None),
        ("Housed", f"{housed}x", housed_bg),
        ("eAPM", str(eapm), None),
        ("Farm Gap (avg)", fg_str, None),
    ])

    pdf.sep()

    # Age-up chart
    pdf.section("Age-Up Timeline")
    pdf.chart(chart_age_up(match), width=170)

    # Brief comparison
    age_ups = match.get("age_ups", [])
    if age_ups and opp:
        f_feudal = next((a["timestamp_secs"] for a in age_ups
                         if a["player"] == focus["name"] and "Feudal" in a["age"]), None)
        o_feudal = next((a["timestamp_secs"] for a in age_ups
                         if a["player"] == opp["name"] and "Feudal" in a["age"]), None)
        if f_feudal and o_feudal:
            diff = f_feudal - o_feudal
            if abs(diff) > 5:
                faster = focus["name"] if diff < 0 else opp["name"]
                pdf.txt(f"{faster} reached Feudal {abs(diff):.0f}s faster "
                        f"({fmt(min(f_feudal, o_feudal))}).")

    pdf.sep()

    # TC idle by era
    pdf.section("TC Idle by Era")
    pdf.chart(chart_tc_idle_by_era(match), width=170)

    # Text summary
    for p in players:
        parts = []
        for era, fld in [("Dark", "tc_idle_dark"), ("Feudal", "tc_idle_feudal"),
                         ("Castle", "tc_idle_castle"), ("Imp", "tc_idle_imperial")]:
            v = p.get(fld, 0) or 0
            parts.append(f"{era} {fmt(v) if v > 0 else '0:00'}")
        total = p.get("tc_idle_secs", 0) or 0
        assess = "good" if total < 300 else "warn" if total < 600 else "bad"
        pdf.data_line(p["name"], f"{', '.join(parts)}", f"(Total: {fmt(total)})", assessment=assess)

    # ═══════════════════════════════════════════════════════════
    # PAGE 2: ECONOMY
    # ═══════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.section("Economy", emoji="")

    for p in players:
        pname = p["name"]
        vills = match.get("unit_production", {}).get(pname, {}).get("Villager", 0)
        farms = match.get("buildings", {}).get(pname, {}).get("Farm", 0)
        fg_val = p.get("farm_gap_average")
        mil_idx = p.get("military_timing_index")
        tc_f = p.get("tc_count_final", "?")
        est = p.get("estimated_idle_vill_time")
        res_eff = match.get("metrics", {}).get(pname, {}).get("resource_collection_efficiency")

        pdf.subsection(f"{pname} ({p.get('civ_name', '?')})")
        pdf.data_line("Villagers Produced", str(vills))
        pdf.data_line("Farms Built", str(farms))
        pdf.data_line("Final TCs", str(tc_f))
        if fg_val is not None:
            q = "excellent" if fg_val < 3 else "good" if fg_val < 6 else "needs work"
            assess = "good" if fg_val < 3 else None if fg_val < 6 else "warn"
            pdf.data_line("Farm Reseeding Gap", f"{fg_val:.1f}s avg ({q})", assessment=assess)
        if est is not None:
            pdf.data_line("Est. Idle Villager Time", fmt(est), "(proxy)")
        if res_eff is not None:
            pdf.data_line("Resource Efficiency", f"{res_eff:.0f}", "res/villager")
        if mil_idx is not None:
            s = "rush" if mil_idx < 0.7 else "boom" if mil_idx > 1.2 else "balanced"
            pdf.data_line("Military Timing Index", f"{mil_idx:.2f} ({s})")
        pdf.ln(3)

    pdf.sep()

    # Production buildings by age
    prod_b = match.get("production_buildings_by_age", {})
    if prod_b:
        pdf.section("Production Buildings by Age")
        abbr = {"Archery Range": "Range", "Barracks": "Rax", "Stable": "Stable",
                "Siege Workshop": "Siege", "Castle": "Castle", "Monastery": "Monastery"}
        for pname in [p["name"] for p in players]:
            pb = prod_b.get(pname, {})
            if not pb:
                continue
            pdf.subsection(pname)
            for era in ["Dark", "Feudal", "Castle", "Imperial"]:
                blds = pb.get(era, {})
                if blds:
                    bstr = ", ".join(f"{c}x {abbr.get(b, b)}" for b, c in blds.items())
                    pdf.txt(f"  {era}: {bstr}")
            pdf.ln(1)

    # ═══════════════════════════════════════════════════════════
    # PAGE 3: MILITARY
    # ═══════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.section("Army Composition")
    pdf.chart(chart_army_composition(match), width=170)

    # Openings
    openings = match.get("openings", {})
    if openings:
        pdf.subsection("Opening Strategies")
        for pname in [p["name"] for p in players]:
            op = openings.get(pname, "Unknown")
            pdf.txt(f"  {pname}: {op}")
        pdf.ln(2)

    pdf.sep()

    # Tech timings
    pdf.section("Key Tech Timings")
    pdf.chart(chart_tech_timeline(match), width=170)

    # Tech assessment
    try:
        from .tech_timings import extract_key_techs, format_timing, assess_timing
        for p in players:
            pname = p["name"]
            kt = extract_key_techs(match, pname)
            if not kt:
                continue
            pdf.subsection(pname)
            by_cat = {}
            for td in kt:
                by_cat.setdefault(td["category"], []).append(td)
            for cat in ["Economy", "Military", "Blacksmith", "University"]:
                techs = by_cat.get(cat, [])
                if techs:
                    parts = []
                    for td in techs[:5]:
                        a = assess_timing(td["tech"], td["timestamp_secs"])
                        ind = " [OK]" if a == "Good" else " [LATE]" if a == "Poor" else ""
                        parts.append(f"{td['tech']} {fmt(td['timestamp_secs'])}{ind}")
                    # Determine overall assessment for category
                    assessments = [assess_timing(td["tech"], td["timestamp_secs"]) for td in techs[:5]]
                    cat_assess = "bad" if "Poor" in assessments else "good" if all(a == "Good" for a in assessments) else None
                    pdf.data_line(cat, ", ".join(parts), assessment=cat_assess)
            pdf.ln(1)
    except ImportError:
        pass

    # ═══════════════════════════════════════════════════════════
    # PAGE 4: INFRASTRUCTURE
    # ═══════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.section("Buildings")

    buildings = match.get("buildings", {})
    if buildings:
        eco_list = ["Town Center", "Farm", "Mill", "Lumber Camp", "Mining Camp", "Market", "House"]
        mil_list = ["Barracks", "Archery Range", "Stable", "Siege Workshop", "Castle"]
        def_list = ["Watch Tower", "Guard Tower", "Keep", "Bombard Tower",
                    "Gate", "Palisade Wall", "Stone Wall", "Fortified Wall"]

        for p in players:
            pname = p["name"]
            pb = buildings.get(pname, {})
            if not pb:
                continue
            pdf.subsection(f"{pname} ({p.get('civ_name', '?')})")
            for gname, glist in [("Economy", eco_list), ("Military", mil_list), ("Defense", def_list)]:
                items = [(b, pb[b]) for b in glist if b in pb and pb[b] > 0]
                if items:
                    pdf.txt(f"  {gname}: {', '.join(f'{c}x {b}' for b, c in items)}")
            shown = set(eco_list + mil_list + def_list)
            others = [(b, c) for b, c in pb.items() if b not in shown and c > 0]
            if others:
                pdf.txt(f"  Other: {', '.join(f'{c}x {b}' for b, c in others)}")
            pdf.ln(1)

    pdf.sep()

    # Walling
    pdf.section("Walling")
    wall_img = chart_walling(match)
    if wall_img:
        pdf.chart(wall_img, width=150)
    else:
        pdf.txt("  No walling data available.")

    wall_data = match.get("wall_tiles_by_age", {})
    if wall_data:
        for pname in [p["name"] for p in players]:
            pw = wall_data.get(pname, {})
            if pw and any(v > 0 for v in pw.values()):
                total = sum(pw.values())
                parts = [f"{era}: {pw[era]}" for era in ["Dark", "Feudal", "Castle", "Imperial"]
                         if pw.get(era, 0) > 0]
                pdf.txt(f"  {pname}: {', '.join(parts)} (Total: {total} tiles)")

    pdf.sep()

    # Housed
    housed_data = match.get("housed_count", {})
    if housed_data and any(v > 0 for v in housed_data.values()):
        pdf.section("Housed Events")
        for pname in [p["name"] for p in players]:
            c = housed_data.get(pname, 0)
            if c > 0:
                sev = "Critical" if c >= 7 else "Warning" if c >= 4 else "Minor"
                pdf.txt(f"  {pname}: {c} times ({sev})")

    # ─── Save ─────────────────────────────────────────────────
    pdf.output(output_path)
    pdf.cleanup()
    return output_path


if __name__ == "__main__":
    from .db import get_db, get_last_match

    conn = get_db()
    match = get_last_match(conn)
    conn.close()

    if match:
        output = "reports/match_report.pdf"
        os.makedirs("reports", exist_ok=True)
        generate_match_pdf(match, output, player_name="blzulian")
        print(f"Generated: {output}")
    else:
        print("No match found")
