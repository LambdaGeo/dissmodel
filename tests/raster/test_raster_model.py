"""
tests/raster/test_model.py
============================
Tests for RasterModel — the base class for raster simulation models.
"""
from __future__ import annotations

import pytest
import numpy as np

from dissmodel.core import Environment
from dissmodel.geo.raster.backend import RasterBackend, DIRS_MOORE
from dissmodel.geo.raster.raster_model import RasterModel
from dissmodel.geo import raster_grid


# ── helpers ───────────────────────────────────────────────────────────────────

class CounterRaster(RasterModel):
    """Adds 1 to every cell of 'state' on each step — push pattern."""
    def setup(self, backend):
        super().setup(backend)

    def execute(self):
        self.backend.arrays["state"] = self.backend.get("state") + 1


class TimeReaderRaster(RasterModel):
    """Records env.now() at each step."""
    def setup(self, backend, times):
        super().setup(backend)
        self._times = times

    def execute(self):
        self._times.append(self.env.now())


class NullRaster(RasterModel):
    """Does nothing — useful for setup tests."""
    def setup(self, backend):
        super().setup(backend)

    def execute(self):
        pass


# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def backend_3x3():
    return raster_grid(rows=3, cols=3, attrs={"state": np.zeros((3, 3), dtype=np.int32)})


@pytest.fixture
def backend_5x5():
    return raster_grid(rows=5, cols=5, attrs={"state": np.zeros((5, 5), dtype=np.int32)})


# ══════════════════════════════════════════════════════════════════════════════
# setup()
# ══════════════════════════════════════════════════════════════════════════════

class TestSetup:

    def test_backend_stored(self, backend_3x3):
        env = Environment(start_time=1, end_time=1)
        m = NullRaster(backend=backend_3x3)
        assert m.backend is backend_3x3

    def test_shape_set(self, backend_3x3):
        env = Environment(start_time=1, end_time=1)
        m = NullRaster(backend=backend_3x3)
        assert m.shape == (3, 3)

    def test_shift_is_callable(self, backend_3x3):
        env = Environment(start_time=1, end_time=1)
        m = NullRaster(backend=backend_3x3)
        assert callable(m.shift)

    def test_dirs_defaults_to_moore(self, backend_3x3):
        env = Environment(start_time=1, end_time=1)
        m = NullRaster(backend=backend_3x3)
        assert m.dirs == DIRS_MOORE

    def test_shift_works_on_array(self, backend_3x3):
        env = Environment(start_time=1, end_time=1)
        m   = NullRaster(backend=backend_3x3)
        arr = np.ones((3, 3), dtype=np.int32)
        result = m.shift(arr, 1, 0)
        assert result.shape == (3, 3)
        assert result[0, 0] == 0   # edge filled with 0


# ══════════════════════════════════════════════════════════════════════════════
# execute() — push pattern
# ══════════════════════════════════════════════════════════════════════════════

class TestExecute:

    def test_counter_one_step(self, backend_3x3):
        env = Environment(start_time=1, end_time=1)
        CounterRaster(backend=backend_3x3)
        env.run()
        assert (backend_3x3.get("state") == 1).all()

    def test_counter_n_steps(self, backend_3x3):
        N = 5
        env = Environment(start_time=1, end_time=N)
        CounterRaster(backend=backend_3x3)
        env.run()
        assert (backend_3x3.get("state") == N).all()

    def test_env_now_accessible(self, backend_3x3):
        times = []
        env = Environment(start_time=1, end_time=3)
        TimeReaderRaster(backend=backend_3x3, times=times)
        env.run()
        assert times == [1, 2, 3]


# ══════════════════════════════════════════════════════════════════════════════
# Multiple models — salabim environment
# ══════════════════════════════════════════════════════════════════════════════

class TestEnvironmentIntegration:

    def test_two_models_same_env(self):
        """Two RasterModels registered in the same env both execute."""
        b1 = raster_grid(rows=3, cols=3, attrs={"state": np.zeros((3,3), dtype=np.int32)})
        b2 = raster_grid(rows=3, cols=3, attrs={"state": np.zeros((3,3), dtype=np.int32)})
        env = Environment(start_time=1, end_time=3)
        CounterRaster(backend=b1)
        CounterRaster(backend=b2)
        env.run()
        assert (b1.get("state") == 3).all()
        assert (b2.get("state") == 3).all()

    def test_model_reads_updated_state_from_previous(self):
        """
        Second model reads state already updated by first model in same step.
        Model A doubles state; Model B adds 1. After 1 step from all-ones:
        A runs first → state=2, then B → state=3.
        """
        b = raster_grid(rows=3, cols=3,
                             attrs={"state": np.ones((3,3), dtype=np.int32)})

        class DoubleModel(RasterModel):
            def setup(self, backend): super().setup(backend)
            def execute(self): self.backend.arrays["state"] *= 2

        class AddOneModel(RasterModel):
            def setup(self, backend): super().setup(backend)
            def execute(self): self.backend.arrays["state"] += 1

        env = Environment(start_time=1, end_time=1)
        DoubleModel(backend=b)
        AddOneModel(backend=b)
        env.run()
        assert (b.get("state") == 3).all()
