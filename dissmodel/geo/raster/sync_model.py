"""
dissmodel/geo/raster/sync_model.py
=====================================
SyncRasterModel and StepSyncModel.

SyncRasterModel
---------------
RasterModel with automatic _past snapshot semantics, equivalent to
TerraME's cs:synchronize() for a single model.

StepSyncModel
-------------
Shared synchronizer for multiple SyncRasterModel instances that share the
same backend. Must be created before the models it synchronizes.

Relationship to domain libraries
----------------------------------
dissluc uses SyncRasterModel as the base for its raster LUCC components,
exposing it under the domain-specific alias LUCRasterModel:

    # dissluc/raster/core.py
    from dissmodel.geo.raster.sync_model import SyncRasterModel as LUCRasterModel
"""
from __future__ import annotations

import numpy as np

from dissmodel.core import Model
from dissmodel.geo import RasterModel


class SyncRasterModel(RasterModel):
    """
    RasterModel with automatic _past snapshot semantics.

    Extends RasterModel with a synchronize() method that copies each array
    listed in self.land_use_types to a <name>_past array in the
    RasterBackend before and after every simulation step.

    Subclass contract
    -----------------
    Declare self.land_use_types (list of array names) in setup().
    SyncRasterModel will manage all <name>_past arrays automatically.
    Subclasses must not create or update _past arrays manually.

    Attributes
    ----------
    auto_sync : bool
        If True (default), synchronize() is called automatically before
        the first step and after each execute(). Set to False when a
        StepSyncModel handles synchronization for multiple models sharing
        the same backend.

    Usage -- single model (default, auto_sync=True)
    ------------------------------------------------
    class MyRasterModel(SyncRasterModel):
        def setup(self, backend, ...):
            super().setup(backend)
            self.land_use_types = ["f", "d"]

        def execute(self):
            f_past = self.backend.get("f_past")  # state at step start
            ...

    Usage -- multiple models sharing a backend (auto_sync=False)
    -------------------------------------------------------------
    class FloodModel(SyncRasterModel):
        def setup(self, backend, taxa_elevacao=0.011):
            super().setup(backend)
            self.land_use_types = ["uso", "alt"]
            self.auto_sync      = False

        def execute(self):
            uso_past = self.backend.get("uso_past")  # frozen by StepSyncModel
            alt_past = self.backend.get("alt_past")
            ...

    # In the executor -- StepSyncModel created BEFORE the models:
    env = Environment(end_time=88)
    StepSyncModel(backend=backend, bands=["uso", "alt", "solo"])
    FloodModel(backend=backend, taxa_elevacao=0.011)
    MangroveModel(backend=backend)
    env.run()

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

    def setup(self, backend, **kwargs) -> None:
        super().setup(backend)
        self.auto_sync = True   # default: self-managed synchronization

    def process(self) -> None:
        """
        Simulation loop with automatic snapshot management.

        Overrides Model.process() to insert synchronize() calls before
        the first step and after each execute(), when auto_sync is True.
        """
        if self.env.now() < self.start_time:
            self.hold(self.start_time - self.env.now())

        if self.auto_sync:
            self.synchronize()   # initial snapshot -- state at t=0

        while self.env.now() < self.end_time:
            self.execute()
            if self.auto_sync:
                self.synchronize()   # snapshot for next step
            self.hold(self._step)

    def synchronize(self) -> None:
        """
        Copy each array in land_use_types to <name>_past in the backend.

        Equivalent to cs:synchronize() in TerraME. Called automatically
        when auto_sync=True, or by StepSyncModel when auto_sync=False.
        Can also be called manually when an explicit mid-step snapshot
        is needed.

        Does nothing if land_use_types has not been set yet (safe to
        call before setup() completes).
        """
        if not hasattr(self, "land_use_types"):
            return
        for name in self.land_use_types:
            self.backend.set(name + "_past", self.backend.get(name).copy())


class StepSyncModel(Model):
    """
    Shared synchronizer for multiple SyncRasterModel instances.

    Freezes a declared set of bands in "<name>_past" on the shared backend
    once per step, before any other model runs. This is the shared equivalent
    of TerraME's cs:synchronize() when multiple models share a backend and
    both need to read the state at the beginning of the step.

    Must be created BEFORE the models it synchronizes -- the salabim
    scheduler executes components in creation order within the same timestep.

    Parameters
    ----------
    backend : RasterBackend
        The shared backend. All models in the group must use the same instance.
    bands : list[str]
        Band names to freeze each step. Typically the union of all models'
        land_use_types. Duplicates are ignored.

    Examples
    --------
    >>> env = Environment(end_time=88)

    >>> # 1. StepSyncModel first -- runs first in every timestep
    >>> StepSyncModel(backend=backend, bands=["uso", "alt", "solo"])

    >>> # 2. Models after -- read from _past frozen above
    >>> FloodModel(backend=backend, taxa_elevacao=0.011)   # auto_sync=False
    >>> MangroveModel(backend=backend)                     # auto_sync=False

    >>> env.run()
    """

    def setup(self, backend, bands: list[str]) -> None:
        if not bands:
            raise ValueError("StepSyncModel requires at least one band name.")
        self.backend = backend
        # deduplicate preserving insertion order
        seen:        set[str]  = set()
        self._bands: list[str] = []
        for name in bands:
            if name not in seen:
                seen.add(name)
                self._bands.append(name)

    def execute(self) -> None:
        """
        Freeze all registered bands in "<name>_past" on the shared backend.

        Called once per timestep before any registered model runs
        (salabim creation-order guarantee).
        """
        print(f"[StepSyncModel] t={self.env.now()} freezing {self._bands}")
        for name in self._bands:
            arr = self.backend.arrays.get(name)
            if arr is not None:
                self.backend.set(name + "_past", arr.copy())