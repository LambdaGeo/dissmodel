
"""
Game of Life — CLI example
===========================
Spatial cellular automaton based on Conway's Game of Life.

Rules
-----
- A live cell with 2 or 3 live neighbors survives.
- A dead cell with exactly 3 live neighbors becomes alive.
- All other cells die or remain dead.

Usage
-----
    python examples/cli/ca_game_of_life.py
"""
from __future__ import annotations

from matplotlib.colors import ListedColormap

from dissmodel.core import Environment
from dissmodel.geo import regular_grid
from dissmodel.models.ca import GameOfLife
from dissmodel.visualization.map import Map

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
gdf = regular_grid(dimension=(20, 20), resolution=1, attrs={"state": 0})

env = Environment(start_time=0, end_time=10)

gol = GameOfLife(gdf=gdf)
gol.initialize()

# ---------------------------------------------------------------------------
# Visualization
# ---------------------------------------------------------------------------
cmap = ListedColormap(["white", "black"])
Map(
    gdf=gdf,
    plot_params={"column": "state", "cmap": cmap, "ec": "gray"},
)

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
env.run()
