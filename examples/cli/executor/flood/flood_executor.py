# services/worker/executors/flood_vector.py
from __future__ import annotations

import io
import os
import tempfile

import geopandas as gpd

from dissmodel.executor    import ModelExecutor
from dissmodel.executor import ExperimentRecord
from .flood_model import FloodModel

from dissmodel.io import load_dataset, save_dataset

from dissmodel.executor.cli import run_cli
from dissmodel.visualization import Map

from matplotlib.colors import ListedColormap, BoundaryNorm



from .constants import (
    USO_COLORS, USO_LABELS,
    SOLO_COLORS, SOLO_LABELS,
)

_vals    = sorted(USO_COLORS)
USO_CMAP = ListedColormap([USO_COLORS[k] for k in _vals])
USO_NORM = BoundaryNorm([v - 0.5 for v in _vals] + [_vals[-1] + 0.5], USO_CMAP.N)

_svals    = sorted(SOLO_COLORS)
SOLO_CMAP = ListedColormap([SOLO_COLORS[k] for k in _svals])
SOLO_NORM = BoundaryNorm([v - 0.5 for v in _svals] + [_svals[-1] + 0.5], SOLO_CMAP.N)



class FloodVectorExecutor(ModelExecutor):
    """
    Executor for the vector-based hydrological flood model.

    Wraps the FloodModel developed and tested in Jupyter,
    without requiring the coastal_dynamics package.
    Input: shapefile / GeoJSON / GPKG / zipped shapefile from MinIO.
    Output: GPKG saved to dissmodel-outputs.
    """

    name = "flood_vector"

    # ── Load ──────────────────────────────────────────────────────────────────

    # services/worker/executors/flood_vector.py

    def load(self, record: ExperimentRecord):
        gdf, checksum          = load_dataset(record.source.uri)
        record.source.checksum = checksum
        if record.column_map:
            gdf = gdf.rename(columns={v: k for k, v in record.column_map.items()})
        record.add_log(f"Loaded GDF: {len(gdf)} features")
        return gdf

    # ── Validate ──────────────────────────────────────────────────────────────

    def validate(self, record: ExperimentRecord) -> None:
        pass
    # ── Run ───────────────────────────────────────────────────────────────────

    def run(self, record: ExperimentRecord) -> gpd.GeoDataFrame:
        from dissmodel.core import Environment

        print ("iniciando")

        params   = record.parameters
        end_time = params.get("end_time", 10)

        gdf = self.load(record)

        env = Environment(
            start_time = params.get("start_time", 1),
            end_time   = end_time,
        )

        flood = FloodModel(
            gdf           = gdf,
            taxa_elevacao = params.get("taxa_elevacao", 0.5),
            attr_uso      = params.get("attr_uso", "uso"),
            attr_alt      = params.get("attr_alt", "alt"),
        )

        Map(gdf=gdf, plot_params={"column": flood.attr_uso,  "cmap": USO_CMAP,  "norm": USO_NORM,  "legend": False})
        
        record.add_log(f"Running {end_time} steps...")
        env.run()
        record.add_log("Simulation complete")

        return gdf

    # ── Save ──────────────────────────────────────────────────────────────────

    def save(self, result: gpd.GeoDataFrame, record: ExperimentRecord) -> ExperimentRecord:
        path = f"experiments/{record.experiment_id}/output.gpkg"
        
        record.output_path   = path
        #record.output_sha256 = _sha256(result)
        record.status        = "completed"
        return record


if __name__ == "__main__":
    run_cli(FloodVectorExecutor)