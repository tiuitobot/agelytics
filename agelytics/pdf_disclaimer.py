"""Disclaimer page generator for Agelytics PDF reports.

Renders a final page with:
- Metrics classification table (deterministic/experimental/derived)
- Methodology version
- Legal/confidence notes
"""

from fpdf import FPDF

# Metric definitions with badges
METRIC_REGISTRY = {
    # Match-level
    "TC Idle Time": {"badge": "✅", "type": "Deterministic", "desc": "Gaps >5s in TC task queue"},
    "TC Idle by Era": {"badge": "✅", "type": "Deterministic", "desc": "TC Idle broken down by game era"},
    "TC Idle Breakdown": {"badge": "✅", "type": "Deterministic", "desc": "Idle gaps classified: micro (5-15s), macro (15-60s), AFK (60s+)"},
    "eAPM": {"badge": "✅", "type": "Deterministic", "desc": "Effective actions per minute from replay commands"},
    "Age-up Times": {"badge": "✅", "type": "Deterministic", "desc": "Research completion timestamps"},
    "Wall Tiles": {"badge": "✅", "type": "Deterministic", "desc": "Wall build commands per era"},
    "Housed Count": {"badge": "🔬", "type": "Experimental", "desc": "Detected via house build bursts (2+ in 10s)"},
    "Housed Time (Lower)": {"badge": "🔬", "type": "Experimental", "desc": "Vill queue gaps with house bursts nearby. Bias: underestimates."},
    "Housed Time (Upper)": {"badge": "🔬", "type": "Experimental", "desc": "Pop timeline vs capacity. Bias: overestimates (missing combat deaths)."},
    "TC Idle Effective": {"badge": "📐", "type": "Derived", "desc": "TC Idle + Housed Time. Reported as range [lower, upper]."},
    "Opening Strategy": {"badge": "🔬", "type": "Experimental", "desc": "Pattern matching on early military production"},
    # Aggregate
    "Win Rate": {"badge": "✅", "type": "Deterministic", "desc": "Games won / total games"},
    "Avg Metrics": {"badge": "📐", "type": "Derived", "desc": "Winsorized mean (10%) across matches. Outliers >2σ flagged."},
    "ELO (API)": {"badge": "✅", "type": "Deterministic", "desc": "Per-match rating from aoe2companion API"},
    "ELO (Replay)": {"badge": "🔬", "type": "Experimental", "desc": "Static snapshot from replay header"},
    "Death Count": {"badge": "🔬", "type": "Experimental", "desc": "Delete commands (exact) + military inactivity heuristic"},
}

METHODOLOGY_VERSION = "1.0"
METHODOLOGY_DATE = "2026-02-11"


def render_disclaimer_page(pdf: FPDF, metrics_used: list[str] = None):
    """Add a disclaimer/methodology page to an existing PDF.
    
    Args:
        pdf: FPDF instance to add page to
        metrics_used: List of metric names to include. If None, includes all.
    """
    pdf.add_page()
    
    # Title
    pdf.set_font("DejaVu", "B", 14)
    pdf.set_text_color(44, 62, 80)
    pdf.cell(0, 10, "Methodology & Disclaimers", ln=True, align="C")
    pdf.ln(4)
    
    # Version
    pdf.set_font("DejaVu", "", 8)
    pdf.set_text_color(127, 140, 141)
    pdf.cell(0, 4, f"Methodology v{METHODOLOGY_VERSION} ({METHODOLOGY_DATE})", ln=True, align="C")
    pdf.ln(6)
    
    # Legend
    pdf.set_font("DejaVu", "B", 9)
    pdf.set_text_color(44, 62, 80)
    pdf.cell(0, 5, "Classification Legend", ln=True)
    pdf.set_font("DejaVu", "", 8)
    pdf.set_text_color(44, 62, 80)
    
    legends = [
        ("✅ Deterministic", "Directly computed from replay data, no estimation"),
        ("🔬 Experimental", "Uses heuristics or estimation, known limitations"),
        ("📐 Derived", "Computed from other metrics, inherits their classification"),
    ]
    for badge, desc in legends:
        pdf.cell(40, 4, f"  {badge}", ln=False)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 4, desc, ln=True)
        pdf.set_text_color(44, 62, 80)
    
    pdf.ln(4)
    
    # Metrics table
    pdf.set_font("DejaVu", "B", 9)
    pdf.cell(0, 5, "Metrics Used in This Report", ln=True)
    pdf.ln(2)
    
    # Table header
    pdf.set_font("DejaVu", "B", 7)
    pdf.set_fill_color(236, 240, 241)
    pdf.cell(8, 5, "", border=1, fill=True)
    pdf.cell(42, 5, "Metric", border=1, fill=True)
    pdf.cell(22, 5, "Type", border=1, fill=True)
    pdf.cell(118, 5, "Description", border=1, fill=True, ln=True)
    
    # Table rows
    pdf.set_font("DejaVu", "", 7)
    metrics_to_show = metrics_used or list(METRIC_REGISTRY.keys())
    
    for metric_name in metrics_to_show:
        if metric_name not in METRIC_REGISTRY:
            continue
        m = METRIC_REGISTRY[metric_name]
        
        # Alternate row color
        pdf.cell(8, 4.5, f" {m['badge']}", border=1)
        pdf.cell(42, 4.5, metric_name[:25], border=1)
        pdf.cell(22, 4.5, m["type"], border=1)
        pdf.cell(118, 4.5, m["desc"][:75], border=1, ln=True)
    
    pdf.ln(6)
    
    # Notes
    pdf.set_font("DejaVu", "B", 9)
    pdf.cell(0, 5, "Important Notes", ln=True)
    pdf.set_font("DejaVu", "", 7.5)
    pdf.set_text_color(60, 60, 60)
    
    notes = [
        "• Experimental metrics (🔬) use heuristics that may produce false positives or negatives.",
        "• Housing time is reported as a range [lower, upper]. The true value lies between bounds.",
        "• Lower bound is conservative (only detects housing with house-building evidence).",
        "• Upper bound is liberal (overestimates in Castle/Imperial due to untracked combat deaths).",
        "• Aggregate averages use winsorized mean (10%) to reduce outlier impact.",
        "• Matches with values >2σ from mean are flagged as outliers in charts.",
        "• Data source: 1v1 matches preferred (≥5). TG included with warning if insufficient 1v1 data.",
        "• Replay parsing via mgz library. Some replay versions may have parsing limitations.",
        "• Experimental metrics may change in future methodology versions.",
    ]
    
    for note in notes:
        pdf.multi_cell(0, 3.5, note)
        pdf.ln(0.5)
    
    # Footer
    pdf.set_y(-15)
    pdf.set_font("DejaVu", "", 6)
    pdf.set_text_color(189, 195, 199)
    pdf.cell(0, 4, f"Agelytics Methodology v{METHODOLOGY_VERSION} — Full documentation: documentation/metrics-methodology.md", ln=True, align="C")


# Convenience: metrics typically used per report type
SCOUTING_METRICS = [
    "Win Rate", "Avg Metrics", "eAPM", "Age-up Times", "TC Idle Time",
    "Housed Time (Lower)", "Housed Time (Upper)", "TC Idle Effective",
    "Opening Strategy", "ELO (API)", "ELO (Replay)", "Death Count",
]

MATCH_REPORT_METRICS = [
    "TC Idle Time", "TC Idle by Era", "TC Idle Breakdown", "eAPM",
    "Age-up Times", "Housed Count", "Housed Time (Lower)", "Housed Time (Upper)",
    "TC Idle Effective", "Opening Strategy", "Wall Tiles", "Death Count",
]

DEEP_COACH_METRICS = MATCH_REPORT_METRICS  # Same base, coach adds narrative
