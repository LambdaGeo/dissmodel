from __future__ import annotations

import random
from enum import IntEnum
from typing import Any

from dissmodel.geo import CellularAutomaton, parse_idx


class SnowState(IntEnum):
    """
    Possible states for a cell in :class:`Snow`.

    Attributes
    ----------
    EMPTY : int
        Empty cell, no snow.
    SNOW : int
        Cell occupied by snow.
    """
    EMPTY = 0
    SNOW  = 1


class Snow(CellularAutomaton):
    """
    Cellular automaton simulating snowfall and accumulation.

    Snow falls from the top row and moves downward one cell per step.
    When a snowflake reaches the bottom or lands on top of another
    snowflake, it accumulates. New snowflakes appear at the top row
    with probability :attr:`probability`.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        GeoDataFrame with geometries and a ``state`` attribute.
        Must be created with ``dim=(n, n)`` so row/column indices
        are available via :func:`~dissmodel.geo.parse_idx`.
    **kwargs :
        Extra keyword arguments forwarded to
        :class:`~dissmodel.geo.CellularAutomaton`.

    Notes
    -----
    This model does not use a spatial neighborhood strategy — cell
    relationships are computed directly from the grid index format
    ``'row-col'`` via :func:`~dissmodel.geo.parse_idx`.
    Therefore, :meth:`execute` is overridden to skip the neighborhood
    check that the base class enforces.

    The number of simulation steps must be greater than the grid size
    for snow to have enough time to fall and accumulate. Snow stops
    falling ``dim`` steps before ``end_time`` to allow flakes already
    in motion to reach the ground.

    A good rule of thumb: ``end_time > 2 * dim``.

    Examples
    --------
    >>> from dissmodel.geo import vector_grid
    >>> from dissmodel.core import Environment
    >>> gdf = vector_grid(dimension=(20, 20), resolution=1, attrs={"state": 0})
    >>> env = Environment(end_time=50)  # steps must be greater than grid_size
    >>> snow = Snow(gdf=gdf, dim=20)
    """

    #: Probability of a new snowflake appearing at the top row each step.
    probability: float

    def setup(self, probability: float = 0.02) -> None:
        """
        Configure the model.

        Parameters
        ----------
        probability : float, optional
            Probability of a new snowflake appearing at the top row
            each step, by default 0.02.

        Notes
        -----
        For visible accumulation, use ``end_time > 2 * dim`` when
        creating the :class:`~dissmodel.core.Environment`.
        """
        self.probability = probability

    def execute(self) -> None:
        """
        Execute one simulation step by applying :meth:`rule` to every cell.

        Overrides the base class implementation to skip the neighborhood
        check — this model computes cell relationships directly from
        grid indices via :func:`~dissmodel.geo.parse_idx`.
        """
        self.gdf[self.state_attr] = self.gdf.index.map(self.rule)

    def rule(self, idx: Any) -> int:
        """
        Apply the snow fall and accumulation rule to cell ``idx``.

        Parameters
        ----------
        idx : any
            Index of the cell being evaluated.

        Returns
        -------
        int
            New state for the cell:

            - Top row → ``SNOW`` with probability :attr:`probability`
              if empty and within the active snowfall window.
            - Snowy cell at bottom row → stays ``SNOW`` (accumulates).
            - Snowy cell with empty cell below → becomes ``EMPTY``
              (snow moves down).
            - Snowy cell with occupied cell below → stays ``SNOW``
              (accumulates).
            - Empty cell with snowy cell above → becomes ``SNOW``
              (snow arrives).
            - Otherwise → ``EMPTY``.

        Notes
        -----
        Snow stops falling ``dim`` steps before ``end_time`` to allow
        flakes already in motion to reach the ground before the
        simulation ends.
        """
        assert self.dim is not None, "dim must be set — pass dim=N when instantiating"
        
        cell = self.gdf.loc[idx]
        x, y = parse_idx(idx)
        t = self.env.now()

        # Top row — snowflakes appear here
        if y == self.dim - 1:
            if (
                cell.state == SnowState.EMPTY
                and t < (self.end_time - self.dim)
                and random.random() < self.probability
            ):
                return SnowState.SNOW
            return SnowState.EMPTY

        # Snow movement — check cell below
        below_idx = f"{y - 1}-{x}" if y - 1 >= 0 else None

        if cell.state == SnowState.SNOW:
            if y == 0:
                return SnowState.SNOW  # bottom row — accumulates
            if below_idx:
                below_state = self.gdf.loc[below_idx, "state"]
                if below_state == SnowState.EMPTY:
                    return SnowState.EMPTY  # snow moves down
                return SnowState.SNOW      # blocked — accumulates

        # Snow arrival — check cell above
        above_idx = f"{y + 1}-{x}" if y + 1 < self.dim else None
        if above_idx and self.gdf.loc[above_idx, "state"] == SnowState.SNOW:
            return SnowState.SNOW

        return SnowState.EMPTY


__all__ = ["Snow", "SnowState"]
