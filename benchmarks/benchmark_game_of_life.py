"""
examples/notebooks/benchmark_game_of_life.py
=============================================
Benchmark: CellularAutomaton (vector) vs RasterCellularAutomaton (raster)
using Conway's Game of Life as the test model.

GameOfLife is ideal for benchmarking because:
- No domain dependencies — runs with dissmodel only
- Deterministic rules — cell-by-cell validation is exact (no floating point)
- Same rule expressed in both substrates — isolates substrate overhead

Usage
-----
    python benchmark_game_of_life.py
    python benchmark_game_of_life.py --steps 20
    python benchmark_game_of_life.py --sizes 10 50 100 200
    python benchmark_game_of_life.py --no-validation
"""
from __future__ import annotations

import argparse
import time
from dataclasses import dataclass, field

import numpy as np
import geopandas as gpd
import pandas as pd

from dissmodel.core import Environment
from dissmodel.geo.vector.cellular_automaton import CellularAutomaton
from dissmodel.geo.raster.backend import RasterBackend
from dissmodel.geo.raster.cellular_automaton import RasterCellularAutomaton
from dissmodel.geo import regular_grid
from dissmodel.geo.raster.regular_grid import make_raster_grid


# ══════════════════════════════════════════════════════════════════════════════
# GAME OF LIFE — VECTOR
# ══════════════════════════════════════════════════════════════════════════════

class GameOfLifeVector(CellularAutomaton):
    """Conway's Game of Life — vector substrate (rule per cell)."""

    def rule(self, idx):
        state     = self.gdf.loc[idx, self.state_attr]
        neighbors = (self.neighbor_values(idx, self.state_attr) == 1).sum()
        if state == 1:
            return 1 if neighbors in (2, 3) else 0
        return 1 if neighbors == 3 else 0


# ══════════════════════════════════════════════════════════════════════════════
# GAME OF LIFE — RASTER
# ══════════════════════════════════════════════════════════════════════════════

class GameOfLifeRaster(RasterCellularAutomaton):
    """Conway's Game of Life — raster substrate (vectorized over full grid)."""

    def rule(self, arrays):
        state     = arrays[self.state_attr]
        neighbors = self.backend.focal_sum_mask(state == 1)
        survive   = (state == 1) & np.isin(neighbors, [2, 3])
        born      = (state == 0) & (neighbors == 3)
        return {self.state_attr: np.where(survive | born, 1, 0).astype(np.int8)}


# ══════════════════════════════════════════════════════════════════════════════
# GRID FACTORIES — same initial state for both substrates
# ══════════════════════════════════════════════════════════════════════════════

def make_initial_state(rows: int, cols: int, seed: int = 42) -> np.ndarray:
    """Shared initial state — ensures both substrates start identically."""
    rng = np.random.default_rng(seed)
    return (rng.random((rows, cols)) < 0.3).astype(np.int8)


def make_vector_grid(rows: int, cols: int, seed: int = 42) -> gpd.GeoDataFrame:
    state = make_initial_state(rows, cols, seed).ravel().astype(int)
    gdf   = regular_grid(dimension=(cols, rows), resolution=1, attrs={"state": 0})
    gdf["state"] = state
    return gdf


def make_raster_grid_gol(rows: int, cols: int, seed: int = 42) -> RasterBackend:
    state = make_initial_state(rows, cols, seed)
    return make_raster_grid(rows=rows, cols=cols, attrs={"state": state})


# ══════════════════════════════════════════════════════════════════════════════
# RESULT
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class BenchResult:
    label:        str
    rows:         int
    cols:         int
    steps:        int
    total_s:      float
    per_step_ms:  float
    state_final:  np.ndarray = field(repr=False)


# ══════════════════════════════════════════════════════════════════════════════
# RUNNERS
# ══════════════════════════════════════════════════════════════════════════════

def run_vector(rows: int, cols: int, steps: int, seed: int = 42) -> BenchResult:
    from libpysal.weights import Queen
    gdf = make_vector_grid(rows, cols, seed)
    env = Environment(start_time=1, end_time=steps)
    ca  = GameOfLifeVector(gdf=gdf)
    ca.create_neighborhood(strategy=Queen, use_index=True)

    t0 = time.perf_counter()
    env.run()
    elapsed = time.perf_counter() - t0

    return BenchResult(
        label="vector", rows=rows, cols=cols, steps=steps,
        total_s=elapsed, per_step_ms=elapsed / steps * 1000,
        state_final=gdf["state"].values.reshape(rows, cols).astype(np.int8),
    )


def run_raster(rows: int, cols: int, steps: int, seed: int = 42) -> BenchResult:
    b   = make_raster_grid_gol(rows, cols, seed)
    env = Environment(start_time=1, end_time=steps)
    GameOfLifeRaster(backend=b)

    t0 = time.perf_counter()
    env.run()
    elapsed = time.perf_counter() - t0

    return BenchResult(
        label="raster", rows=rows, cols=cols, steps=steps,
        total_s=elapsed, per_step_ms=elapsed / steps * 1000,
        state_final=b.get("state").copy(),
    )


# ══════════════════════════════════════════════════════════════════════════════
# VALIDATION
# ══════════════════════════════════════════════════════════════════════════════

def validate(v: BenchResult, r: BenchResult) -> tuple[bool, float]:
    """
    Compare final state between vector and raster results.
    Returns (identical, % of matching cells).
    """
    match = v.state_final == r.state_final
    pct   = float(match.mean()) * 100
    return bool(match.all()), pct


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

VECTOR_CELL_LIMIT = 10_000   # skip vector above this — too slow to be useful


def benchmark(sizes: list[int], steps: int, validate_output: bool) -> None:
    rows_data = []

    for n in sizes:
        cells = n * n
        print(f"\n── {n}×{n} ({cells:,} cells, {steps} steps) ──")

        print(f"  raster ...", end=" ", flush=True)
        r = run_raster(n, n, steps)
        print(f"{r.total_s:.3f}s  ({r.per_step_ms:.1f} ms/step)")

        if cells <= VECTOR_CELL_LIMIT:
            print(f"  vector ...", end=" ", flush=True)
            v = run_vector(n, n, steps)
            print(f"{v.total_s:.3f}s  ({v.per_step_ms:.1f} ms/step)")

            speedup = v.total_s / r.total_s if r.total_s > 0 else float("inf")
            print(f"  speedup:  {speedup:.0f}×")

            if validate_output:
                ok, pct = validate(v, r)
                status  = "✅ identical" if ok else f"⚠️  {pct:.2f}% match"
                print(f"  validation: {status}")
            else:
                ok = None

            rows_data.append({
                "grid":      f"{n}×{n}",
                "cells":     cells,
                "raster_ms": round(r.per_step_ms, 2),
                "vector_ms": round(v.per_step_ms, 2),
                "speedup":   f"{speedup:.0f}×",
                "identical": ok if validate_output else "—",
            })

        else:
            print(f"  vector: skipped (>{VECTOR_CELL_LIMIT:,} cells)")
            rows_data.append({
                "grid":      f"{n}×{n}",
                "cells":     cells,
                "raster_ms": round(r.per_step_ms, 2),
                "vector_ms": "—",
                "speedup":   "—",
                "identical": "—",
            })

    print("\n" + "═" * 62)
    print("RESULTS — Game of Life: vector vs raster (ms per step)")
    print("═" * 62)
    df = pd.DataFrame(rows_data)
    print(df.to_string(index=False))
    print()


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Benchmark GameOfLife: CellularAutomaton vs RasterCellularAutomaton"
    )
    p.add_argument(
        "--sizes", nargs="+", type=int,
        default=[10, 50, 100, 200, 500, 1000],
        help="Grid sizes N×N (default: 10 50 100 200 500 1000)",
    )
    p.add_argument(
        "--steps", type=int, default=10,
        help="Steps per benchmark run (default: 10)",
    )
    p.add_argument(
        "--no-validation", dest="validate", action="store_false",
        help="Skip cell-by-cell output validation",
    )
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    benchmark(sizes=args.sizes, steps=args.steps, validate_output=args.validate)
