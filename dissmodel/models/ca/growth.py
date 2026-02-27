from __future__ import annotations

import random
from enum import IntEnum
from typing import Any

from libpysal.weights import Queen

from dissmodel.geo import CellularAutomaton


class GrowthState(IntEnum):
    """
    Possible states for a cell in :class:`Growth`.

    Attributes
    ----------
    EMPTY : int
        Empty cell, not yet colonized.
    ALIVE : int
        Live cell, can spread to neighbors.
    """
    EMPTY = 0
    ALIVE = 1


class Growth(CellularAutomaton):
    """
    Stochastic cellular automaton simulating spatial growth from a seed.

    A single live cell is placed at the center of the grid at initialization.
    At each step, empty cells adjacent to at least one live cell become alive
    with probability :attr:`probability`.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        GeoDataFrame with geometries and a ``state`` attribute.
        Must be created with ``dim=(n, n)`` so the center cell can be
        located by index.
    **kwargs :
        Extra keyword arguments forwarded to
        :class:`~dissmodel.geo.CellularAutomaton`.

    Examples
    --------
    >>> from dissmodel.geo import regular_grid
    >>> from dissmodel.core import Environment
    >>> gdf = regular_grid(dimension=(20, 20), resolution=1, attrs={"state": 0})
    >>> env = Environment(end_time=15)
    >>> growth = Growth(gdf=gdf, dim=20)
    >>> growth.initialize()
    """

    #: Probability of an empty cell becoming alive if it has at least one live neighbor.
    probability: float

    def setup(self, probability: float = 0.15) -> None:
        """
        Configure the model and build the neighborhood.

        Parameters
        ----------
        probability : float, optional
            Probability of colonization per step for empty cells adjacent
            to at least one live cell, by default 0.15.
        """
        self.probability = probability
        self.create_neighborhood(strategy=Queen, use_index=True)

    def initialize(self) -> None:
        """
        Place a single live cell at the center of the grid.

        All other cells start as empty.
        """
        assert self.dim is not None, "dim must be set — pass dim=N when instantiating"
        center = self.dim // 2
        center_idx = f"{center}-{center}"
        self.gdf.loc[:, "state"] = GrowthState.EMPTY
        self.gdf.loc[center_idx, "state"] = GrowthState.ALIVE

    def rule(self, idx: Any) -> int:
        """
        Apply the stochastic growth rule to cell ``idx``.

        Parameters
        ----------
        idx : any
            Index of the cell being evaluated.

        Returns
        -------
        int
            New state for the cell:

            - ``ALIVE`` if already alive (cells never die).
            - ``ALIVE`` with probability :attr:`probability` if empty
              and has at least one live neighbor.
            - ``EMPTY`` otherwise.
        """
        assert self.dim is not None, "dim must be set — pass dim=N when instantiating"
        state = self.gdf.loc[idx, self.state_attr]

        if state == GrowthState.ALIVE:
            return GrowthState.ALIVE

        
        alive_neighbors = (self.neighbor_values(idx, self.state_attr) == GrowthState.ALIVE).sum()


        if alive_neighbors > 0 and random.random() < self.probability:
            return GrowthState.ALIVE

        return GrowthState.EMPTY


__all__ = ["Growth", "GrowthState"]
