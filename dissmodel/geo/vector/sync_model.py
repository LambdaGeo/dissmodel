"""
dissmodel/geo/vector/sync_model.py
=====================================
SyncSpatialModel — SpatialModel with automatic _past snapshot semantics.

This module provides the snapshot mechanism equivalent to TerraME's
``cs:synchronize()``, as a reusable base class for any vector model that
needs per-step state history (LUCC, fire spread, epidemic models, etc.).

How it works
------------
Before the first ``execute()``, ``pre_execute()`` calls ``synchronize()``
once to capture the initial state. After each ``execute()``,
``post_execute()`` calls ``synchronize()`` again to freeze the current
state as ``<col>_past`` for the next step.

Models can read ``gdf["f_past"]`` inside ``execute()`` to access the state
at the beginning of the current step — equivalent to TerraME's
``cell.past[attr]``.

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
    ``pre_execute()`` / ``post_execute()`` hooks that copy each column
    listed in ``self.land_use_types`` to a ``<col>_past`` column before
    and after every simulation step.

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

    def pre_execute(self) -> None:
        """
        Snapshot columns before the first step.

        On the first call, freezes the initial state into ``<col>_past``
        columns so that ``execute()`` can read them. Subsequent calls are
        no-ops — post_execute() handles ongoing snapshots.
        """
        if not getattr(self, "_first_sync_done", False):
            self.synchronize()
            self._first_sync_done = True

    def post_execute(self) -> None:
        """
        Snapshot columns after each step.

        Freezes the current state into ``<col>_past`` columns so that
        the next ``execute()`` call reads the state at step start —
        equivalent to TerraME's ``cs:synchronize()``.
        """
        self.synchronize()

    def synchronize(self) -> None:
        """
        Copy each column in ``land_use_types`` to ``<col>_past``.

        Equivalent to ``cs:synchronize()`` in TerraME. Called automatically
        via ``pre_execute()`` before the first step and via ``post_execute()``
        after each ``execute()``. Can also be called manually when an explicit
        mid-step snapshot is needed.

        Does nothing if ``land_use_types`` has not been set yet (safe to
        call before ``setup()`` completes).
        """
        if not hasattr(self, "land_use_types"):
            return
        for col in self.land_use_types:
            self.gdf[col + "_past"] = self.gdf[col].copy()
