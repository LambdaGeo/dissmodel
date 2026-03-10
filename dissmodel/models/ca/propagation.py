from __future__ import annotations

from enum import IntEnum
from typing import Any

import numpy as np
from libpysal.weights import KNN

from dissmodel.geo import CellularAutomaton, FillStrategy, fill


class PropagationState(IntEnum):
    """
    Possible states for a cell in :class:`Propagation`.

    Attributes
    ----------
    OFF : int
        Inactive cell, can be activated by neighbors.
    ON : int
        Active cell, spreads to neighbors.
    """
    OFF = 0
    ON  = 1


class Propagation(CellularAutomaton):
    """
    Stochastic spatial propagation cellular automaton.

    Active cells (``ON``) spread to inactive neighbors with probability
    :attr:`prob`. Once a cell becomes active, it stays active permanently.
    The neighborhood is based on K-nearest neighbors (KNN, k=4).

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        GeoDataFrame with geometries and a ``state`` attribute.
    **kwargs :
        Extra keyword arguments forwarded to
        :class:`~dissmodel.geo.CellularAutomaton`.

    Examples
    --------
    >>> from dissmodel.geo import regular_grid
    >>> from dissmodel.core import Environment
    >>> gdf = regular_grid(dimension=(20, 20), resolution=1, attrs={"state": 0})
    >>> env = Environment(end_time=15)
    >>> prop = Propagation(gdf=gdf)
    >>> prop.initialize()
    """

    #: Probability of an inactive cell becoming active per step
    #: if it has at least one active neighbor.
    prob: float

    #: Initial proportion of active cells (0.0 – 1.0).
    initial_density: float

    def setup(
        self,
        prob: float = 0.1,
        initial_density: float = 0.4,
    ) -> None:
        """
        Configure the model and build the neighborhood.

        Parameters
        ----------
        prob : float, optional
            Probability of activation per step for inactive cells adjacent
            to at least one active cell, by default 0.1.
        initial_density : float, optional
            Initial proportion of active cells, by default 0.4.
        """
        self.prob = prob
        self.initial_density = initial_density
        self.create_neighborhood(strategy=KNN, k=4, use_index=True)

    def initialize(self) -> None:
        """
        Fill the grid with a random initial state.

        Uses :attr:`initial_density` to determine the proportion of
        cells that start as active. The remaining cells start as inactive.
        """
        fill(
            strategy=FillStrategy.RANDOM_SAMPLE,
            gdf=self.gdf,
            attr="state",
            data={
                PropagationState.OFF: 1 - self.initial_density,
                PropagationState.ON:  self.initial_density,
            },
            seed=42,
        )

    def rule(self, idx: Any) -> int:
        """
        Apply the stochastic propagation rule to cell ``idx``.

        Parameters
        ----------
        idx : any
            Index of the cell being evaluated.

        Returns
        -------
        int
            New state for the cell:

            - ``ON`` if already active (cells never deactivate).
            - ``ON`` with probability :attr:`prob` if inactive and has
              at least one active neighbor.
            - ``OFF`` otherwise.
        """
        state = self.gdf.loc[idx, self.state_attr]

        if state == PropagationState.ON:
            return PropagationState.ON

        has_active_neighbor = (
            self.neighbor_values(idx, self.state_attr) == PropagationState.ON
        ).any()

        if has_active_neighbor and np.random.rand() < self.prob:
            return PropagationState.ON

        return PropagationState.OFF


__all__ = ["Propagation", "PropagationState"]
