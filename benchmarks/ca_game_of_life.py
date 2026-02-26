"""
Game of Life — Benchmark
========================
Compares two implementations of the Game of Life rule:

- Original  — uses ``neighs(idx)`` returning a GeoDataFrame
- Optimized — uses ``neighbor_values(idx, col)`` returning a numpy array

Usage
-----
    python benchmarks/ca_game_of_life.py
"""
from __future__ import annotations

import time
import warnings

from libpysal.weights import Queen

from dissmodel.core import Environment
from dissmodel.geo import FillStrategy, fill, regular_grid
from dissmodel.geo.celullar_automaton import CellularAutomaton


# ---------------------------------------------------------------------------
# Model definitions
# ---------------------------------------------------------------------------

class GameOfLifeOriginal(CellularAutomaton):
    """Uses neighs(idx) — returns a GeoDataFrame slice."""

    def setup(self) -> None:
        self.create_neighborhood(strategy=Queen, use_index=True)

    def initialize(self) -> None:
        fill(
            strategy=FillStrategy.RANDOM_SAMPLE,
            gdf=self.gdf,
            attr="state",
            data={1: 0.6, 0: 0.4},
            seed=42,
        )

    def rule(self, idx):
        value = self.gdf.loc[idx, self.state_attr]
        count = self.neighs(idx)[self.state_attr].fillna(0).sum()
        if value == 1:
            return 1 if 2 <= count <= 3 else 0
        return 1 if count == 3 else 0


class GameOfLifeOptimized(CellularAutomaton):
    """Uses neighbor_values(idx, col) — returns a numpy array."""

    def setup(self) -> None:
        self.create_neighborhood(strategy=Queen, use_index=True)

    def initialize(self) -> None:
        fill(
            strategy=FillStrategy.RANDOM_SAMPLE,
            gdf=self.gdf,
            attr="state",
            data={1: 0.6, 0: 0.4},
            seed=42,
        )

    def rule(self, idx):
        value = self.gdf.at[idx, self.state_attr]
        count = self.neighbor_values(idx, self.state_attr).sum()
        if value == 1:
            return 1 if 2 <= count <= 3 else 0
        return 1 if count == 3 else 0


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_benchmark(
    model_cls: type,
    dim: tuple[int, int] = (50, 50),
    steps: int = 10,
    name: str = "Benchmark",
) -> float:
    print(f"[{name}] Setting up {dim[0]}x{dim[1]} grid...")
    env = Environment(start_time=0, end_time=steps)
    gdf = regular_grid(dimension=dim, resolution=1, attrs={"state": 0})
    model = model_cls(gdf=gdf)
    model.initialize()

    print(f"[{name}] Running {steps} steps...")
    start = time.time()
    env.run()
    elapsed = time.time() - start

    print(f"[{name}] Done in {elapsed:.4f}s")
    return elapsed


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    warnings.filterwarnings("ignore")

    print("Warming up...")
    run_benchmark(GameOfLifeOriginal, dim=(20, 20), steps=1, name="Warmup")

    print("\n--- Benchmark: 50x50, 5 steps ---")
    t_orig = run_benchmark(GameOfLifeOriginal, dim=(50, 50), steps=5, name="Original")
    t_opt  = run_benchmark(GameOfLifeOptimized, dim=(50, 50), steps=5, name="Optimized")

    print(f"\nResults:")
    print(f"  Original:  {t_orig:.4f}s")
    print(f"  Optimized: {t_opt:.4f}s")
    print(f"  Speedup:   {t_orig / t_opt:.2f}x")
