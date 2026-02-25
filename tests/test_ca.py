
import pytest
from dissmodel.geo import regular_grid
from dissmodel.geo.celular_automaton import CellularAutomaton
from dissmodel.core import Environment
from libpysal.weights import Queen

@pytest.fixture
def env():
    # We need an environment for salabim components
    return Environment()

def test_neighborhood_caching(env):
    """Test if caching neighbors actually works and returns correct results."""
    # regular_grid needs dimension as tuple (cols, rows) AND resolution.
    gdf = regular_grid(dimension=(3, 3), resolution=1)

    # CellularAutomaton attaches to the default env provided by fixture
    ca = CellularAutomaton(gdf)
    ca.create_neighborhood(strategy=Queen, use_index=True)

    # Check if cache is populated
    assert ca._neighs_cache is not None
    assert len(ca._neighs_cache) == 9

    first_idx = gdf.index[0]

    # We rely on neighs_id to return something valid
    neighs = ca.neighs_id(first_idx)
    assert isinstance(neighs, list)

    # Compare with direct access
    assert neighs == ca._neighs_cache[first_idx]

def test_neighbor_values(env):
    """Test the new neighbor_values method."""
    gdf = regular_grid(dimension=(3, 3), resolution=1, attrs={'val': 1})
    ca = CellularAutomaton(gdf, state_attr='val')
    ca.create_neighborhood(strategy=Queen, use_index=True)

    # Center of 3x3 is "1-1"
    idx = "1-1"
    vals = ca.neighbor_values(idx, 'val')

    # Center of 3x3 has 8 neighbors (Queen)
    assert len(vals) == 8
    assert all(v == 1 for v in vals)
