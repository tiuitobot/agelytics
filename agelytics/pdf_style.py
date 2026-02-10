"""Visual style configuration for Agelytics PDF reports.

Uses seaborn for consistent, professional chart styling.
"""

import matplotlib.pyplot as plt
import seaborn as sns

# Color palette — dark professional theme
COLORS = {
    "bg": "#FFFFFF",
    "text_primary": "#2C3E50",
    "text_secondary": "#7F8C8D",
    "edge_color": "#BDC3C7",
    "grid_color": "#ECF0F1",
    "victory": "#27AE60",
    "defeat": "#E74C3C",
    "accent_orange": "#E67E22",
    "warning": "#F39C12",
}

# Seaborn palette for players (max 8)
PLAYER_PALETTE = sns.color_palette("deep", 8)


def apply_style():
    """Apply seaborn + custom tweaks for clean charts."""
    sns.set_theme(
        style="whitegrid",
        palette="deep",
        font_scale=0.95,
        rc={
            "figure.facecolor": COLORS["bg"],
            "axes.facecolor": COLORS["bg"],
            "axes.edgecolor": COLORS["edge_color"],
            "axes.labelcolor": COLORS["text_primary"],
            "text.color": COLORS["text_primary"],
            "xtick.color": COLORS["text_secondary"],
            "ytick.color": COLORS["text_secondary"],
            "grid.color": COLORS["grid_color"],
            "grid.alpha": 0.4,
            "axes.spines.top": False,
            "axes.spines.right": False,
        },
    )


def get_player_colors(n=2):
    """Return n contrasting colors for players."""
    return list(PLAYER_PALETTE[:n])
