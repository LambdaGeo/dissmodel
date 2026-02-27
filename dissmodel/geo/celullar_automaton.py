from __future__ import annotations

import math
from typing import Any, Optional, Type

import numpy as np
import geopandas as gpd
from libpysal.weights import Queen, W

from dissmodel.core import Model
from dissmodel.geo import attach_neighbors


from dissmodel.geo.neighborhood import StrategyType

from abc import ABC, abstractmethod


class CellularAutomaton(Model, ABC):
    """
    Base class for spatial cellular automata backed by a GeoDataFrame.

    Extends :class:`~dissmodel.core.Model` with neighborhood management and
    a cell-by-cell transition rule loop.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        GeoDataFrame with geometries and a state attribute.
    state_attr : str, optional
        Column name representing the cell state, by default ``"state"``.
    step : float, optional
        Time increment per execution step, by default 1.
    start_time : float, optional
        Simulation start time, by default 0.
    end_time : float, optional
        Simulation end time, by default ``math.inf``.
    name : str, optional
        Optional model name, by default ``""``.
    dim : tuple of int, optional
        Grid dimensions as ``(n_cols, n_rows)``, by default ``None``.
    **kwargs :
        Extra keyword arguments forwarded to :class:`~dissmodel.core.Model`.

    Examples
    --------
    >>> class MyCA(CellularAutomaton):
    ...     def rule(self, idx):
    ...         return self.gdf.loc[idx, self.state_attr]
    """

    def __init__(
        self,
        gdf: gpd.GeoDataFrame,
        state_attr: str = "state",
        step: float = 1,
        start_time: float = 0,
        end_time: float = math.inf,
        name: str = "",
        dim: Optional[int] = None,
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
            **kwargs,
        )

    def initialize(self) -> None:
        """
        Set up the initial model state.

        Override in subclasses to define the starting conditions.
        """
        pass

    def create_neighborhood(
        self,
        strategy: StrategyType = Queen,
        neighbors_dict: Optional[dict[Any, list[Any]] | str] = None,
        **kwargs: Any,
    ) -> None:
        """
        Build and attach the neighborhood structure to the GeoDataFrame.

        Parameters
        ----------
        strategy : type, optional
            Libpysal weight class (e.g. ``Queen``, ``Rook``),
            by default ``Queen``.
        neighbors_dict : dict or str, optional
            Precomputed ``{id: [neighbor_ids]}`` mapping or a path to a JSON
            file with the same structure. If provided, ``strategy`` is ignored.
        **kwargs :
            Extra keyword arguments forwarded to the strategy.
        """
        self.gdf = attach_neighbors(
            gdf=self.gdf,
            strategy=strategy,
            neighbors_dict=neighbors_dict,
            **kwargs,
        )
        self._neighborhood_created = True
        self._neighs_cache = self.gdf["_neighs"].to_dict()

    def neighs_id(self, idx: Any) -> list[Any]:
        """
        Return the neighbor indices for cell ``idx``.

        Parameters
        ----------
        idx : any
            Index of the cell in the GeoDataFrame.

        Returns
        -------
        list
            List of neighbor indices.
        """
        if self._neighs_cache:
            return self._neighs_cache.get(idx, [])
        return self.gdf.loc[idx, "_neighs"]

    def neighs(self, idx: Any) -> gpd.GeoDataFrame:
        """
        Return the neighboring cells of ``idx`` as a GeoDataFrame.

        Parameters
        ----------
        idx : any
            Index of the cell in the GeoDataFrame.

        Returns
        -------
        geopandas.GeoDataFrame
            GeoDataFrame containing the neighboring rows.

        Raises
        ------
        RuntimeError
            If the neighborhood has not been created yet.
        ValueError
            If the ``_neighs`` column is missing from the GeoDataFrame.

        Notes
        -----
        Returns a GeoDataFrame slice, which involves Pandas overhead.
        For performance-critical rule evaluation inside simulation loops,
        prefer :meth:`neighbor_values` which returns a NumPy array directly.
 
        """
        if not self._neighborhood_created:
            raise RuntimeError(
                "Neighborhood has not been created yet. "
                "Call `.create_neighborhood()` first."
            )
        if "_neighs" not in self.gdf.columns:
            raise ValueError("Column '_neighs' is not present in the GeoDataFrame.")

        return self.gdf.loc[self.neighs_id(idx)]

    def neighbor_values(self, idx: Any, col: str) -> np.ndarray:
        """
        Return the values of ``col`` for all neighbors of cell ``idx``.

        Faster than ``neighs(idx)[col]`` because it skips geometry overhead.

        Parameters
        ----------
        idx : any
            Index of the cell in the GeoDataFrame.
        col : str
            Column name to retrieve.

        Returns
        -------
        numpy.ndarray
            Array of neighbor values.
        """
        return self.gdf.loc[self.neighs_id(idx), col].values
    
    @abstractmethod
    def rule(self, idx: Any) -> Any:
        """
        Transition rule applied to each cell.

        Must be overridden in subclasses to define the state transition logic.

        Parameters
        ----------
        idx : any
            Index of the cell being evaluated.

        Returns
        -------
        any
            New state value for the cell.

        Raises
        ------
        NotImplementedError
            If not overridden by the subclass.
        """
        raise NotImplementedError("Subclasses must implement the transition rule.")

    def execute(self) -> None:
        """
        Execute one simulation step by applying :meth:`rule` to every cell.

        Raises
        ------
        RuntimeError
            If the neighborhood has not been created yet.

        Notes
        -----
        Because :meth:`rule` is an arbitrary Python function, the update
        cannot be vectorized automatically. Performance-critical subclasses
        should prefer :meth:`neighbor_values` over :meth:`neighs` inside
        ``rule`` to avoid geometry overhead on every lookup.
        """
        if not self._neighborhood_created:
            raise RuntimeError(
                "Neighborhood must be created before running the model. "
                "Call `.create_neighborhood()` first."
            )
        self.gdf[self.state_attr] = self.gdf.index.map(self.rule)
