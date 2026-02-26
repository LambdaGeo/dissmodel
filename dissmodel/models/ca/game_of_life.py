from __future__ import annotations

import random
from typing import Any

from libpysal.weights import Queen

from dissmodel.geo import FillStrategy, fill
from dissmodel.geo.celullar_automaton import CellularAutomaton


class GameOfLife(CellularAutomaton):
    """
    Spatial cellular automaton implementation of Conway's Game of Life.

    Cells live or die based on the number of live neighbors according to
    the following rules:

    - A live cell with fewer than 2 or more than 3 live neighbors dies.
    - A live cell with 2 or 3 live neighbors survives.
    - A dead cell with exactly 3 live neighbors becomes alive.

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
    >>> gdf = regular_grid(dimension=(5, 5), resolution=1, attrs={"state": 0})
    >>> env = Environment(end_time=3)
    >>> gol = GameOfLife(gdf=gdf)
    >>> gol.initialize()
    """

    def setup(self) -> None:
        """Build the Queen neighborhood for the grid."""
        self.create_neighborhood(strategy=Queen, use_index=True)

    def initialize(self) -> None:
        """
        Fill the grid with a random initial state.

        Uses a 60/40 live/dead split with a fixed seed for reproducibility.
        Override this method to define a custom initial state.
        """
        fill(
            strategy=FillStrategy.RANDOM_SAMPLE,
            gdf=self.gdf,
            attr="state",
            data={1: 0.6, 0: 0.4},
            seed=42,
        )

    def initialize_patterns(
        self,
        patterns: list[str] | None = None,
    ) -> None:
        """
        Place classic Game of Life patterns at random positions on the grid.

        Parameters
        ----------
        patterns : list of str, optional
            Pattern names to place. If ``None``, all available patterns are
            used. Available patterns: ``"glider"``, ``"toad"``,
            ``"blinker"``.

        Notes
        -----
        Assumes a square grid. Patterns are placed at random positions
        bounded to avoid out-of-range indices.
        """
        available: dict[str, list[list[int]]] = {
            "glider": [
                [0, 1, 0],
                [0, 0, 1],
                [1, 1, 1],
            ],
            "toad": [
                [0, 1, 1, 1],
                [1, 1, 1, 0],
            ],
            "blinker": [
                [1, 1, 1],
            ],
        }

        selected = (
            {k: available[k] for k in patterns if k in available}
            if patterns
            else available
        )

        grid_dim = int(len(self.gdf) ** 0.5)

        for pattern in selected.values():
            start_x = random.randint(0, grid_dim - len(pattern))
            start_y = random.randint(0, grid_dim - len(pattern[0]))
            fill(
                strategy=FillStrategy.PATTERN,
                gdf=self.gdf,
                attr="state",
                pattern=pattern,
                start_x=start_x,
                start_y=start_y,
            )

    def rule(self, idx: Any) -> int:
        """
        Apply the Game of Life transition rule to cell ``idx``.

        Parameters
        ----------
        idx : any
            Index of the cell being evaluated.

        Returns
        -------
        int
            ``1`` if the cell is alive after the transition, ``0`` if dead.
        """
        state = self.gdf.loc[idx, self.state_attr]
        live_neighbors = self.neighs(idx)[self.state_attr].fillna(0).sum()

        if state == 1:
            return 1 if 2 <= live_neighbors <= 3 else 0
        return 1 if live_neighbors == 3 else 0
