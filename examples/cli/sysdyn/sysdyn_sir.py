"""
SIR Model — CLI
===============
Deterministic SIR epidemiological model.

Susceptible individuals become infected through contact with infectious
individuals, then recover and gain immunity.

Usage
-----
    python examples/cli/sysdyn_sir.py
"""
from __future__ import annotations

from dissmodel.core import Environment
from examples.models.sysdyn import SIR
from dissmodel.visualization import Chart

# ---------------------------------------------------------------------------
# Setup
#
# Instantiation order matters:
#   1. Environment — must exist before any model connects to it
#   2. Model       — connects to the active environment on creation
#   3. Chart       — connects to the active environment and redraws each step
# ---------------------------------------------------------------------------

# 1. Environment
env = Environment()

# 2. Model
SIR(
    susceptible=9998,
    infected=2,
    recovered=0,
    duration=2,
    contacts=6,
    probability=0.25,
)

# 3. Chart
Chart(show_legend=True, show_grid=True, title="SIR Model")

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
env.run(30)
