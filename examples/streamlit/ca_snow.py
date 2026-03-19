"""
Snow Model — Streamlit
======================
Cellular automaton simulating snowfall and accumulation.

Snow falls from the top row and moves downward one cell per step.
When a snowflake reaches the bottom or lands on top of another,
it accumulates.

Notes
-----
Simulation steps should be greater than the grid size, otherwise
snow will not have enough time to fall and accumulate.
A good rule of thumb: steps > grid_size.

Usage
-----
    streamlit run examples/streamlit/ca_snow.py
"""
from __future__ import annotations

import matplotlib.pyplot as plt
import streamlit as st

from dissmodel.core import Environment
from dissmodel.geo import vector_grid
from dissmodel.models.ca.snow import Snow, SnowState
from dissmodel.visualization import Map
from dissmodel.visualization.widgets import display_inputs

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Snow Model", layout="centered")
st.title("Snow Model (dissmodel)")

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
st.sidebar.title("Parameters")
steps     = st.sidebar.slider("Simulation steps", min_value=1, max_value=100, value=30)
grid_size = st.sidebar.slider("Grid size", min_value=5, max_value=50, value=20)

if steps <= grid_size:
    st.sidebar.warning(
        f"⚠️ Simulation steps ({steps}) should be greater than "
        f"grid size ({grid_size}) for snow to fall and accumulate."
    )

cmap_name = st.sidebar.selectbox(
    "Colormap",
    ["Blues", "coolwarm", "viridis", "plasma", "Greens", "tab10"],
)
run = st.button("Run Simulation")

# ---------------------------------------------------------------------------
# Setup
#
# Instantiation order matters:
#   1. Environment  — must exist before any model connects to it
#   2. Grid         — spatial structure shared between model and map
#   3. Model        — connects to the active environment on creation
#   4. display_inputs — reads annotated attributes and renders sidebar widgets
#   5. Map          — connects to the active environment and redraws each step
# ---------------------------------------------------------------------------

# 1. Environment
env = Environment(start_time=0, end_time=steps)

# 2. Grid — all cells start empty
gdf = vector_grid(
    dimension=(grid_size, grid_size),
    resolution=1,
    attrs={"state": SnowState.EMPTY},
)

# 3. Model
snow = Snow(gdf=gdf, dim=grid_size, start_time=0, end_time=steps)

# 4. Sidebar widgets — updates model parameters before run
display_inputs(snow, st.sidebar)

# 5. Map
cmap = plt.get_cmap(cmap_name)
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
