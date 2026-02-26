"""
Game of Life — Streamlit
========================
Spatial cellular automaton based on Conway's Game of Life.

Rules
-----
- A live cell with 2 or 3 live neighbors survives.
- A dead cell with exactly 3 live neighbors becomes alive.
- All other cells die or remain dead.

Usage
-----
    streamlit run examples/streamlit/ca_game_of_life.py
"""
from __future__ import annotations

from matplotlib.colors import ListedColormap
import streamlit as st

from dissmodel.core import Environment
from dissmodel.geo import regular_grid
from dissmodel.models.ca import GameOfLife
from dissmodel.models.ca.game_of_life import PATTERNS
from dissmodel.visualization.map import Map

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Game of Life", layout="centered")
st.title("Game of Life (dissmodel)")

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
st.sidebar.title("Parameters")

steps     = st.sidebar.slider("Simulation steps", min_value=1, max_value=50, value=10)
grid_size = st.sidebar.slider("Grid size", min_value=5, max_value=50, value=20)
init_mode = st.sidebar.radio("Initialization", ["Random", "Patterns"])

selected_patterns = []
if init_mode == "Patterns":
    selected_patterns = st.sidebar.multiselect(
        "Select patterns",
        options=list(PATTERNS.keys()),
        default=["glider", "blinker", "toad", "beacon"],
    )

run = st.button("Run Simulation")

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
gdf = regular_grid(dimension=(grid_size, grid_size), resolution=1, attrs={"state": 0})
env = Environment(start_time=0, end_time=steps)

gol = GameOfLife(gdf=gdf)
if init_mode == "Random":
    gol.initialize()
else:
    gol.initialize_patterns(patterns=selected_patterns or None)

cmap = ListedColormap(["white", "black"])
plot_area = st.empty()

Map(
    gdf=gdf,
    plot_params={"column": "state", "cmap": cmap, "ec": "gray"},
    plot_area=plot_area,
)

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
if run:
    env.reset()
    env.run()
