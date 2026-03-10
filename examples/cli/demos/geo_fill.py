"""
Fill Strategy — RANDOM_SAMPLE
==============================
Demonstrates how to fill a grid attribute with values sampled
from a probability distribution using ``FillStrategy.RANDOM_SAMPLE``.

Each cell in the grid is assigned one of the provided values
according to the specified probabilities.

Usage
-----
    python examples/cli/geo_fill.py
"""
from __future__ import annotations

import matplotlib.pyplot as plt

from dissmodel.geo import FillStrategy, fill, regular_grid

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
grid = regular_grid(dimension=(5, 5), resolution=1.0)

fill(
    strategy=FillStrategy.RANDOM_SAMPLE,
    gdf=grid,
    attr="risk",
    data={
        "low":    0.2,
        "medium": 0.5,
        "high":   0.3,
    },
    seed=42,
)

# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------
print(grid[["risk"]])

grid.plot(column="risk", legend=True)
plt.title("Risk distribution (RANDOM_SAMPLE)")
plt.show()
