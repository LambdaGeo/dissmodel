"""
dissmodel/geo/raster/sync_model.py
=====================================
SyncRasterModel — RasterModel with automatic _past snapshot semantics.

This module provides the snapshot mechanism equivalent to TerraME's
``cs:synchronize()``, as a reusable base class for any raster model that
needs per-step state history (LUCC, fire spread, epidemic models, etc.).

How it works
------------
At the start of each step, ``synchronize()`` copies the current NumPy array
for every name in ``land_use_types`` to a ``<name>_past`` array in the
RasterBackend. Models can call ``self.backend.get("f_past")`` to access the
state at the beginning of the current step, regardless of changes made
during execution.

Usage
-----
Subclass ``SyncRasterModel`` instead of ``RasterModel`` and declare
``self.land_use_types`` in ``setup()``:

    class MyRasterModel(SyncRasterModel):
        def setup(self, backend, ...):
            super().setup(backend)               # RasterModel setup
            self.land_use_types = ["f", "d"]     # arrays to snapshot

        def execute(self):
            f_past = self.backend.get("f_past")  # state at step start
            ...

The ``synchronize()`` method is called automatically:
  - once before the first ``execute()``   → snapshot of the initial state
  - once after each ``execute()``         → snapshot for the next step

It can also be called manually when needed.

Relationship to domain libraries
----------------------------------
``dissluc`` uses this class as the base for its raster LUCC components,
exposing it under the domain-specific alias ``LUCRasterModel``:

    # dissluc/raster/core.py
    from dissmodel.geo.raster.sync_model import SyncRasterModel as LUCRasterModel
"""
from __future__ import annotations

import numpy as np

from dissmodel.geo import RasterModel


class SyncRasterModel(RasterModel):
    """
    ``RasterModel`` with automatic ``_past`` snapshot semantics.

    Extends :class:`~dissmodel.geo.raster.model.RasterModel` with a
    ``synchronize()`` method that copies each array listed in
    ``self.land_use_types`` to a ``<name>_past`` array in the
    :class:`~dissmodel.geo.raster.backend.RasterBackend` before and after
    every simulation step.

    This is the raster analogue of
    :class:`~dissmodel.geo.vector.sync_model.SyncSpatialModel` and the
    Python equivalent of TerraME's ``cs:synchronize()``.

    Subclass contract
    -----------------
    Declare ``self.land_use_types`` (list of array names) in ``setup()``.
    ``SyncRasterModel`` will manage all ``<name>_past`` arrays automatically.
    Subclasses must **not** create or update ``_past`` arrays manually.

    Parameters
    ----------
    backend : RasterBackend
        Passed through to :class:`~dissmodel.geo.raster.model.RasterModel`.
    **kwargs
        Any additional keyword arguments accepted by the parent class.

    Examples
    --------
    >>> class ForestRaster(SyncRasterModel):
    ...     def setup(self, backend, rate=0.01):
    ...         super().setup(backend)
    ...         self.land_use_types = ["forest", "defor"]
    ...         self.rate = rate
    ...
    ...     def execute(self):
    ...         forest_past = self.backend.get("forest_past")
    ...         gain = forest_past * self.rate
    ...         self.backend.arrays["forest"] = forest_past + gain
    """

    def process(self) -> None:
        """
        Simulation loop with automatic snapshot management.

        Overrides :meth:`~dissmodel.core.Model.process` to insert
        :meth:`synchronize` calls before the first step and after each step.
        """
        if self.env.now() < self.start_time:
            self.hold(self.start_time - self.env.now())

        # initial snapshot — captures state at t=0 before any execution
        self.synchronize()

        while self.env.now() < self.end_time:
            self.execute()
            self.synchronize()   # update snapshot for the next step
            self.hold(self._step)

    def synchronize(self) -> None:
        """
        Copy each array in ``land_use_types`` to ``<name>_past`` in the backend.

        Equivalent to ``cs:synchronize()`` in TerraME. Called automatically
        before the first step and after each ``execute()``. Can also be
        called manually when an explicit mid-step snapshot is needed.

        Does nothing if ``land_use_types`` has not been set yet (safe to
        call before ``setup()`` completes).
        """
        if not hasattr(self, "land_use_types"):
            return
        for name in self.land_use_types:
            self.backend.set(name + "_past", self.backend.get(name).copy())
