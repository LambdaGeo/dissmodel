"""
SIR Model — Streamlit
=====================
Deterministic SIR epidemiological model.

Susceptible individuals become infected through contact with infectious
individuals, then recover and gain immunity.

Usage
-----
    streamlit run examples/streamlit/sysdyn_sir.py
"""
from __future__ import annotations

import streamlit as st

from dissmodel.core import Environment
from examples.models.sysdyn import SIR
from dissmodel.visualization import Chart, display_inputs

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(page_title="SIR Model", layout="centered")
st.title("SIR Model (dissmodel)")

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
st.sidebar.title("Parameters")
steps = st.sidebar.slider("Simulation steps", min_value=1, max_value=100, value=30)
run   = st.button("Run Simulation")

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

# 2. Model
sir = SIR(
    susceptible=9998,
    infected=2,
    recovered=0,
    duration=2,
    contacts=6,
    probability=0.25,
)

# 3. Sidebar widgets — model-specific parameters rendered automatically
st.sidebar.markdown("---")
st.sidebar.markdown("**Model parameters**")
display_inputs(sir, st.sidebar)

# 4. Chart
Chart(
    show_legend=True,
    show_grid=True,
    title="SIR Model",
    plot_area=st.empty(),
)

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
if run:
    env.reset()
    env.run()
