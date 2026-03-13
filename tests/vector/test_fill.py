"""
tests/vector/test_fill.py
====================================
Tests for fill() and FillStrategy — vector grid fill utilities.
"""
import pytest
from dissmodel.core import Environment
from dissmodel.geo import vector_grid, fill, FillStrategy
from dissmodel.geo.vector.vector_grid import parse_idx


@pytest.fixture(autouse=True)
def default_env():
    return Environment(start_time=1, end_time=1)


def test_pattern_square_grid():
    """Pattern applied to correct cells on a square grid."""
    gdf = vector_grid(dimension=(3, 3), resolution=1.0, attrs={"state": 0})
    pattern = [[1, 0], [0, 1]]
    fill(FillStrategy.PATTERN, gdf=gdf, attr="state", pattern=pattern)
    # pattern[1][0] → row=0, col=0 → idx "0-0"
    assert gdf.loc["0-0", "state"] == 0
    # pattern[0][0] → row=1, col=0 → idx "1-0"
    assert gdf.loc["1-0", "state"] == 1


def test_pattern_nonsquare_grid():
    """Pattern applied to correct cells on a non-square grid (3 cols x 5 rows)."""
    gdf = vector_grid(dimension=(3, 5), resolution=1.0, attrs={"state": 0})
    assert len(gdf) == 15

    pattern = [[1, 1, 1]]  # 1 row, 3 cols
    fill(FillStrategy.PATTERN, gdf=gdf, attr="state", pattern=pattern,
         start_x=0, start_y=0)

    # pattern[0][0..2] → row=0, col=0,1,2 → idx "0-0", "0-1", "0-2"
    assert gdf.loc["0-0", "state"] == 1
    assert gdf.loc["0-1", "state"] == 1
    assert gdf.loc["0-2", "state"] == 1
    # Other rows untouched
    assert gdf.loc["1-0", "state"] == 0


def test_pattern_out_of_bounds_ignored():
    """Pattern cells outside the grid are silently ignored."""
    gdf = vector_grid(dimension=(2, 2), resolution=1.0, attrs={"state": 0})
    pattern = [[1, 1, 1], [1, 1, 1]]  # wider than grid
    fill(FillStrategy.PATTERN, gdf=gdf, attr="state", pattern=pattern)
    # No KeyError should be raised
    assert gdf.loc["0-0", "state"] == 1
    assert gdf.loc["0-1", "state"] == 1


def test_parse_idx_roundtrip():
    """parse_idx correctly extracts col, row from row-col index string."""
    pos = parse_idx("3-4")
    assert pos.row == 3
    assert pos.col == 4
