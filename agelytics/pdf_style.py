"""Matplotlib style configuration for Agelytics PDF reports."""

import matplotlib.pyplot as plt


# Color palette inspired by Power BI professional dashboards
COLORS = {
    'bg': '#FFFFFF',
    'primary_dark': '#3B3B3B',
    'primary_blue': '#2C3E50',
    'accent_orange': '#E67E22',
    'accent_yellow': '#F1C40F',
    'text_primary': '#2C3E50',
    'text_secondary': '#7F8C8D',
    'edge_color': '#BDC3C7',
    'grid_color': '#ECF0F1',
    'bar_gradient_start': '#3B3B3B',
    'bar_gradient_end': '#5D6D7E',
    'victory': '#27AE60',
    'defeat': '#E74C3C',
}


def apply_agelytics_style():
    """Apply Power BI-inspired clean theme to matplotlib."""
    plt.rcParams.update({
        'figure.facecolor': COLORS['bg'],
        'axes.facecolor': COLORS['bg'],
        'axes.edgecolor': COLORS['edge_color'],
        'axes.labelcolor': COLORS['text_primary'],
        'text.color': COLORS['text_primary'],
        'xtick.color': COLORS['text_secondary'],
        'ytick.color': COLORS['text_secondary'],
        'grid.color': COLORS['grid_color'],
        'grid.alpha': 0.5,
        'font.family': 'sans-serif',
        'font.sans-serif': ['DejaVu Sans', 'Helvetica', 'Arial'],
        'axes.spines.top': False,
        'axes.spines.right': False,
        'axes.grid': True,
        'axes.axisbelow': True,
    })


def get_player_colors(num_players=2):
    """Get contrasting colors for players."""
    if num_players == 2:
        return [COLORS['primary_blue'], COLORS['accent_orange']]
    else:
        # For more players, return a gradient
        colors = []
        for i in range(num_players):
            alpha = i / max(1, num_players - 1)
            # Interpolate between primary_blue and accent_orange
            colors.append(f'#{int(0x2C + alpha * (0xE6 - 0x2C)):02X}'
                         f'{int(0x3E + alpha * (0x7E - 0x3E)):02X}'
                         f'{int(0x50 + alpha * (0x22 - 0x50)):02X}')
        return colors
