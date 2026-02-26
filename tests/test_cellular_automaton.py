import pytest
from dissmodel.geo import regular_grid
from dissmodel.geo.celullar_automaton import CellularAutomaton
from dissmodel.core import Environment
from libpysal.weights import Queen


@pytest.fixture
def env():
    return Environment()


class ConcreteCA(CellularAutomaton):
    """Minimal concrete subclass for testing."""
    def rule(self, idx):
        return self.gdf.loc[idx, self.state_attr]


# ---------------------------------------------------------------------------
# Existing tests
# ---------------------------------------------------------------------------

def test_neighborhood_caching(env):
    """Test if caching neighbors actually works and returns correct results."""
    gdf = regular_grid(dimension=(3, 3), resolution=1)
    ca = ConcreteCA(gdf)
    ca.create_neighborhood(strategy=Queen, use_index=True)

    assert ca._neighs_cache is not None
    assert len(ca._neighs_cache) == 9

    first_idx = gdf.index[0]
    neighs = ca.neighs_id(first_idx)
    assert isinstance(neighs, list)
    assert neighs == ca._neighs_cache[first_idx]


def test_neighbor_values(env):
    """Test the neighbor_values method."""
    gdf = regular_grid(dimension=(3, 3), resolution=1, attrs={'val': 1})
    ca = ConcreteCA(gdf, state_attr='val')
    ca.create_neighborhood(strategy=Queen, use_index=True)

    idx = "1-1"
    vals = ca.neighbor_values(idx, 'val')

    assert len(vals) == 8
    assert all(v == 1 for v in vals)


# ---------------------------------------------------------------------------
# ABC contract enforcement
# ---------------------------------------------------------------------------

def test_cannot_instantiate_without_rule(env):
    """CellularAutomaton cannot be instantiated without implementing rule."""
    with pytest.raises(TypeError, match="rule"):
        CellularAutomaton(gdf=regular_grid(dimension=(3, 3), resolution=1))


def test_can_instantiate_with_rule(env):
    """A subclass that implements rule can be instantiated."""
    ca = ConcreteCA(gdf=regular_grid(dimension=(3, 3), resolution=1))
    assert ca is not None


def test_execute_without_neighborhood_raises(env):
    """execute() raises RuntimeError if neighborhood was not created."""
    ca = ConcreteCA(gdf=regular_grid(dimension=(3, 3), resolution=1))
    with pytest.raises(RuntimeError, match="create_neighborhood"):
        ca.execute()


def test_neighs_without_neighborhood_raises(env):
    """neighs() raises RuntimeError if neighborhood was not created."""
    ca = ConcreteCA(gdf=regular_grid(dimension=(3, 3), resolution=1))
    with pytest.raises(RuntimeError, match="create_neighborhood"):
        ca.neighs("0-0")