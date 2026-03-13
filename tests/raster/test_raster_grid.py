"""
tests/raster/test_raster_grid.py
==================================
Tests for raster_grid() — raster grid factory.
"""
from __future__ import annotations

import pytest
import numpy as np

from dissmodel.geo.raster.backend import RasterBackend
from dissmodel.geo import raster_grid


# ══════════════════════════════════════════════════════════════════════════════
# Return type
# ══════════════════════════════════════════════════════════════════════════════

class TestReturnType:

    def test_returns_raster_backend(self):
        b = raster_grid(rows=3, cols=3)
        assert isinstance(b, RasterBackend)

    def test_shape_matches(self):
        b = raster_grid(rows=4, cols=6)
        assert b.shape == (4, 6)


# ══════════════════════════════════════════════════════════════════════════════
# attrs
# ══════════════════════════════════════════════════════════════════════════════

class TestAttrs:

    def test_scalar_attr_creates_band(self):
        b = raster_grid(rows=3, cols=3, attrs={"state": 0})
        assert "state" in b.arrays

    def test_scalar_attr_fills_array(self):
        b = raster_grid(rows=3, cols=3, attrs={"state": 5})
        assert (b.get("state") == 5).all()

    def test_array_attr_stored(self):
        arr = np.arange(9, dtype=np.int32).reshape(3, 3)
        b = raster_grid(rows=3, cols=3, attrs={"state": arr})
        np.testing.assert_array_equal(b.get("state"), arr)

    def test_multiple_attrs(self):
        b = raster_grid(rows=3, cols=3,
                             attrs={"uso": 2, "alt": 0.0, "solo": 1})
        for band in ("uso", "alt", "solo"):
            assert band in b.arrays

    def test_no_attrs_gives_empty_backend(self):
        b = raster_grid(rows=3, cols=3)
        assert len(b.arrays) == 0

    def test_array_shape_matches_grid(self):
        rows, cols = 4, 7
        b = raster_grid(rows=rows, cols=cols, attrs={"state": 0})
        assert b.get("state").shape == (rows, cols)

    def test_attrs_independent(self):
        """Modifying one band must not affect another."""
        b = raster_grid(rows=3, cols=3, attrs={"a": 0, "b": 0})
        b.arrays["a"][0, 0] = 99
        assert b.get("b")[0, 0] == 0


# ══════════════════════════════════════════════════════════════════════════════
# Edge cases
# ══════════════════════════════════════════════════════════════════════════════

class TestEdgeCases:

    def test_1x1_grid(self):
        b = raster_grid(rows=1, cols=1, attrs={"state": 7})
        assert b.shape == (1, 1)
        assert b.get("state")[0, 0] == 7

    def test_1xN_grid(self):
        b = raster_grid(rows=1, cols=10, attrs={"state": 0})
        assert b.shape == (1, 10)
        assert b.get("state").shape == (1, 10)

    def test_Nx1_grid(self):
        b = raster_grid(rows=10, cols=1, attrs={"state": 0})
        assert b.shape == (10, 1)

    def test_large_grid(self):
        b = raster_grid(rows=1000, cols=1000, attrs={"state": 0})
        assert b.shape == (1000, 1000)
        assert b.get("state").shape == (1000, 1000)
