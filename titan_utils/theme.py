"""Theme constants — single source of truth for the Titan dark theme."""

THEME = {
    "bg_main": "#0a0e17",
    "bg_card": "#1a1f2e",
    "bg_hover": "#222838",
    "gold": "#d4af37",
    "cyan": "#66fcf1",
    "red": "#ff0055",
    "green": "#1dd1a1",
    "text": "#e0e0e0",
    "muted": "#8b9bb4",
}

# CSS injected at the top of every page to ensure consistent look.
TITAN_THEME_CSS = f"""
<style>
    .stApp {{ background-color: {THEME['bg_main']}; }}
    .main {{ background-color: {THEME['bg_main']}; }}
    h1, h2, h3, h4 {{ color: {THEME['gold']} !important; }}
    [data-testid="stSidebar"] {{ background-color: {THEME['bg_card']}; }}
    .stButton>button {{
        background-color: {THEME['gold']};
        color: {THEME['bg_main']};
        border: none;
        font-weight: bold;
    }}
    .stButton>button:hover {{
        background-color: #b8952f;
        color: {THEME['bg_main']};
    }}
    /* Metric cards */
    [data-testid="stMetricValue"] {{ color: {THEME['gold']} !important; }}
    /* Code blocks */
    code {{ color: {THEME['cyan']} !important; }}
</style>
"""
