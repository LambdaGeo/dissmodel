"""
System Dynamics Explorer — Streamlit
=====================================
Dynamically loads all system dynamics models from ``dissmodel.models.sysdyn``
and lets the user choose, configure, and run any of them from a single
interface.

This is possible because all models follow the same conventions:
- Annotated attributes (``param: float``) are picked up by ``display_inputs``
  and rendered as sidebar widgets automatically.
- ``@track_plot`` decorators register variables for automatic live plotting.

Usage
-----
    streamlit run examples/streamlit/run_all_sysdyn.py
"""
from __future__ import annotations

import inspect

import streamlit as st

import dissmodel.models.sysdyn as sysdyn_models
from dissmodel.core import Environment, Model
from dissmodel.visualization import Chart, display_inputs

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(page_title="SysDyn Explorer", layout="centered")
st.title("System Dynamics Explorer (dissmodel)")

# ---------------------------------------------------------------------------
# Discover models — only concrete Model subclasses
# ---------------------------------------------------------------------------
model_classes: dict[str, type] = {
    name: cls
    for name, cls in inspect.getmembers(sysdyn_models, inspect.isclass)
    if issubclass(cls, Model)
    and cls is not Model
    and not inspect.isabstract(cls)
}

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
st.sidebar.title("Parameters")

model_name = st.sidebar.selectbox("Model", list(model_classes.keys()))
steps      = st.sidebar.slider("Simulation steps", min_value=1, max_value=1000, value=30)
run        = st.button("Run Simulation")

# ---------------------------------------------------------------------------
# Setup
#
# Instantiation order matters:
#   1. Environment    — must exist before any model connects to it
#   2. Model          — connects to the active environment on creation
#   3. display_inputs — reads annotated attributes → renders sidebar widgets
#   4. Chart          — connects to the active environment, redraws each step
# ---------------------------------------------------------------------------

# 1. Environment
env = Environment(start_time=0, end_time=steps)

# 2. Model — instantiated dynamically from sidebar selection
ModelClass = model_classes[model_name]
model = ModelClass()

# 3. Sidebar widgets — model-specific parameters rendered automatically
st.sidebar.markdown("---")
st.sidebar.markdown(f"**{model_name} parameters**")
display_inputs(model, st.sidebar)

# 4. Chart
Chart(
    show_legend=True,
    show_grid=True,
    title=f"{model_name}",
    plot_area=st.empty(),
)

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
if run:
    env.reset()
    env.run()
