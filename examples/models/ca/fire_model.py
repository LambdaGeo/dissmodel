from __future__ import annotations

from enum import IntEnum
from typing import Any

from libpysal.weights import Rook

from dissmodel.geo import CellularAutomaton, FillStrategy, fill


class FireState(IntEnum):
    """
    Possible states for a cell in :class:`FireModel`.

    Attributes
    ----------
    FOREST : int
        Healthy tree, can catch fire.
    BURNING : int
        Actively burning, spreads fire to neighbors.
    BURNED : int
        Already burned, no longer spreads.
    """
    FOREST  = 0
    BURNING = 1
    BURNED  = 2


class FireModel(CellularAutomaton):
    """
    Spatial cellular automaton simulating forest fire spread.

    The fire spreads to any forest cell that has at least one burning
    neighbor (Rook neighborhood — 4 cardinal directions).

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        GeoDataFrame with geometries and a ``state`` attribute.
    **kwargs :
        Extra keyword arguments forwarded to
        :class:`~dissmodel.geo.CellularAutomaton`.

    Examples
    --------
    >>> from dissmodel.geo import vector_grid
    >>> from dissmodel.core import Environment
    >>> gdf = vector_grid(dimension=(10, 10), resolution=1, attrs={"state": 0})
    >>> env = Environment(end_time=10)
    >>> fire = FireModel(gdf=gdf)
    >>> fire.initialize()
    """

    #: Proportion of cells initially on fire (0.0 – 1.0).
    initial_fire_density: float

    def setup(
        self,
        initial_fire_density: float = 0.05,
        seed: int = 42,
    ) -> None:
        """
        Configure the model and build the neighborhood.

        Parameters
        ----------
        initial_fire_density : float, optional
            Proportion of cells that start as burning, by default 0.05.
            Must be between 0.0 and 1.0.
        seed : int, optional
            Random seed used during initialization, by default 42.
        """
        self.initial_fire_density = initial_fire_density
        self.seed = seed
        self.create_neighborhood(strategy=Rook, use_index=True)

    def initialize(self) -> None:
        """
        Fill the grid with a random initial state.

        Uses :attr:`initial_fire_density` to determine the proportion of
        cells that start as burning. The remaining cells start as forest.
        """
        fill(
            strategy=FillStrategy.RANDOM_SAMPLE,
            gdf=self.gdf,
            attr="state",
            data={
                FireState.FOREST:  1 - self.initial_fire_density,
                FireState.BURNING: self.initial_fire_density,
            },
            seed=self.seed,
        )

    def rule(self, idx: Any) -> int:
        """
        Apply the fire spread transition rule to cell ``idx``.

        Parameters
        ----------
        idx : any
            Index of the cell being evaluated.

        Returns
        -------
        int
            New state for the cell:

            - ``BURNED`` if the cell is currently burning.
            - ``BURNING`` if the cell is forest and has at least one
              burning neighbor.
            - Unchanged otherwise.
        """
        state = self.gdf.loc[idx, self.state_attr]

        if state == FireState.BURNING:
            return FireState.BURNED

        if state == FireState.FOREST:
            if (self.neighbor_values(idx, self.state_attr) == FireState.BURNING).any():
                return FireState.BURNING

        return state


__all__ = ["FireModel", "FireState"]