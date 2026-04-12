"""
Cellular Automata Explorer — Streamlit
=======================================
Dynamically loads all cellular automaton models from ``examples.models.ca``
and lets the user choose, configure, and run any of them from a single
interface.

This is possible because all models follow the same conventions:
- Annotated attributes (``param: float``) are picked up by ``display_inputs``
  and rendered as sidebar widgets automatically.
- ``initialize()`` uses the parameters set by ``display_inputs``.
- ``execute()`` applies ``rule()`` to every cell each step.

Usage
-----
    streamlit run examples/streamlit/ca_all.py
"""
from __future__ import annotations

import inspect

import matplotlib.pyplot as plt
import streamlit as st

import examples.models.ca as ca_models
from dissmodel.core import Environment
from dissmodel.geo import CellularAutomaton, vector_grid
from dissmodel.visualization import Map
from dissmodel.visualization.widgets import display_inputs

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(page_title="CA Explorer", layout="centered")
st.title("Cellular Automata Explorer (dissmodel)")

# ---------------------------------------------------------------------------
# Discover models — only concrete CellularAutomaton subclasses
# ---------------------------------------------------------------------------
model_classes: dict[str, type] = {
    name: cls
    for name, cls in inspect.getmembers(ca_models, inspect.isclass)
    if issubclass(cls, CellularAutomaton)
    and cls is not CellularAutomaton
    and not inspect.isabstract(cls)
}

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
st.sidebar.title("Parameters")

model_name = st.sidebar.selectbox("Model", list(model_classes.keys()))
steps      = st.sidebar.slider("Simulation steps", min_value=1, max_value=1000, value=50)
grid_size  = st.sidebar.slider("Grid size", min_value=5, max_value=100, value=20)
cmap_name  = st.sidebar.selectbox(
    "Colormap",
    ["tab10", "viridis", "plasma", "Greens", "Reds", "Blues", "coolwarm"],
)
run = st.button("Run Simulation")

# ---------------------------------------------------------------------------
# Setup
#
# Instantiation order matters:
#   1. Environment    — must exist before any model connects to it
#   2. Grid           — spatial structure shared between model and map
#   3. Model          — connects to the active environment on creation
#   4. display_inputs — reads annotated attributes → renders sidebar widgets
#   5. initialize()   — uses parameters set by display_inputs to fill the grid
#   6. Map            — connects to the active environment, redraws each step
# ---------------------------------------------------------------------------

# 1. Environment
env = Environment(start_time=0, end_time=steps)

# 2. Grid
gdf = vector_grid(
    dimension=(grid_size, grid_size),
    resolution=1,
    attrs={"state": 0},
)

# 3. Model — instantiated dynamically from sidebar selection
ModelClass = model_classes[model_name]
model = ModelClass(gdf=gdf, dim=grid_size, start_time=0, end_time=steps)

# 4. Sidebar widgets — model-specific parameters rendered automatically
st.sidebar.markdown("---")
st.sidebar.markdown(f"**{model_name} parameters**")
display_inputs(model, st.sidebar)

# 5. Initialize — uses parameters updated by display_inputs
model.initialize()

# 6. Map
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
