"""
tests/vector/test_regular_grid.py
====================================
Tests for regular_grid() and parse_idx() — vector grid utilities.
"""
from __future__ import annotations

import pytest
import numpy as np
import geopandas as gpd
from shapely.geometry import Polygon

from dissmodel.core import Environment
from dissmodel.geo.vector.regular_grid import regular_grid, parse_idx


@pytest.fixture(autouse=True)
def default_env():
    return Environment(start_time=1, end_time=1)


# ══════════════════════════════════════════════════════════════════════════════
# regular_grid — return type and structure
# ══════════════════════════════════════════════════════════════════════════════

class TestReturnType:

    def test_returns_geodataframe(self):
        gdf = regular_grid(dimension=(3, 3), resolution=1)
        assert isinstance(gdf, gpd.GeoDataFrame)

    def test_geometry_column_exists(self):
        gdf = regular_grid(dimension=(3, 3), resolution=1)
        assert "geometry" in gdf.columns

    def test_geometries_are_polygons(self):
        gdf = regular_grid(dimension=(3, 3), resolution=1)
        assert all(isinstance(g, Polygon) for g in gdf.geometry)


# ══════════════════════════════════════════════════════════════════════════════
# regular_grid — cell count
# ══════════════════════════════════════════════════════════════════════════════

class TestCellCount:

    @pytest.mark.parametrize("cols,rows,expected", [
        (3, 3, 9),
        (5, 5, 25),
        (10, 5, 50),
        (1, 1, 1),
        (1, 10, 10),
    ])
    def test_cell_count(self, cols, rows, expected):
        gdf = regular_grid(dimension=(cols, rows), resolution=1)
        assert len(gdf) == expected


# ══════════════════════════════════════════════════════════════════════════════
# regular_grid — index format
# ══════════════════════════════════════════════════════════════════════════════

class TestIndex:

    def test_index_format_is_two_numbers(self):
        """Index must follow 'a-b' format with two numeric parts."""
        gdf = regular_grid(dimension=(3, 3), resolution=1)
        for idx in gdf.index:
            parts = idx.split("-")
            assert len(parts) == 2
            assert parts[0].isdigit()
            assert parts[1].isdigit()

    def test_index_is_unique(self):
        gdf = regular_grid(dimension=(4, 4), resolution=1)
        assert gdf.index.is_unique

    def test_corner_indices_present(self):
        gdf = regular_grid(dimension=(3, 3), resolution=1)
        assert "0-0" in gdf.index
        assert "0-2" in gdf.index
        assert "2-0" in gdf.index
        assert "2-2" in gdf.index


# ══════════════════════════════════════════════════════════════════════════════
# regular_grid — resolution
# ══════════════════════════════════════════════════════════════════════════════

class TestResolution:

    def test_cell_width_matches_resolution(self):
        res = 100
        gdf = regular_grid(dimension=(3, 3), resolution=res)
        b   = gdf.geometry.iloc[0].bounds   # (minx, miny, maxx, maxy)
        assert abs((b[2] - b[0]) - res) < 1e-6

    def test_cell_height_matches_resolution(self):
        res = 50
        gdf = regular_grid(dimension=(3, 3), resolution=res)
        b   = gdf.geometry.iloc[0].bounds
        assert abs((b[3] - b[1]) - res) < 1e-6

    def test_total_width(self):
        cols, res = 4, 10
        gdf   = regular_grid(dimension=(cols, 3), resolution=res)
        total = gdf.total_bounds[2] - gdf.total_bounds[0]
        assert abs(total - cols * res) < 1e-6

    def test_total_height(self):
        rows, res = 5, 10
        gdf   = regular_grid(dimension=(3, rows), resolution=res)
        total = gdf.total_bounds[3] - gdf.total_bounds[1]
        assert abs(total - rows * res) < 1e-6


# ══════════════════════════════════════════════════════════════════════════════
# regular_grid — attrs
# ══════════════════════════════════════════════════════════════════════════════

class TestAttrs:

    def test_single_attr_creates_column(self):
        gdf = regular_grid(dimension=(3, 3), resolution=1, attrs={"state": 0})
        assert "state" in gdf.columns

    def test_attr_default_value(self):
        gdf = regular_grid(dimension=(3, 3), resolution=1, attrs={"state": 7})
        assert (gdf["state"] == 7).all()

    def test_multiple_attrs(self):
        gdf = regular_grid(dimension=(3, 3), resolution=1,
                           attrs={"uso": 2, "alt": 0.0, "solo": 1})
        for col in ("uso", "alt", "solo"):
            assert col in gdf.columns

    def test_attrs_independent(self):
        """Writing one column must not affect another."""
        gdf = regular_grid(dimension=(3, 3), resolution=1,
                           attrs={"a": 0, "b": 0})
        gdf.loc["0-0", "a"] = 99
        assert gdf.loc["0-0", "a"] == 99
        assert gdf.loc["0-0", "b"] == 0


# ══════════════════════════════════════════════════════════════════════════════
# parse_idx
# NOTE: parse_idx returns (col, row) — confirmed from implementation.
# ══════════════════════════════════════════════════════════════════════════════

class TestParseIdx:

    @pytest.mark.parametrize("idx,expected", [
        ("0-0", (0, 0)),
        ("1-2", (2, 1)),    # returns (col, row): col=2, row=1
        ("10-5", (5, 10)),  # col=5, row=10
        ("0-99", (99, 0)),  # col=99, row=0
    ])
    def test_parses_correctly(self, idx, expected):
        assert parse_idx(idx) == expected

    def test_returns_tuple_of_ints(self):
        result = parse_idx("3-7")
        assert all(isinstance(v, int) for v in result)

    def test_consistent_with_grid_index(self):
        """parse_idx must round-trip: reconstructing the index gives the original."""
        gdf = regular_grid(dimension=(4, 3), resolution=1)
        for idx in gdf.index:
            col, row = parse_idx(idx)
            assert f"{row}-{col}" == idx
