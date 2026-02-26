from __future__ import annotations

import random
from typing import Any

from libpysal.weights import Queen

from dissmodel.geo import FillStrategy, fill
from dissmodel.geo.celullar_automaton import CellularAutomaton


# ---------------------------------------------------------------------------
# Built-in patterns
# ---------------------------------------------------------------------------

#: Classic Game of Life patterns organized by category.
#: Can be imported and used independently of :class:`GameOfLife`.
PATTERNS: dict[str, list[list[int]]] = {
    # --- Oscillators ---
    "blinker": [                        # period 2
        [1, 1, 1],
    ],
    "toad": [                           # period 2
        [0, 1, 1, 1],
        [1, 1, 1, 0],
    ],
    "beacon": [                         # period 2
        [1, 1, 0, 0],
        [1, 1, 0, 0],
        [0, 0, 1, 1],
        [0, 0, 1, 1],
    ],
    "pulsar": [                         # period 3 — requires grid >= 15x15
        [0,0,1,1,1,0,0,0,1,1,1,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,0],
        [1,0,0,0,0,1,0,1,0,0,0,0,1],
        [1,0,0,0,0,1,0,1,0,0,0,0,1],
        [1,0,0,0,0,1,0,1,0,0,0,0,1],
        [0,0,1,1,1,0,0,0,1,1,1,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,1,1,1,0,0,0,1,1,1,0,0],
        [1,0,0,0,0,1,0,1,0,0,0,0,1],
        [1,0,0,0,0,1,0,1,0,0,0,0,1],
        [1,0,0,0,0,1,0,1,0,0,0,0,1],
        [0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,1,1,1,0,0,0,1,1,1,0,0],
    ],
    # --- Spaceships ---
    "glider": [                         # moves diagonally
        [0, 1, 0],
        [0, 0, 1],
        [1, 1, 1],
    ],
    "lwss": [                           # lightweight spaceship
        [0, 1, 0, 0, 1],
        [1, 0, 0, 0, 0],
        [1, 0, 0, 0, 1],
        [1, 1, 1, 1, 0],
    ],
    # --- Still lifes ---
    "block": [                          # never changes
        [1, 1],
        [1, 1],
    ],
    "beehive": [                        # never changes
        [0, 1, 1, 0],
        [1, 0, 0, 1],
        [0, 1, 1, 0],
    ],
    "loaf": [                           # never changes
        [0, 1, 1, 0],
        [1, 0, 0, 1],
        [0, 1, 0, 1],
        [0, 0, 1, 0],
    ],
}


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------

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
            Pattern names to place. If ``None``, all patterns in
            :data:`PATTERNS` are used. Available keys: ``"blinker"``,
            ``"toad"``, ``"beacon"``, ``"pulsar"``, ``"glider"``,
            ``"lwss"``, ``"block"``, ``"beehive"``, ``"loaf"``.

        Notes
        -----
        Assumes a square grid. The ``"pulsar"`` pattern requires a grid
        of at least 15x15 to avoid out-of-range placement.
        """
        selected = (
            {k: PATTERNS[k] for k in patterns if k in PATTERNS}
            if patterns
            else PATTERNS
        )

        grid_dim = int(len(self.gdf) ** 0.5)

        for pattern in selected.values():
            start_x = random.randint(0, grid_dim - len(pattern[0]))   # col _ offset bounded by n_cols
            start_y = random.randint(0, grid_dim - len(pattern))     # row offset bounded by n_rows

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


__all__ = ["GameOfLife", "PATTERNS"]