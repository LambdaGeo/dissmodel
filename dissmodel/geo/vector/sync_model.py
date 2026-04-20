"""
dissmodel/geo/vector/sync_model.py
=====================================
SyncSpatialModel and StepSyncSpatialModel.

SyncSpatialModel
----------------
SpatialModel with automatic _past snapshot semantics, equivalent to
TerraME's cs:synchronize() for a single vector model.

StepSyncSpatialModel
--------------------
Shared synchronizer for multiple SyncSpatialModel instances that share the
same GeoDataFrame. Must be created before the models it synchronizes.

Relationship to domain libraries
----------------------------------
dissluc uses SyncSpatialModel as the base for its LUCC components,
exposing it under the domain-specific alias LUCSpatialModel:

    # dissluc/core.py
    from dissmodel.geo.vector.sync_model import SyncSpatialModel as LUCSpatialModel
"""
from __future__ import annotations

from dissmodel.core import Model
from dissmodel.geo.vector.spatial_model import SpatialModel


class SyncSpatialModel(SpatialModel):
    """
    SpatialModel with automatic _past snapshot semantics.

    Extends SpatialModel with a synchronize() method that copies each column
    listed in self.land_use_types to a <col>_past column in the GeoDataFrame
    before and after every simulation step.

    This is the Python equivalent of TerraME's cs:synchronize() -- it
    ensures that every model reads a consistent snapshot of the state at
    the beginning of the current step, even when multiple models share the
    same GeoDataFrame.

    Subclass contract
    -----------------
    Declare self.land_use_types (list of column names) in setup().
    SyncSpatialModel will manage all <col>_past columns automatically.
    Subclasses must not create or update _past columns manually.

    Attributes
    ----------
    auto_sync : bool
        If True (default), synchronize() is called automatically before
        the first step and after each execute(). Set to False when a
        StepSyncSpatialModel handles synchronization for multiple models
        sharing the same GeoDataFrame.

        Defined in __init__ (not setup) so subclasses that override setup()
        without calling super() still have the attribute.

    Usage -- single model (default, auto_sync=True)
    ------------------------------------------------
    class MyModel(SyncSpatialModel):
        def setup(self, ...):
            self.land_use_types = ["f", "d"]

        def execute(self):
            past_f = self.gdf["f_past"]   # state at step start
            ...

    Usage -- multiple models sharing a GeoDataFrame (auto_sync=False)
    ------------------------------------------------------------------
    class FloodVector(SyncSpatialModel):
        def setup(self, taxa_elevacao=0.011):
            self.land_use_types = ["uso", "alt"]
            self.auto_sync      = False

        def execute(self):
            uso_past = self.gdf["uso_past"]   # frozen by StepSyncSpatialModel
            alt_past = self.gdf["alt_past"]
            ...

    # In the executor -- StepSyncSpatialModel created BEFORE the models:
    env = Environment(end_time=88)
    StepSyncSpatialModel(gdf=gdf, cols=["uso", "alt", "solo"])
    FloodVector(gdf=gdf, taxa_elevacao=0.011)
    MangroveVector(gdf=gdf)
    env.run()

    Examples
    --------
    >>> class ForestCA(SyncSpatialModel):
    ...     def setup(self, rate=0.01):
    ...         self.land_use_types = ["forest", "defor"]
    ...         self.rate = rate
    ...
    ...     def execute(self):
    ...         gain = self.gdf["forest_past"] * self.rate
    ...         self.gdf["forest"] = self.gdf["forest_past"] + gain
    """

    def __init__(self, gdf, **kwargs) -> None:
        self.auto_sync = True   # defined here so setup() override never breaks it
        super().__init__(gdf, **kwargs)

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
        Copy each column in land_use_types to <col>_past in the GeoDataFrame.

        Equivalent to cs:synchronize() in TerraME. Called automatically
        when auto_sync=True, or by StepSyncSpatialModel when auto_sync=False.
        Can also be called manually when an explicit mid-step snapshot is
        needed.

        Does nothing if land_use_types has not been set yet (safe to
        call before setup() completes).
        """
        if not hasattr(self, "land_use_types"):
            return
        for col in self.land_use_types:
            self.gdf[col + "_past"] = self.gdf[col].copy()


class StepSyncSpatialModel(Model):
    """
    Shared synchronizer for multiple SyncSpatialModel instances.

    Freezes a declared set of columns in "<col>_past" on the shared
    GeoDataFrame once per step, before any other model runs. This is the
    shared equivalent of TerraME's cs:synchronize() when multiple models
    share a GeoDataFrame and both need to read the state at the beginning
    of the step.

    Must be created BEFORE the models it synchronizes -- the salabim
    scheduler executes components in creation order within the same timestep.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        The shared GeoDataFrame. All models in the group must use the same
        instance.
    cols : list[str]
        Column names to freeze each step. Typically the union of all models'
        land_use_types. Duplicates are ignored.

    Examples
    --------
    >>> env = Environment(end_time=88)

    >>> # 1. StepSyncSpatialModel first -- runs first in every timestep
    >>> StepSyncSpatialModel(gdf=gdf, cols=["uso", "alt", "solo"])

    >>> # 2. Models after -- read from _past frozen above
    >>> FloodVector(gdf=gdf, taxa_elevacao=0.011)   # auto_sync=False
    >>> MangroveVector(gdf=gdf)                     # auto_sync=False

    >>> env.run()
    """

    def setup(self, gdf, cols: list[str]) -> None:
        if not cols:
            raise ValueError("StepSyncSpatialModel requires at least one column name.")
        self.gdf = gdf
        # deduplicate preserving insertion order
        seen:      set[str]  = set()
        self._cols: list[str] = []
        for col in cols:
            if col not in seen:
                seen.add(col)
                self._cols.append(col)

    def execute(self) -> None:
        """
        Freeze all registered columns in "<col>_past" on the shared GeoDataFrame.

        Called once per timestep before any registered model runs
        (salabim creation-order guarantee).
        """
        for col in self._cols:
            if col in self.gdf.columns:
                self.gdf[col + "_past"] = self.gdf[col].copy()