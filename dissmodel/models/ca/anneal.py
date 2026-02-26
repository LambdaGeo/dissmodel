from __future__ import annotations

import random
from enum import IntEnum
from typing import Any

from libpysal.weights import Queen

from dissmodel.geo import CellularAutomaton


class AnnealState(IntEnum):
    """
    Possible states for a cell in :class:`Anneal`.

    Attributes
    ----------
    L : int
        Left state (0).
    R : int
        Right state (1).
    """
    L = 0
    R = 1


class Anneal(CellularAutomaton):
    """
    Cellular automaton implementing the Anneal rule.

    The Anneal rule is a majority-vote variant that produces smooth,
    blob-like regions. Each cell's next state depends on the count of
    neighbors (including itself) in state ``L``:

    - count ≤ 3  → ``R``
    - count == 4 → ``L``
    - count == 5 → ``R``
    - count ≥ 6  → ``L``

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
    >>> env = Environment(end_time=10)
    >>> ca = Anneal(gdf=gdf)
    >>> ca.initialize()
    """

    def setup(self) -> None:
        """Build the Queen neighborhood for the grid."""
        self.create_neighborhood(strategy=Queen, use_index=True)

    def initialize(self) -> None:
        """
        Fill the grid with a random initial state.

        Each cell is assigned ``L`` or ``R`` with equal probability.
        """
        self.gdf["state"] = [
            random.choice([AnnealState.L, AnnealState.R])
            for _ in range(len(self.gdf))
        ]

    def rule(self, idx: Any) -> int:
        """
        Apply the Anneal transition rule to cell ``idx``.

        Counts the number of cells in state ``L`` among the cell's
        neighbors plus the cell itself, then applies the threshold rule.

        Parameters
        ----------
        idx : any
            Index of the cell being evaluated.

        Returns
        -------
        int
            New state for the cell (``L`` or ``R``).
        """
        state = self.gdf.loc[idx, self.state_attr]

        # Count neighbors in state L, including the cell itself
        count = (self.neighbor_values(idx, self.state_attr) == AnnealState.L).sum()
        if state == AnnealState.L:
            count += 1

        if count <= 3:
            return AnnealState.R
        if count == 4:
            return AnnealState.L
        if count == 5:
            return AnnealState.R
        return AnnealState.L  # count >= 6


__all__ = ["Anneal", "AnnealState"]
