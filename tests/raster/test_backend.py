"""
tests/raster/test_backend.py
==============================
Tests for RasterBackend — the NumPy array store for raster models.
"""
from __future__ import annotations

import pytest
import numpy as np

from dissmodel.geo.raster.backend import RasterBackend, DIRS_MOORE, DIRS_VON_NEUMANN


@pytest.fixture
def backend_3x3():
    b = RasterBackend(shape=(3, 3))
    b.set("state", np.zeros((3, 3), dtype=np.int8))
    return b


@pytest.fixture
def backend_5x5():
    b = RasterBackend(shape=(5, 5))
    b.set("state", np.zeros((5, 5), dtype=np.int8))
    b.set("alt",   np.zeros((5, 5), dtype=np.float32))
    return b


# ══════════════════════════════════════════════════════════════════════════════
# Initialisation
# ══════════════════════════════════════════════════════════════════════════════

class TestInit:

    def test_shape_stored(self):
        b = RasterBackend(shape=(4, 6))
        assert b.shape == (4, 6)

    def test_arrays_empty_on_init(self):
        b = RasterBackend(shape=(3, 3))
        assert len(b.arrays) == 0


# ══════════════════════════════════════════════════════════════════════════════
# set / get
# ══════════════════════════════════════════════════════════════════════════════

class TestSetGet:

    def test_set_and_get_roundtrip(self, backend_3x3):
        arr = np.arange(9, dtype=np.int32).reshape(3, 3)
        backend_3x3.set("data", arr)
        np.testing.assert_array_equal(backend_3x3.get("data"), arr)

    def test_get_missing_key_raises(self, backend_3x3):
        with pytest.raises(KeyError):
            backend_3x3.get("nonexistent")

    def test_set_overwrites(self, backend_3x3):
        backend_3x3.set("state", np.ones((3, 3), dtype=np.int8))
        backend_3x3.set("state", np.full((3, 3), 7, dtype=np.int8))
        assert (backend_3x3.get("state") == 7).all()

    def test_multiple_bands(self, backend_5x5):
        assert "state" in backend_5x5.arrays
        assert "alt"   in backend_5x5.arrays

    def test_get_returns_array_not_copy(self, backend_3x3):
        """get() should return the live array (mutations visible)."""
        arr = backend_3x3.get("state")
        arr[0, 0] = 99
        assert backend_3x3.get("state")[0, 0] == 99


# ══════════════════════════════════════════════════════════════════════════════
# snapshot
# ══════════════════════════════════════════════════════════════════════════════

class TestSnapshot:

    def test_snapshot_returns_copy(self, backend_3x3):
        snap = backend_3x3.get("state").copy()
        backend_3x3.arrays["state"][0, 0] = 99
        assert snap[0, 0] == 0   # copy is unaffected

    def test_copy_isolates_from_original(self, backend_5x5):
        uso_copy = backend_5x5.get("state").copy()
        backend_5x5.arrays["state"][:] = 7
        assert (uso_copy == 0).all()


# ══════════════════════════════════════════════════════════════════════════════
# shift2d
# ══════════════════════════════════════════════════════════════════════════════

class TestShift2d:

    def test_shift_down(self):
        arr = np.array([[1, 2], [3, 4]], dtype=np.int32)
        result = RasterBackend.shift2d(arr, 1, 0)
        # row shifted down: top row becomes 0
        assert result[0, 0] == 0
        assert result[1, 0] == 1

    def test_shift_right(self):
        arr = np.array([[1, 2], [3, 4]], dtype=np.int32)
        result = RasterBackend.shift2d(arr, 0, 1)
        assert result[0, 0] == 0
        assert result[0, 1] == 1

    def test_shift_up(self):
        arr = np.array([[1, 2], [3, 4]], dtype=np.int32)
        result = RasterBackend.shift2d(arr, -1, 0)
        assert result[0, 0] == 3
        assert result[1, 0] == 0

    def test_shift_zero(self):
        arr = np.arange(9, dtype=np.int32).reshape(3, 3)
        np.testing.assert_array_equal(RasterBackend.shift2d(arr, 0, 0), arr)

    def test_shift_preserves_shape(self):
        arr = np.ones((5, 7), dtype=np.float32)
        result = RasterBackend.shift2d(arr, 1, -1)
        assert result.shape == (5, 7)

    def test_shift_fills_edge_with_zero(self):
        arr = np.ones((3, 3), dtype=np.int32)
        result = RasterBackend.shift2d(arr, 1, 0)
        assert (result[0, :] == 0).all()


# ══════════════════════════════════════════════════════════════════════════════
# focal_sum_mask
# ══════════════════════════════════════════════════════════════════════════════

class TestFocalSumMask:

    def test_all_true_center_moore(self):
        """Center cell of all-True 3×3 grid has 8 Moore neighbors."""
        mask = np.ones((3, 3), dtype=bool)
        result = RasterBackend(shape=(3,3)).focal_sum_mask(mask)
        assert result[1, 1] == 8

    def test_all_false_gives_zero(self):
        mask = np.zeros((3, 3), dtype=bool)
        b = RasterBackend(shape=(3, 3))
        assert (b.focal_sum_mask(mask) == 0).all()

    def test_single_source(self):
        """Single True cell at center — only its neighbors get count=1."""
        mask = np.zeros((5, 5), dtype=bool)
        mask[2, 2] = True
        b = RasterBackend(shape=(5, 5))
        result = b.focal_sum_mask(mask)
        # all 8 Moore neighbors of (2,2) should have count 1
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                assert result[2+dr, 2+dc] == 1
        # center itself: no self-count
        assert result[2, 2] == 0


# ══════════════════════════════════════════════════════════════════════════════
# neighbor_contact
# ══════════════════════════════════════════════════════════════════════════════

class TestNeighborContact:

    def test_isolated_cell_neighbors_have_contact(self):
        """
        neighbor_contact returns True wherever a cell has at least one
        True neighbor. Cells adjacent to the single True cell must be True.
        """
        mask = np.zeros((5, 5), dtype=bool)
        mask[2, 2] = True
        b = RasterBackend(shape=(5, 5))
        contact = b.neighbor_contact(mask)
        # all 8 Moore neighbors of (2,2) must have contact
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                assert contact[2+dr, 2+dc], f"Expected contact at ({2+dr},{2+dc})"

    def test_isolated_cell_far_cells_no_contact(self):
        """Cells far from the single True source must have no contact."""
        mask = np.zeros((5, 5), dtype=bool)
        mask[2, 2] = True
        b = RasterBackend(shape=(5, 5))
        contact = b.neighbor_contact(mask)
        # corners are distance >1 from (2,2) — no contact
        assert not contact[0, 0]
        assert not contact[0, 4]
        assert not contact[4, 0]
        assert not contact[4, 4]

    def test_all_false_gives_no_contact(self):
        """All-False mask → no cell has a True neighbor."""
        mask = np.zeros((3, 3), dtype=bool)
        b = RasterBackend(shape=(3, 3))
        assert not b.neighbor_contact(mask).any()

    def test_all_true_all_have_contact(self):
        """All-True mask → every cell has at least one True neighbor."""
        mask = np.ones((3, 3), dtype=bool)
        b = RasterBackend(shape=(3, 3))
        contact = b.neighbor_contact(mask)
        # every cell has True neighbors — all must be True
        assert contact.all()


# ══════════════════════════════════════════════════════════════════════════════
# Neighborhood directions
# ══════════════════════════════════════════════════════════════════════════════

class TestDirs:

    def test_moore_has_8_directions(self):
        assert len(DIRS_MOORE) == 8

    def test_von_neumann_has_4_directions(self):
        assert len(DIRS_VON_NEUMANN) == 4

    def test_moore_includes_diagonals(self):
        diagonals = {(dr, dc) for dr, dc in DIRS_MOORE if dr != 0 and dc != 0}
        assert len(diagonals) == 4

    def test_von_neumann_no_diagonals(self):
        diagonals = [(dr, dc) for dr, dc in DIRS_VON_NEUMANN if dr != 0 and dc != 0]
        assert diagonals == []
