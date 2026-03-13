"""
Fire Model — Streamlit
======================
Spatial cellular automaton simulating forest fire spread.

States
------
- Forest (0)  — healthy tree, can catch fire.
- Burning (1) — actively burning, spreads to neighbors.
- Burned (2)  — already burned, no longer spreads.

Usage
-----
    streamlit run examples/streamlit/ca_fire_model.py
"""
from __future__ import annotations

from matplotlib.colors import ListedColormap
import streamlit as st

from dissmodel.core import Environment
from dissmodel.geo import vector_grid
from dissmodel.models.ca import FireModel
from dissmodel.models.ca.fire_model import FireState
from dissmodel.visualization import display_inputs
from dissmodel.visualization.map import Map

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Fire Model", layout="centered")
st.title("Forest Fire Model (dissmodel)")

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
st.sidebar.title("Parameters")
steps     = st.sidebar.slider("Simulation steps", min_value=1, max_value=50, value=10)
grid_size = st.sidebar.slider("Grid size", min_value=5, max_value=100, value=20)
run       = st.button("Run Simulation")

# ---------------------------------------------------------------------------
# Setup
#
# Instantiation order matters:
#   1. Environment  — must exist before any model connects to it
#   2. Grid         — spatial structure shared between model and map
#   3. Model        — connects to the active environment on creation
#   4. display_inputs — reads annotated attributes and renders sidebar widgets,
#                       updating model parameters before initialization
#   5. initialize() — uses the parameters set by display_inputs to fill the grid
#   6. Map          — connects to the active environment and redraws each step
# ---------------------------------------------------------------------------

# 1. Environment
env = Environment(start_time=0, end_time=steps)

# 2. Grid
gdf = vector_grid(
    dimension=(grid_size, grid_size),
    resolution=1,
    attrs={"state": FireState.FOREST},
)

# 3. Model
fire = FireModel(gdf=gdf)

# 4. Sidebar widgets — must come before initialize()
#    so parameters are set before the grid is filled
display_inputs(fire, st.sidebar)

# 5. Initialize — uses parameters updated by display_inputs
fire.initialize()

# 6. Map
cmap = ListedColormap(["green", "red", "brown"])  # Forest, Burning, Burned
Map(
    gdf=gdf,
    plot_params={"column": "state", "cmap": cmap, "ec": "black"},
    plot_area=st.empty(),
)

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
if run:
    env.reset()
    env.run()
