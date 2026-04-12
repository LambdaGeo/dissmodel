"""
Game of Life — CLI example (raster)
=====================================
Raster version of the Game of Life using RasterCellularAutomaton + RasterMap.

Same rules as the vector version, fully vectorized over NumPy arrays.

Usage
-----
    python examples/cli/ca_game_of_life_raster.py
    RASTER_MAP_INTERACTIVE=1 python examples/cli/ca_game_of_life_raster.py
"""
from __future__ import annotations

from dissmodel.core import Environment
from dissmodel.geo import raster_grid
from examples.models.ca.game_of_life_raster import GameOfLife
from dissmodel.visualization.raster_map import RasterMap

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
b = raster_grid(rows=1000, cols=1000, attrs={"state": 0})

env = Environment(start_time=0, end_time=10)

gol = GameOfLife(backend=b)
gol.initialize()

# ---------------------------------------------------------------------------
# Visualization
# ---------------------------------------------------------------------------
RasterMap(
    backend   = b,
    band      = "state",
    color_map = {0: "#ffffff", 1: "#000000"},
    labels    = {0: "dead", 1: "alive"},
    title     = "Game of Life",
)

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
env.run()
