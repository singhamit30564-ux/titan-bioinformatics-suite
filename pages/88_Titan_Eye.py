"""🌍 Titan's Eye Globe — Interactive 3D globe with toggleable data layers.

Uses Plotly's scattergeo for a static 3D globe view with:
- Demo earthquake data (USGS-style, static)
- Demo weather events (static)
- Demo Titan user locations (labelled as demo)
All data is static / embedded — no live API.
"""
from __future__ import annotations

import json
import random

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from titan_utils.i18n import t
from titan_utils.ui import dr_titan_tip, titan_title

titan_title(
    "🌍",
    "Titan's Eye Globe",
    "Explore a 3D interactive globe with toggleable layers: earthquakes, weather events, and Titan community locations.",
)

# ── Static demo data ─────────────────────────────────────────────────────────

@st.cache_data
def _load_earthquake_data() -> pd.DataFrame:
    """Static demo earthquake data (USGS-style, illustrative only)."""
    return pd.DataFrame([
        {"lat": 35.68, "lon": 139.69, "mag": 7.2, "place": "Tokyo, Japan", "depth_km": 60},
        {"lat": 28.23, "lon": 84.73, "mag": 7.8, "place": "Gorkha, Nepal", "depth_km": 8},
        {"lat": -33.45, "lon": -70.67, "mag": 6.9, "place": "Santiago, Chile", "depth_km": 25},
        {"lat": 37.77, "lon": -122.42, "mag": 6.0, "place": "San Francisco, USA", "depth_km": 12},
        {"lat": 38.72, "lon": 20.73, "mag": 6.5, "place": "Lefkada, Greece", "depth_km": 10},
        {"lat": -8.50, "lon": 115.50, "mag": 6.3, "place": "Bali, Indonesia", "depth_km": 35},
        {"lat": 23.42, "lon": 45.08, "mag": 5.8, "place": "Riyadh, Saudi Arabia", "depth_km": 20},
        {"lat": 51.75, "lon": -1.25, "mag": 4.5, "place": "Oxford, UK", "depth_km": 5},
        {"lat": 19.08, "lon": 72.88, "mag": 5.5, "place": "Mumbai, India", "depth_km": 15},
        {"lat": -22.91, "lon": -43.17, "mag": 5.0, "place": "Rio de Janeiro, Brazil", "depth_km": 30},
        {"lat": 55.76, "lon": 37.62, "mag": 4.8, "place": "Moscow, Russia", "depth_km": 22},
        {"lat": 31.23, "lon": 121.47, "mag": 5.2, "place": "Shanghai, China", "depth_km": 18},
    ])


@st.cache_data
def _load_weather_data() -> pd.DataFrame:
    """Static demo weather event data."""
    return pd.DataFrame([
        {"lat": 25.76, "lon": -80.19, "event": "Hurricane Milton (Cat 3)", "type": "cyclone"},
        {"lat": 22.57, "lon": 88.36, "event": "Cyclone Amphan landfall", "type": "cyclone"},
        {"lat": 35.68, "lon": 139.69, "event": "Heatwave 40°C+", "type": "heatwave"},
        {"lat": -34.60, "lon": -58.38, "event": "Record flooding in Buenos Aires", "type": "flood"},
        {"lat": 64.15, "lon": -21.94, "event": "Volcanic eruption near Reykjavik", "type": "volcanic"},
        {"lat": 34.05, "lon": -118.24, "event": "Wildfire alert — Los Angeles", "type": "wildfire"},
        {"lat": 48.86, "lon": 2.35, "event": "Severe thunderstorm warning — Paris", "type": "storm"},
        {"lat": -37.81, "lon": 144.96, "event": "Bushfire risk — Melbourne", "type": "wildfire"},
    ])


@st.cache_data
def _load_user_locations() -> pd.DataFrame:
    """Fake demo data for Titan user locations (clearly labelled)."""
    return pd.DataFrame([
        {"lat": 28.61, "lon": 77.21, "city": "New Delhi", "users": 1200, "label": "demo"},
        {"lat": 19.08, "lon": 72.88, "city": "Mumbai", "users": 950, "label": "demo"},
        {"lat": 40.71, "lon": -74.01, "city": "New York", "users": 800, "label": "demo"},
        {"lat": 51.51, "lon": -0.13, "city": "London", "users": 720, "label": "demo"},
        {"lat": 35.68, "lon": 139.69, "city": "Tokyo", "users": 600, "label": "demo"},
        {"lat": -33.87, "lon": 151.21, "city": "Sydney", "users": 480, "label": "demo"},
        {"lat": 37.57, "lon": 126.98, "city": "Seoul", "users": 550, "label": "demo"},
        {"lat": 48.86, "lon": 2.35, "city": "Paris", "users": 610, "label": "demo"},
        {"lat": 52.52, "lon": 13.41, "city": "Berlin", "users": 430, "label": "demo"},
        {"lat": -23.55, "lon": -46.63, "city": "São Paulo", "users": 370, "label": "demo"},
        {"lat": 12.97, "lon": 77.59, "city": "Bangalore", "users": 1100, "label": "demo"},
        {"lat": 23.02, "lon": 72.57, "city": "Ahmedabad", "users": 400, "label": "demo"},
    ])


# ── Layer toggles ────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)
with col1:
    show_quakes = st.toggle(t("🌍 Earthquakes"), value=True)
with col2:
    show_weather = st.toggle(t("🌦️ Weather Events"), value=True)
with col3:
    show_users = st.toggle(t("👥 Titan Users (demo)"), value=True)

# ── Build globe ──────────────────────────────────────────────────────────────
fig = go.Figure()

if show_quakes:
    eq = _load_earthquake_data()
    fig.add_trace(go.Scattergeo(
        lat=eq["lat"], lon=eq["lon"],
        text=eq["place"] + "<br>Magnitude: " + eq["mag"].astype(str),
        marker=dict(
            size=eq["mag"] * 4,
            color=eq["mag"],
            colorscale="Reds",
            opacity=0.8,
            line=dict(width=0.5, color="white"),
        ),
        name="🔴 Earthquakes",
        hoverinfo="text",
    ))

if show_weather:
    wx = _load_weather_data()
    wx_colors = {"cyclone": "blue", "heatwave": "red", "flood": "cyan", "volcanic": "orange", "wildfire": "yellow", "storm": "purple"}
    fig.add_trace(go.Scattergeo(
        lat=wx["lat"], lon=wx["lon"],
        text=wx["event"],
        marker=dict(
            size=14,
            color=[wx_colors.get(t, "white") for t in wx["type"]],
            symbol="diamond",
            opacity=0.9,
            line=dict(width=1, color="white"),
        ),
        name="🌦️ Weather Events",
        hoverinfo="text",
    ))

if show_users:
    users = _load_user_locations()
    fig.add_trace(go.Scattergeo(
        lat=users["lat"], lon=users["lon"],
        text=users["city"] + "<br>Users: " + users["users"].astype(str) + " (demo data)",
        marker=dict(
            size=users["users"] / 40,
            color="#66fcf1",
            opacity=0.7,
            line=dict(width=1, color="white"),
        ),
        name="👥 Titan Users (demo)",
        hoverinfo="text",
    ))

fig.update_geos(
    projection_type="orthographic",
    showland=True,
    landcolor="#1a1f2e",
    showocean=True,
    oceancolor="#0a0e17",
    showcountries=True,
    countrycolor="#333",
    bgcolor="#0a0e17",
)
fig.update_layout(
    height=600,
    margin=dict(l=0, r=0, t=0, b=0),
    paper_bgcolor="#0a0e17",
    plot_bgcolor="#0a0e17",
    font_color="#e0e0e0",
    legend=dict(bgcolor="rgba(0,0,0,0.5)", font=dict(color="#e0e0e0")),
    geo=dict(bgcolor="#0a0e17"),
)

st.plotly_chart(fig, use_container_width=True)

st.caption(t(
    "ℹ️ All data is **static / demo** — earthquake data is illustrative (not live USGS), "
    "user locations are simulated, and weather events are curated examples."
))

st.markdown("---")
st.caption(t("🌎 *Inspired by God's Eye View — seeing the whole planet from above.*"))
st.caption(t("🧭 Rotate and zoom the globe — it works on mobile too!"))

dr_titan_tip(
    "Satellite data and GIS (Geographic Information Systems) are increasingly used in bioinformatics — "
    "from tracking disease outbreaks to monitoring biodiversity with remote sensing!"
)