"""
tests/integration/test_game_of_life.py
========================================
Integration test: GameOfLifeVector vs GameOfLifeRaster.

Runs both substrates with the same initial state and asserts that the
final state is cell-by-cell identical. This is the strongest correctness
guarantee for the dual backend — if this passes, the raster substrate
faithfully implements the same rules as the vector substrate.

Why GameOfLife works well here
-------------------------------
- Deterministic and integer-only — no floating point tolerance needed
- No domain dependencies — runs with dissmodel only
- Short rules — easy to reason about correctness by inspection
- Queen neighborhood on vector == Moore neighborhood on raster (8 dirs)
"""
from __future__ import annotations

import numpy as np
import pytest
import geopandas as gpd

from dissmodel.core import Environment
from dissmodel.geo import regular_grid
from dissmodel.geo.vector.cellular_automaton import CellularAutomaton
from dissmodel.geo.raster.backend import RasterBackend
from dissmodel.geo.raster.cellular_automaton import RasterCellularAutomaton
from dissmodel.geo import make_raster_grid


# ══════════════════════════════════════════════════════════════════════════════
# MODELS
# ══════════════════════════════════════════════════════════════════════════════

class GameOfLifeVector(CellularAutomaton):
    """Conway's Game of Life — vector substrate."""

    def rule(self, idx):
        state     = self.gdf.loc[idx, self.state_attr]
        neighbors = (self.neighbor_values(idx, self.state_attr) == 1).sum()
        if state == 1:
            return 1 if neighbors in (2, 3) else 0
        return 1 if neighbors == 3 else 0


class GameOfLifeRaster(RasterCellularAutomaton):
    """Conway's Game of Life — raster substrate."""

    def rule(self, arrays):
        state     = arrays[self.state_attr]
        neighbors = self.backend.focal_sum_mask(state == 1)
        survive   = (state == 1) & np.isin(neighbors, [2, 3])
        born      = (state == 0) & (neighbors == 3)
        return {self.state_attr: np.where(survive | born, 1, 0).astype(np.int8)}


# ══════════════════════════════════════════════════════════════════════════════
# FACTORIES
# ══════════════════════════════════════════════════════════════════════════════

def make_initial(rows: int, cols: int, seed: int = 42) -> np.ndarray:
    """Shared initial state — both substrates must start identically."""
    rng = np.random.default_rng(seed)
    return (rng.random((rows, cols)) < 0.3).astype(np.int8)


def setup_vector(rows: int, cols: int, steps: int, seed: int = 42):
    from libpysal.weights import Queen
    state = make_initial(rows, cols, seed).ravel().astype(int)
    gdf   = regular_grid(dimension=(cols, rows), resolution=1, attrs={"state": 0})
    gdf["state"] = state
    env = Environment(start_time=1, end_time=steps)
    ca  = GameOfLifeVector(gdf=gdf)
    ca.create_neighborhood(strategy=Queen, use_index=True)
    return env, gdf


def setup_raster(rows: int, cols: int, steps: int, seed: int = 42):
    state = make_initial(rows, cols, seed)
    b     = make_raster_grid(rows=rows, cols=cols, attrs={"state": state})
    env   = Environment(start_time=1, end_time=steps)
    GameOfLifeRaster(backend=b)
    return env, b


def final_vector(gdf: gpd.GeoDataFrame, rows: int, cols: int) -> np.ndarray:
    return gdf["state"].values.reshape(rows, cols).astype(np.int8)


def final_raster(b: RasterBackend) -> np.ndarray:
    return b.get("state").astype(np.int8)


# ══════════════════════════════════════════════════════════════════════════════
# TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestGameOfLifeEquivalence:
    """
    Assert that vector and raster substrates produce identical results
    when starting from the same initial state.
    """

    @pytest.mark.parametrize("n,steps", [
        (5,  1),
        (5,  5),
        (10, 1),
        (10, 5),
        (20, 3),
    ])
    def test_identical_output(self, n, steps):
        """Final state must be cell-by-cell identical for both substrates."""
        rows, cols = n, n

        env_v, gdf = setup_vector(rows, cols, steps)
        env_v.run()
        state_v = final_vector(gdf, rows, cols)

        env_r, b = setup_raster(rows, cols, steps)
        env_r.run()
        state_r = final_raster(b)

        mismatches = int((state_v != state_r).sum())
        assert mismatches == 0, (
            f"{n}×{n} grid after {steps} steps: "
            f"{mismatches} cells differ between vector and raster"
        )

    def test_step_by_step_equivalence(self):
        """
        State must match after every individual step, not just the last one.
        Catches bugs where substrates diverge mid-simulation.
        """
        rows, cols, seed = 10, 10, 7
        initial = make_initial(rows, cols, seed)

        for step in range(1, 6):
            from libpysal.weights import Queen

            # vector
            gdf_s = regular_grid(dimension=(cols, rows), resolution=1, attrs={"state": 0})
            gdf_s["state"] = initial.ravel().astype(int)
            env_v = Environment(start_time=1, end_time=step)
            ca = GameOfLifeVector(gdf=gdf_s)
            ca.create_neighborhood(strategy=Queen, use_index=True)
            env_v.run()
            sv = final_vector(gdf_s, rows, cols)

            # raster
            b_s   = make_raster_grid(rows=rows, cols=cols,
                                     attrs={"state": initial.copy()})
            env_r = Environment(start_time=1, end_time=step)
            GameOfLifeRaster(backend=b_s)
            env_r.run()
            sr = final_raster(b_s)

            mismatches = int((sv != sr).sum())
            assert mismatches == 0, (
                f"Diverged at step {step}: {mismatches} cells differ"
            )

    @pytest.mark.parametrize("seed", [0, 1, 42, 99, 123])
    def test_multiple_seeds(self, seed):
        """Results must match across different random initial conditions."""
        rows, cols, steps = 10, 10, 3

        env_v, gdf = setup_vector(rows, cols, steps, seed=seed)
        env_v.run()
        state_v = final_vector(gdf, rows, cols)

        env_r, b = setup_raster(rows, cols, steps, seed=seed)
        env_r.run()
        state_r = final_raster(b)

        assert (state_v == state_r).all(), (
            f"seed={seed}: substrates diverged after {steps} steps"
        )

    def test_all_dead_stays_dead(self):
        """A fully dead grid must remain dead on both substrates."""
        rows, cols, steps = 5, 5, 3

        # vector
        gdf   = regular_grid(dimension=(cols, rows), resolution=1, attrs={"state": 0})
        env_v = Environment(start_time=1, end_time=steps)
        from libpysal.weights import Queen
        ca = GameOfLifeVector(gdf=gdf)
        ca.create_neighborhood(strategy=Queen, use_index=True)
        env_v.run()
        assert (gdf["state"] == 0).all(), "All-dead vector grid became alive"

        # raster
        b     = make_raster_grid(rows=rows, cols=cols, attrs={"state": 0})
        env_r = Environment(start_time=1, end_time=steps)
        GameOfLifeRaster(backend=b)
        env_r.run()
        assert (final_raster(b) == 0).all(), "All-dead raster grid became alive"

    def test_still_life_block(self):
        """
        A 2×2 block in the center of a 6×6 grid is a still life —
        it must remain unchanged for both substrates.
        """
        rows, cols, steps = 6, 6, 5
        initial = np.zeros((rows, cols), dtype=np.int8)
        # place a 2×2 block in the center
        initial[2:4, 2:4] = 1

        # vector
        gdf = regular_grid(dimension=(cols, rows), resolution=1, attrs={"state": 0})
        gdf["state"] = initial.ravel().astype(int)
        env_v = Environment(start_time=1, end_time=steps)
        from libpysal.weights import Queen
        ca = GameOfLifeVector(gdf=gdf)
        ca.create_neighborhood(strategy=Queen, use_index=True)
        env_v.run()
        sv = final_vector(gdf, rows, cols)

        # raster
        b     = make_raster_grid(rows=rows, cols=cols, attrs={"state": initial.copy()})
        env_r = Environment(start_time=1, end_time=steps)
        GameOfLifeRaster(backend=b)
        env_r.run()
        sr = final_raster(b)

        np.testing.assert_array_equal(sv, initial,
            err_msg="Vector: 2×2 block is not a still life")
        np.testing.assert_array_equal(sr, initial,
            err_msg="Raster: 2×2 block is not a still life")
        np.testing.assert_array_equal(sv, sr,
            err_msg="Vector and raster diverged on still life")
