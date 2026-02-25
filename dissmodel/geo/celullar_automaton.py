from __future__ import annotations

import math
from typing import Any, Optional, Type

import numpy as np
import geopandas as gpd
from libpysal.weights import Queen, W

from dissmodel.core import Model
from dissmodel.geo import attach_neighbors

# A strategy is a libpysal weight class (not an instance)
StrategyType = Type[W]


class CellularAutomaton(Model):
    """
    Base class for spatial cellular automata backed by a GeoDataFrame.

    Args:
        gdf:        GeoDataFrame with geometries and a state attribute.
        state_attr: Column name representing the cell state.
        step:       Time increment per execution step.
        start_time: Simulation start time.
        end_time:   Simulation end time.
        name:       Optional model name.
        dim:        Optional grid dimensions (n_cols, n_rows).
        *args:      Extra positional arguments forwarded to :class:`Model`.
        **kwargs:   Extra keyword arguments forwarded to :class:`Model`.
    """

    def __init__(
        self,
        gdf: gpd.GeoDataFrame,
        state_attr: str = "state",
        step: float = 1,
        start_time: float = 0,
        end_time: float = math.inf,
        name: str = "",
        dim: Optional[tuple[int, int]] = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.gdf = gdf
        self.state_attr = state_attr
        self._neighborhood_created: bool = False
        self._neighs_cache: dict[Any, list[Any]] = {}
        self.dim = dim
        super().__init__(
            step=step,
            start_time=start_time,
            end_time=end_time,
            name=name,
            *args,
            **kwargs,
        )

    def initialize(self) -> None:
        """Override in subclasses to set up initial state."""
        pass

    def create_neighborhood(
        self,
        strategy: StrategyType = Queen,
        neighbors_dict: Optional[dict[Any, list[Any]] | str] = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Build and attach the neighborhood structure to the GeoDataFrame.

        Args:
            strategy:       Libpysal weight class (e.g. ``Queen``, ``Rook``).
            neighbors_dict: Precomputed ``{id: [neighbor_ids]}`` mapping or a
                            path to a JSON file with the same structure.
            *args:          Extra positional arguments forwarded to the strategy.
            **kwargs:       Extra keyword arguments forwarded to the strategy.
        """
        self.gdf = attach_neighbors(
            gdf=self.gdf,
            strategy=strategy,
            neighbors_dict=neighbors_dict,
            *args,
            **kwargs,
        )
        self._neighborhood_created = True
        self._neighs_cache = self.gdf["_neighs"].to_dict()

    def neighs_id(self, idx: Any) -> list[Any]:
        """
        Return the list of neighbor indices for cell ``idx``.

        Args:
            idx: Index of the cell in the GeoDataFrame.

        Returns:
            List of neighbor indices.
        """
        if self._neighs_cache:
            return self._neighs_cache.get(idx, [])
        return self.gdf.loc[idx, "_neighs"]

    def neighs(self, idx: Any) -> gpd.GeoDataFrame:
        """
        Return the neighboring cells of ``idx`` as a GeoDataFrame.

        Args:
            idx: Index of the cell in the GeoDataFrame.

        Returns:
            GeoDataFrame containing the neighboring rows.

        Raises:
            RuntimeError: If the neighborhood has not been created yet.
            ValueError:   If the '_neighs' column is missing.
        """
        if not self._neighborhood_created:
            raise RuntimeError(
                "Neighborhood has not been created yet. Call `.create_neighborhood()` first."
            )
        if "_neighs" not in self.gdf.columns:
            raise ValueError("Column '_neighs' is not present in the GeoDataFrame.")

        return self.gdf.loc[self.neighs_id(idx)]

    def neighbor_values(self, idx: Any, col: str) -> np.ndarray:
        """
        Return the values of ``col`` for all neighbors of cell ``idx``.

        Faster than ``neighs(idx)[col]`` because it skips geometry overhead.

        Args:
            idx: Index of the cell in the GeoDataFrame.
            col: Column name to retrieve.

        Returns:
            Numpy array of neighbor values.
        """
        return self.gdf.loc[self.neighs_id(idx), col].values

    def rule(self, idx: Any) -> Any:
        """
        Transition rule applied to each cell. Must be overridden in subclasses.

        Args:
            idx: Index of the cell being evaluated.

        Returns:
            New state value for the cell.

        Raises:
            NotImplementedError: If not overridden by the subclass.
        """
        raise NotImplementedError("Subclasses must implement the transition rule.")

    def execute(self) -> None:
        """
        Execute one simulation step by applying :meth:`rule` to every cell.

        Raises:
            RuntimeError: If the neighborhood has not been created yet.

        Note:
            Because :meth:`rule` is an arbitrary Python function, the update
            cannot be vectorized automatically. Performance-critical subclasses
            should avoid repeated ``self.neighs(idx)`` calls inside ``rule``
            and prefer :meth:`neighbor_values` instead, which skips geometry
            overhead.
        """
        if not self._neighborhood_created:
            raise RuntimeError(
                "Neighborhood must be created before running the model. "
                "Call `.create_neighborhood()` first."
            )
        self.gdf[self.state_attr] = self.gdf.index.map(self.rule)
