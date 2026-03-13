"""
tests/vector/test_cellular_automaton.py
========================================
Tests for CellularAutomaton and SpatialModel (vector substrate).
"""
from __future__ import annotations

import pytest
import numpy as np
from libpysal.weights import Queen, Rook

from dissmodel.core import Environment
from dissmodel.geo import vector_grid
from dissmodel.geo.vector.cellular_automaton import CellularAutomaton


# ── helpers ───────────────────────────────────────────────────────────────────

class IdentityCA(CellularAutomaton):
    """Returns current state unchanged — useful for structure tests."""
    def rule(self, idx):
        return self.gdf.loc[idx, self.state_attr]


class SumNeighborsCA(CellularAutomaton):
    """New state = sum of neighbor values — useful for transition tests."""
    def rule(self, idx):
        return int(self.neighbor_values(idx, self.state_attr).sum())


class IncrementCA(CellularAutomaton):
    """New state = current state + 1 — useful for step counting tests."""
    def rule(self, idx):
        return self.gdf.loc[idx, self.state_attr] + 1


# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def default_env():
    """
    Create a default Environment for every test.

    Required by salabim — any Model instantiation fails without an active
    Environment. Tests that need a different end_time create their own
    Environment locally, which replaces this default.
    """
    return Environment(start_time=1, end_time=1)


@pytest.fixture
def grid_3x3():
    return vector_grid(dimension=(3, 3), resolution=1, attrs={"state": 0})


# ══════════════════════════════════════════════════════════════════════════════
# ABC contract
# ══════════════════════════════════════════════════════════════════════════════

class TestABCContract:

    def test_cannot_instantiate_without_rule(self, grid_3x3):
        """CellularAutomaton is abstract — must implement rule()."""
        with pytest.raises(TypeError, match="rule"):
            CellularAutomaton(gdf=grid_3x3)

    def test_can_instantiate_with_rule(self, grid_3x3):
        ca = IdentityCA(gdf=grid_3x3)
        assert ca is not None

    def test_execute_without_neighborhood_raises(self, grid_3x3):
        ca = IdentityCA(gdf=grid_3x3)
        with pytest.raises(RuntimeError, match="create_neighborhood"):
            ca.execute()

    def test_neighs_without_neighborhood_raises(self, grid_3x3):
        ca = IdentityCA(gdf=grid_3x3)
        with pytest.raises(RuntimeError, match="create_neighborhood"):
            ca.neighs("0-0")


# ══════════════════════════════════════════════════════════════════════════════
# Neighborhood creation
# ══════════════════════════════════════════════════════════════════════════════

class TestNeighborhood:

    def test_queen_cache_size(self, grid_3x3):
        """Cache must have one entry per cell."""
        ca = IdentityCA(gdf=grid_3x3)
        ca.create_neighborhood(strategy=Queen, use_index=True)
        assert len(ca._neighs_cache) == 9

    def test_neighborhood_created_flag(self, grid_3x3):
        ca = IdentityCA(gdf=grid_3x3)
        assert not ca._neighborhood_created
        ca.create_neighborhood(strategy=Queen, use_index=True)
        assert ca._neighborhood_created

    def test_center_cell_has_8_queen_neighbors(self, grid_3x3):
        """Center cell of 3x3 grid has 8 neighbors under Queen."""
        ca = IdentityCA(gdf=grid_3x3)
        ca.create_neighborhood(strategy=Queen, use_index=True)
        assert len(ca.neighs_id("1-1")) == 8

    def test_corner_cell_has_3_queen_neighbors(self, grid_3x3):
        """Corner cell of 3x3 grid has 3 neighbors under Queen."""
        ca = IdentityCA(gdf=grid_3x3)
        ca.create_neighborhood(strategy=Queen, use_index=True)
        corner = grid_3x3.index[0]
        assert len(ca.neighs_id(corner)) == 3

    def test_center_cell_has_4_rook_neighbors(self, grid_3x3):
        """Center cell of 3x3 grid has 4 neighbors under Rook."""
        ca = IdentityCA(gdf=grid_3x3)
        ca.create_neighborhood(strategy=Rook, use_index=True)
        assert len(ca.neighs_id("1-1")) == 4

    def test_neighs_id_matches_cache(self, grid_3x3):
        ca = IdentityCA(gdf=grid_3x3)
        ca.create_neighborhood(strategy=Queen, use_index=True)
        idx = grid_3x3.index[0]
        assert ca.neighs_id(idx) == ca._neighs_cache[idx]

    def test_neighs_returns_geodataframe(self, grid_3x3):
        import geopandas as gpd
        ca = IdentityCA(gdf=grid_3x3)
        ca.create_neighborhood(strategy=Queen, use_index=True)
        result = ca.neighs("1-1")
        assert isinstance(result, gpd.GeoDataFrame)
        assert len(result) == 8


# ══════════════════════════════════════════════════════════════════════════════
# neighbor_values
# ══════════════════════════════════════════════════════════════════════════════

class TestNeighborValues:

    def test_uniform_values(self, grid_3x3):
        """All neighbors of center cell have the same value."""
        grid_3x3["state"] = 1
        ca = IdentityCA(gdf=grid_3x3, state_attr="state")
        ca.create_neighborhood(strategy=Queen, use_index=True)
        vals = ca.neighbor_values("1-1", "state")
        assert len(vals) == 8
        assert np.all(vals == 1)

    def test_returns_numpy_array(self, grid_3x3):
        ca = IdentityCA(gdf=grid_3x3)
        ca.create_neighborhood(strategy=Queen, use_index=True)
        vals = ca.neighbor_values("1-1", "state")
        assert isinstance(vals, np.ndarray)

    def test_mixed_values(self, grid_3x3):
        """neighbor_values returns correct subset for non-uniform grid."""
        grid_3x3.loc["0-0", "state"] = 5
        ca = IdentityCA(gdf=grid_3x3)
        ca.create_neighborhood(strategy=Queen, use_index=True)
        vals = ca.neighbor_values("1-1", "state")
        assert 5 in vals


# ══════════════════════════════════════════════════════════════════════════════
# execute() — state transitions
# ══════════════════════════════════════════════════════════════════════════════

class TestExecute:
    # NOTE: env must be created BEFORE the model — the model registers to
    # the active Environment at instantiation time.

    def test_identity_rule_preserves_state(self, grid_3x3):
        """IdentityCA must not change any cell value."""
        grid_3x3["state"] = 7
        env = Environment(start_time=1, end_time=1)
        ca = IdentityCA(gdf=grid_3x3)
        ca.create_neighborhood(strategy=Queen, use_index=True)
        env.run()
        assert (grid_3x3["state"] == 7).all()

    def test_increment_rule_updates_all_cells(self, grid_3x3):
        """IncrementCA must add 1 to every cell per step."""
        env = Environment(start_time=1, end_time=1)
        ca = IncrementCA(gdf=grid_3x3)
        ca.create_neighborhood(strategy=Queen, use_index=True)
        env.run()
        assert (grid_3x3["state"] == 1).all()

    def test_increment_rule_multiple_steps(self, grid_3x3):
        """IncrementCA after N steps — all cells equal N."""
        env = Environment(start_time=1, end_time=5)
        ca = IncrementCA(gdf=grid_3x3)
        ca.create_neighborhood(strategy=Queen, use_index=True)
        env.run()
        assert (grid_3x3["state"] == 5).all()

    def test_sum_neighbors_center_cell(self, grid_3x3):
        """Center cell surrounded by cells of value 1 gets sum = 8 (Queen)."""
        grid_3x3["state"] = 1
        grid_3x3.loc["1-1", "state"] = 0
        env = Environment(start_time=1, end_time=1)
        ca = SumNeighborsCA(gdf=grid_3x3)
        ca.create_neighborhood(strategy=Queen, use_index=True)
        env.run()
        assert grid_3x3.loc["1-1", "state"] == 8

    def test_execute_uses_state_attr(self):
        """execute() writes result to state_attr column."""
        gdf = vector_grid(dimension=(3, 3), resolution=1, attrs={"mystate": 3})
        env = Environment(start_time=1, end_time=1)
        ca  = IncrementCA(gdf=gdf, state_attr="mystate")
        ca.create_neighborhood(strategy=Queen, use_index=True)
        env.run()
        assert (gdf["mystate"] == 4).all()


# ══════════════════════════════════════════════════════════════════════════════
# SpatialModel (inherited via CellularAutomaton)
# ══════════════════════════════════════════════════════════════════════════════

class TestSpatialModelBase:

    def test_gdf_stored_on_init(self, grid_3x3):
        ca = IdentityCA(gdf=grid_3x3)
        assert ca.gdf is grid_3x3

    def test_default_state_attr(self, grid_3x3):
        ca = IdentityCA(gdf=grid_3x3)
        assert ca.state_attr == "state"

    def test_custom_state_attr(self, grid_3x3):
        ca = IdentityCA(gdf=grid_3x3, state_attr="landuse")
        assert ca.state_attr == "landuse"

    def test_neighborhood_not_created_on_init(self, grid_3x3):
        ca = IdentityCA(gdf=grid_3x3)
        assert not ca._neighborhood_created
        assert ca._neighs_cache == {}
