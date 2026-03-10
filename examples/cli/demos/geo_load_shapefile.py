"""
Load Shapefile — CLI
====================
Demonstrates how to load geographic data from a file and
visualize it using dissmodel's Map component.

Usage
-----
    python examples/cli/geo_load_shapefile.py
"""
from __future__ import annotations

import geopandas as gpd

from dissmodel.core import Environment
from dissmodel.visualization.map import Map

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
gdf = gpd.read_file("examples/data/ilha_do_maranhao.zip")

env = Environment(start_time=0, end_time=1)

Map(
    gdf=gdf,
    plot_params={"edgecolor": "black", "linewidth": 0.5},
)

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
env.run()
