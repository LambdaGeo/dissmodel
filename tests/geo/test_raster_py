"""
tests/geo/test_raster_backend.py
tests/visualization/test_raster_map.py

Testes simples para RasterBackend, RasterModel e RasterMap.

Execução
--------
    pytest tests/ -v
    pytest tests/geo/test_raster_backend.py -v
"""
from __future__ import annotations

import numpy as np
import pytest

from dissmodel.geo.raster_backend import RasterBackend, DIRS_MOORE, DIRS_VON_NEUMANN


# ══════════════════════════════════════════════════════════════════════════════
# RasterBackend
# ══════════════════════════════════════════════════════════════════════════════

class TestRasterBackend:

    def setup_method(self):
        self.b = RasterBackend(shape=(5, 5))
        data = np.arange(25, dtype=float).reshape(5, 5)
        self.b.set("val", data)

    # ── set / get ─────────────────────────────────────────────────────────────

    def test_set_stores_copy(self):
        arr = np.zeros((5, 5))
        self.b.set("x", arr)
        arr[0, 0] = 99
        assert self.b.get("x")[0, 0] == 0   # cópia, não referência

    def test_get_returns_reference(self):
        ref = self.b.get("val")
        ref[0, 0] = 999
        assert self.b.arrays["val"][0, 0] == 999   # referência direta

    def test_shape(self):
        assert self.b.shape == (5, 5)

    # ── snapshot ──────────────────────────────────────────────────────────────

    def test_snapshot_is_deep_copy(self):
        snap = self.b.snapshot()
        self.b.arrays["val"][0, 0] = 999
        assert snap["val"][0, 0] != 999   # independente

    def test_snapshot_has_all_arrays(self):
        self.b.set("extra", np.ones((5, 5)))
        snap = self.b.snapshot()
        assert "val" in snap
        assert "extra" in snap

    # ── shift2d ───────────────────────────────────────────────────────────────

    def test_shift2d_north(self):
        arr = np.zeros((3, 3))
        arr[1, 1] = 1.0
        shifted = RasterBackend.shift2d(arr, -1, 0)  # norte
        assert shifted[0, 1] == 1.0
        assert shifted[1, 1] == 0.0

    def test_shift2d_south(self):
        arr = np.zeros((3, 3))
        arr[1, 1] = 1.0
        shifted = RasterBackend.shift2d(arr, 1, 0)   # sul
        assert shifted[2, 1] == 1.0

    def test_shift2d_border_zeros(self):
        arr = np.ones((3, 3))
        shifted = RasterBackend.shift2d(arr, 0, 1)   # leste
        # coluna 0 deve ser zero (borda)
        assert np.all(shifted[:, 0] == 0)

    def test_shift2d_identity_zero(self):
        arr = np.eye(3)
        shifted = RasterBackend.shift2d(arr, 0, 0)
        np.testing.assert_array_equal(shifted, arr)

    # ── neighbor_contact ──────────────────────────────────────────────────────

    def test_neighbor_contact_propagates(self):
        cond = np.zeros((5, 5), dtype=bool)
        cond[2, 2] = True
        contact = self.b.neighbor_contact(cond)
        # todas as células ao redor de (2,2) devem ser True
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                assert contact[2+dr, 2+dc]

    def test_neighbor_contact_corner(self):
        cond = np.zeros((5, 5), dtype=bool)
        cond[0, 0] = True
        contact = self.b.neighbor_contact(cond)
        assert contact[0, 1]
        assert contact[1, 0]
        assert contact[1, 1]
        assert not contact[0, 2]

    # ── focal_sum_mask ────────────────────────────────────────────────────────

    def test_focal_sum_mask_center(self):
        mask = np.zeros((5, 5), dtype=bool)
        mask[2, 2] = True
        counts = self.b.focal_sum_mask(mask)
        # vizinhos de (2,2) devem ter contagem 1
        assert counts[1, 1] == 1
        assert counts[1, 2] == 1
        assert counts[2, 1] == 1
        # (2,2) não conta a si mesmo
        assert counts[2, 2] == 0

    def test_focal_sum_mask_all_true(self):
        mask = np.ones((3, 3), dtype=bool)
        b = RasterBackend(shape=(3, 3))
        counts = b.focal_sum_mask(mask)
        # célula central tem 8 vizinhos True
        assert counts[1, 1] == 8
        # canto tem 3 vizinhos True
        assert counts[0, 0] == 3

    # ── dirs ──────────────────────────────────────────────────────────────────

    def test_dirs_moore_count(self):
        assert len(DIRS_MOORE) == 8

    def test_dirs_von_neumann_count(self):
        assert len(DIRS_VON_NEUMANN) == 4

    def test_dirs_von_neumann_no_diagonals(self):
        for dr, dc in DIRS_VON_NEUMANN:
            assert abs(dr) + abs(dc) == 1   # sem diagonais

    # ── repr ──────────────────────────────────────────────────────────────────

    def test_repr_contains_shape(self):
        assert "5, 5" in repr(self.b)

    def test_repr_contains_band_names(self):
        assert "val" in repr(self.b)


# ══════════════════════════════════════════════════════════════════════════════
# RasterModel
# ══════════════════════════════════════════════════════════════════════════════

class TestRasterModel:

    def test_setup_populates_attrs(self):
        from dissmodel.geo.raster_model import RasterModel
        from dissmodel.core import Environment

        class DummyModel(RasterModel):
            def setup(self, backend):
                super().setup(backend)
            def execute(self):
                pass

        b   = RasterBackend(shape=(4, 4))
        env = Environment(start_time=1, end_time=1)
        m   = DummyModel(backend=b)

        assert m.backend is b
        assert m.shape == (4, 4)
        assert m.shift is RasterBackend.shift2d
        assert m.dirs is DIRS_MOORE

    def test_execute_called_by_environment(self):
        from dissmodel.geo.raster_model import RasterModel
        from dissmodel.core import Environment

        calls = []

        class CountModel(RasterModel):
            def setup(self, backend):
                super().setup(backend)
            def execute(self):
                calls.append(self.env.now())

        b   = RasterBackend(shape=(3, 3))
        env = Environment(start_time=1, end_time=3)
        CountModel(backend=b)
        env.run()

        assert calls == [1, 2, 3]

    def test_subclass_can_modify_backend(self):
        from dissmodel.geo.raster_model import RasterModel
        from dissmodel.core import Environment

        class IncrementModel(RasterModel):
            def setup(self, backend):
                super().setup(backend)
            def execute(self):
                self.backend.arrays["v"] += 1

        b = RasterBackend(shape=(2, 2))
        b.set("v", np.zeros((2, 2)))

        env = Environment(start_time=1, end_time=3)
        IncrementModel(backend=b)
        env.run()

        np.testing.assert_array_equal(b.get("v"), np.full((2, 2), 3.0))


# ══════════════════════════════════════════════════════════════════════════════
# RasterMap — testa sem display (headless)
# ══════════════════════════════════════════════════════════════════════════════

class TestRasterMap:

    def test_headless_saves_png(self, tmp_path, monkeypatch):
        """RasterMap deve salvar PNG em headless sem levantar exceção."""
        import os
        from dissmodel.visualization.raster_map import RasterMap
        from dissmodel.core import Environment

        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("RASTER_MAP_INTERACTIVE", "0")

        b = RasterBackend(shape=(10, 10))
        b.set("estado", np.random.randint(0, 3, (10, 10)))

        env = Environment(start_time=1, end_time=2)
        RasterMap(backend=b, band="estado")
        env.run()

        frames = list((tmp_path / "raster_map_frames").glob("estado_step_*.png"))
        assert len(frames) == 2

    def test_headless_categorical(self, tmp_path, monkeypatch):
        """Modo categórico (color_map) não deve levantar exceção."""
        import os
        from dissmodel.visualization.raster_map import RasterMap
        from dissmodel.core import Environment

        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("RASTER_MAP_INTERACTIVE", "0")

        b = RasterBackend(shape=(8, 8))
        b.set("uso", np.random.choice([1, 2, 3], (8, 8)))

        color_map = {1: "#006400", 2: "#808000", 3: "#00008b"}
        labels    = {1: "A", 2: "B", 3: "C"}

        env = Environment(start_time=1, end_time=1)
        RasterMap(backend=b, band="uso", color_map=color_map, labels=labels)
        env.run()

        frames = list((tmp_path / "raster_map_frames").glob("uso_step_*.png"))
        assert len(frames) == 1

    def test_headless_continuous_with_mask(self, tmp_path, monkeypatch):
        """Modo contínuo com mask_band não deve levantar exceção."""
        from dissmodel.visualization.raster_map import RasterMap
        from dissmodel.core import Environment

        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("RASTER_MAP_INTERACTIVE", "0")

        b = RasterBackend(shape=(8, 8))
        alt = np.random.uniform(0, 10, (8, 8))
        uso = np.ones((8, 8), dtype=int)
        uso[0, :] = 3   # MAR
        b.set("alt", alt)
        b.set("uso", uso)

        env = Environment(start_time=1, end_time=1)
        RasterMap(
            backend        = b,
            band           = "alt",
            cmap           = "terrain",
            colorbar_label = "Altitude (m)",
            mask_band      = "uso",
            mask_value     = 3,
        )
        env.run()

        frames = list((tmp_path / "raster_map_frames").glob("alt_step_*.png"))
        assert len(frames) == 1

    def test_missing_band_does_not_crash(self, tmp_path, monkeypatch):
        """Band inexistente deve renderizar mensagem, não levantar exceção."""
        from dissmodel.visualization.raster_map import RasterMap
        from dissmodel.core import Environment

        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("RASTER_MAP_INTERACTIVE", "0")

        b = RasterBackend(shape=(5, 5))
        b.set("uso", np.ones((5, 5)))

        env = Environment(start_time=1, end_time=1)
        RasterMap(backend=b, band="inexistente")
        env.run()   # não deve levantar
