"""
Fire Model Probabilistic — Streamlit
=====================================
Probabilistic cellular automaton simulating forest fire spread.

Unlike the basic Fire Model, fire starts spontaneously via
``prob_combustion`` — no explicit initialization needed.

States
------
- Forest (0)  — healthy tree, can catch fire spontaneously.
- Burning (1) — actively burning, spreads to neighbors.
- Burned (2)  — already burned, can regrow as forest.

Usage
-----
    streamlit run examples/streamlit/ca_fire_model_prob.py
"""
from __future__ import annotations

from matplotlib.colors import ListedColormap
import streamlit as st

from dissmodel.core import Environment
from dissmodel.geo import vector_grid
from dissmodel.models.ca import FireModelProb
from dissmodel.models.ca.fire_model import FireState
from dissmodel.visualization import display_inputs
from dissmodel.visualization import Map

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Fire Model (Probabilistic)", layout="centered")
st.title("Probabilistic Forest Fire Model (dissmodel)")

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
#   1. Environment    — must exist before any model connects to it
#   2. Grid           — spatial structure shared between model and map
#   3. Model          — connects to the active environment on creation
#   4. display_inputs — reads annotated attributes and renders sidebar widgets
#                       updating model parameters (prob_combustion, prob_regrowth)
#   5. Map            — connects to the active environment and redraws each step
#
# Note: no initialize() needed — fire starts spontaneously via prob_combustion
# ---------------------------------------------------------------------------

# 1. Environment
env = Environment(start_time=0, end_time=steps)

# 2. Grid — all cells start as forest
gdf = vector_grid(
    dimension=(grid_size, grid_size),
    resolution=1,
    attrs={"state": FireState.FOREST},
)

# 3. Model
fire = FireModelProb(gdf=gdf)

# 4. Sidebar widgets — updates prob_combustion and prob_regrowth before run
display_inputs(fire, st.sidebar)

# 5. Map
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
