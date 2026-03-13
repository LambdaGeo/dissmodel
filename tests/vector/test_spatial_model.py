"""
tests/vector/test_spatial_model.py
====================================
Tests for SpatialModel — the base class for vector push/source models.
"""
from __future__ import annotations

import pytest
import numpy as np
import geopandas as gpd
from libpysal.weights import Queen, Rook

from dissmodel.core import Environment
from dissmodel.geo import vector_grid
from dissmodel.geo.vector.spatial_model import SpatialModel


# ── helpers ───────────────────────────────────────────────────────────────────

class CounterModel(SpatialModel):
    """Increments 'count' by 1 every step — push pattern."""
    def execute(self):
        self.gdf["count"] = self.gdf["count"] + 1


class SourcePropagator(SpatialModel):
    """Sources (state=1) spread to Queen neighbors every step."""
    def execute(self):
        sources  = set(self.gdf.index[self.gdf["state"] == 1])
        new_vals = self.gdf["state"].copy()
        for idx in sources:
            for n in self.neighs_id(idx):
                new_vals[n] = 1
        self.gdf["state"] = new_vals


class NullModel(SpatialModel):
    """Does nothing — useful for init and neighborhood tests."""
    def execute(self):
        pass


class TimeReader(SpatialModel):
    """Records env.now() at each step."""
    def __init__(self, *args, times, **kwargs):
        self._times = times
        super().__init__(*args, **kwargs)

    def execute(self):
        self._times.append(self.env.now())


# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def default_env():
    return Environment(start_time=1, end_time=1)


@pytest.fixture
def grid_3x3():
    return vector_grid(dimension=(3, 3), resolution=1, attrs={"state": 0, "count": 0})


@pytest.fixture
def grid_5x5():
    return vector_grid(dimension=(5, 5), resolution=1, attrs={"state": 0})


# ══════════════════════════════════════════════════════════════════════════════
# Initialisation
# ══════════════════════════════════════════════════════════════════════════════

class TestInit:

    def test_gdf_stored(self, grid_3x3):
        m = NullModel(gdf=grid_3x3)
        assert m.gdf is grid_3x3

    def test_neighborhood_not_created_on_init(self, grid_3x3):
        m = NullModel(gdf=grid_3x3)
        assert not m._neighborhood_created
        assert m._neighs_cache == {}


# ══════════════════════════════════════════════════════════════════════════════
# Neighborhood
# ══════════════════════════════════════════════════════════════════════════════

class TestNeighborhood:

    def test_create_neighborhood_sets_flag(self, grid_3x3):
        m = NullModel(gdf=grid_3x3)
        m.create_neighborhood(strategy=Queen, use_index=True)
        assert m._neighborhood_created

    def test_create_neighborhood_populates_cache(self, grid_3x3):
        m = NullModel(gdf=grid_3x3)
        m.create_neighborhood(strategy=Queen, use_index=True)
        assert len(m._neighs_cache) == 9

    def test_neighs_id_without_neighborhood_raises(self, grid_3x3):
        """Accessing neighbors before create_neighborhood must raise."""
        m = NullModel(gdf=grid_3x3)
        with pytest.raises((RuntimeError, KeyError)):
            m.neighs_id("0-0")

    def test_neighs_without_neighborhood_raises(self, grid_3x3):
        m = NullModel(gdf=grid_3x3)
        with pytest.raises((RuntimeError, KeyError)):
            m.neighs("0-0")

    def test_queen_center_has_8_neighbors(self, grid_3x3):
        m = NullModel(gdf=grid_3x3)
        m.create_neighborhood(strategy=Queen, use_index=True)
        assert len(m.neighs_id("1-1")) == 8

    def test_rook_center_has_4_neighbors(self, grid_3x3):
        m = NullModel(gdf=grid_3x3)
        m.create_neighborhood(strategy=Rook, use_index=True)
        assert len(m.neighs_id("1-1")) == 4

    def test_neighs_returns_geodataframe(self, grid_3x3):
        m = NullModel(gdf=grid_3x3)
        m.create_neighborhood(strategy=Queen, use_index=True)
        result = m.neighs("1-1")
        assert isinstance(result, gpd.GeoDataFrame)

    def test_neighs_id_matches_cache(self, grid_3x3):
        m = NullModel(gdf=grid_3x3)
        m.create_neighborhood(strategy=Queen, use_index=True)
        idx = grid_3x3.index[0]
        assert m.neighs_id(idx) == m._neighs_cache[idx]


# ══════════════════════════════════════════════════════════════════════════════
# neighbor_values
# ══════════════════════════════════════════════════════════════════════════════

class TestNeighborValues:

    def test_returns_numpy_array(self, grid_3x3):
        m = NullModel(gdf=grid_3x3)
        m.create_neighborhood(strategy=Queen, use_index=True)
        vals = m.neighbor_values("1-1", "state")
        assert isinstance(vals, np.ndarray)

    def test_uniform_values(self, grid_3x3):
        grid_3x3["state"] = 5
        m = NullModel(gdf=grid_3x3)
        m.create_neighborhood(strategy=Queen, use_index=True)
        vals = m.neighbor_values("1-1", "state")
        assert np.all(vals == 5)

    def test_correct_count_queen(self, grid_3x3):
        m = NullModel(gdf=grid_3x3)
        m.create_neighborhood(strategy=Queen, use_index=True)
        assert len(m.neighbor_values("1-1", "state")) == 8

    def test_correct_count_rook(self, grid_3x3):
        m = NullModel(gdf=grid_3x3)
        m.create_neighborhood(strategy=Rook, use_index=True)
        assert len(m.neighbor_values("1-1", "state")) == 4


# ══════════════════════════════════════════════════════════════════════════════
# execute() — push pattern
# NOTE: env must be created BEFORE the model so the model registers to it.
# ══════════════════════════════════════════════════════════════════════════════

class TestExecute:

    def test_counter_increments_once(self, grid_3x3):
        env = Environment(start_time=1, end_time=1)
        CounterModel(gdf=grid_3x3)
        env.run()
        assert (grid_3x3["count"] == 1).all()

    def test_counter_increments_n_steps(self, grid_3x3):
        N = 7
        env = Environment(start_time=1, end_time=N)
        CounterModel(gdf=grid_3x3)
        env.run()
        assert (grid_3x3["count"] == N).all()

    def test_source_propagation_one_step(self, grid_5x5):
        """Source at center (2-2) spreads to all 8 Queen neighbors in 1 step."""
        grid_5x5.loc["2-2", "state"] = 1
        env = Environment(start_time=1, end_time=1)
        m = SourcePropagator(gdf=grid_5x5)
        m.create_neighborhood(strategy=Queen, use_index=True)
        env.run()

        activated = set(grid_5x5.index[grid_5x5["state"] == 1])
        expected  = set(m.neighs_id("2-2")) | {"2-2"}
        assert activated == expected

    def test_source_propagation_two_steps(self, grid_5x5):
        """After 2 steps, all cells in 5×5 grid are reached from center."""
        grid_5x5.loc["2-2", "state"] = 1
        env = Environment(start_time=1, end_time=2)
        m = SourcePropagator(gdf=grid_5x5)
        m.create_neighborhood(strategy=Queen, use_index=True)
        env.run()
        assert (grid_5x5["state"] == 1).all()

    def test_execute_uses_past_values(self, grid_3x3):
        """
        SourcePropagator snapshots state before iterating.
        Cells activated mid-step must NOT become sources in the same step.
        Corner 0-0 + its 3 Queen neighbors = 4 active cells after 1 step.
        """
        grid_3x3.loc["0-0", "state"] = 1
        env = Environment(start_time=1, end_time=1)
        m = SourcePropagator(gdf=grid_3x3)
        m.create_neighborhood(strategy=Queen, use_index=True)
        env.run()

        active = int((grid_3x3["state"] == 1).sum())
        assert active == 4   # 0-0 + 3 neighbors


# ══════════════════════════════════════════════════════════════════════════════
# SpatialModel in salabim environment
# ══════════════════════════════════════════════════════════════════════════════

class TestEnvironmentIntegration:

    def test_multiple_models_same_env(self, grid_3x3):
        """Two models registered in the same environment both execute."""
        grid_3x3["count_a"] = 0
        grid_3x3["count_b"] = 0

        class ModelA(SpatialModel):
            def execute(self): self.gdf["count_a"] += 1

        class ModelB(SpatialModel):
            def execute(self): self.gdf["count_b"] += 2

        env = Environment(start_time=1, end_time=3)
        ModelA(gdf=grid_3x3)
        ModelB(gdf=grid_3x3)
        env.run()

        assert (grid_3x3["count_a"] == 3).all()
        assert (grid_3x3["count_b"] == 6).all()

    def test_env_now_accessible(self, grid_3x3):
        """SpatialModel can read env.now() during execute."""
        times = []

        class TimeReader(SpatialModel):
            def execute(self):
                times.append(self.env.now())

        env = Environment(start_time=1, end_time=3)
        TimeReader(gdf=grid_3x3)
        env.run()

        assert times == [1, 2, 3]
