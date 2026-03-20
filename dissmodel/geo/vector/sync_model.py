"""
dissmodel/geo/vector/sync_model.py
=====================================
SyncSpatialModel — SpatialModel with automatic _past snapshot semantics.

This module provides the snapshot mechanism equivalent to TerraME's
``cs:synchronize()``, as a reusable base class for any vector model that
needs per-step state history (LUCC, fire spread, epidemic models, etc.).

How it works
------------
At the start of each step, ``synchronize()`` copies the current value of
every column in ``land_use_types`` to a ``<col>_past`` column in the
GeoDataFrame. Models can read ``gdf["f_past"]`` to access the state at the
beginning of the current step, regardless of changes made during execution.

Usage
-----
Subclass ``SyncSpatialModel`` instead of ``SpatialModel`` and declare
``self.land_use_types`` in ``setup()``:

    class MyModel(SyncSpatialModel):
        def setup(self, gdf, ...):
            super().setup(gdf)                 # SpatialModel setup
            self.land_use_types = ["f", "d"]   # columns to snapshot

        def execute(self):
            past_f = self.gdf["f_past"]        # state at step start
            ...

The ``synchronize()`` method is called automatically:
  - once before the first ``execute()``   → snapshot of the initial state
  - once after each ``execute()``         → snapshot for the next step

It can also be called manually when needed (e.g. mid-step resets).

Relationship to domain libraries
----------------------------------
``dissluc`` uses this class as the base for its LUCC components,
exposing it under the domain-specific alias ``LUCSpatialModel``:

    # dissluc/core.py
    from dissmodel.geo.vector.sync_model import SyncSpatialModel as LUCSpatialModel
"""
from __future__ import annotations

from dissmodel.geo.vector.spatial_model import SpatialModel


class SyncSpatialModel(SpatialModel):
    """
    ``SpatialModel`` with automatic ``_past`` snapshot semantics.

    Extends :class:`~dissmodel.geo.vector.spatial_model.SpatialModel` with
    a ``synchronize()`` method that copies each column listed in
    ``self.land_use_types`` to a ``<col>_past`` column before and after
    every simulation step.

    This is the Python equivalent of TerraME's ``cs:synchronize()`` — it
    ensures that every model reads a consistent snapshot of the state at
    the beginning of the current step, even when multiple models share the
    same GeoDataFrame.

    Subclass contract
    -----------------
    Declare ``self.land_use_types`` (list of column names) in ``setup()``.
    ``SyncSpatialModel`` will manage all ``<col>_past`` columns automatically.
    Subclasses must **not** create or update ``_past`` columns manually.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        Passed through to :class:`~dissmodel.geo.vector.spatial_model.SpatialModel`.
    **kwargs
        Any additional keyword arguments accepted by the parent class.

    Examples
    --------
    >>> class ForestCA(SyncSpatialModel):
    ...     def setup(self, gdf, rate=0.01):
    ...         super().setup(gdf)
    ...         self.land_use_types = ["forest", "defor"]
    ...         self.rate = rate
    ...
    ...     def execute(self):
    ...         # forest_past holds the state at the start of this step
    ...         gain = self.gdf["forest_past"] * self.rate
    ...         self.gdf["forest"] = self.gdf["forest_past"] + gain
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
        Copy each column in ``land_use_types`` to ``<col>_past``.

        Equivalent to ``cs:synchronize()`` in TerraME. Called automatically
        before the first step and after each ``execute()``. Can also be
        called manually when an explicit mid-step snapshot is needed.

        Does nothing if ``land_use_types`` has not been set yet (safe to
        call before ``setup()`` completes).
        """
        if not hasattr(self, "land_use_types"):
            return
        for col in self.land_use_types:
            self.gdf[col + "_past"] = self.gdf[col].copy()
