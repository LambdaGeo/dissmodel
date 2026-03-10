"""
dissmodel/examples/game_of_life_raster.py
==========================================
Raster version of Conway's Game of Life using RasterCellularAutomaton.

Symmetric counterpart of the vector GameOfLife (GeoDataFrame + CellularAutomaton).
Same rules, fully vectorized — rule() operates on the full NumPy grid in a
single call instead of cell-by-cell.

Rules (Conway 1970)
-------------------
- Any live cell with 2 or 3 live neighbors survives.
- Any dead cell with exactly 3 live neighbors becomes alive.
- All other cells die or remain dead.

Comparison
----------
    # vector — rule called once per cell per step
    class GameOfLife(CellularAutomaton):
        def rule(self, idx):
            state     = self.gdf.loc[idx, self.state_attr]
            neighbors = (self.neighbor_values(idx, "state") == 1).sum()
            if state == 1: return 1 if neighbors in (2, 3) else 0
            else:          return 1 if neighbors == 3 else 0

    # raster — rule called once per step, covers all cells
    class GameOfLife(RasterCellularAutomaton):
        def rule(self, arrays):
            state     = arrays["state"]
            neighbors = self.backend.focal_sum_mask(state == 1)
            survive   = (state == 1) & np.isin(neighbors, [2, 3])
            born      = (state == 0) & (neighbors == 3)
            return {"state": np.where(survive | born, 1, 0).astype(np.int8)}

Usage
-----
    from dissmodel.core import Environment
    from dissmodel.geo.raster_grid import make_raster_grid
    from dissmodel.examples.game_of_life_raster import GameOfLife
    import numpy as np

    rng = np.random.default_rng(42)
    b   = make_raster_grid(50, 50, attrs={"state": rng.integers(0, 2, (50, 50))})

    env = Environment(start_time=1, end_time=100)
    GameOfLife(backend=b)
    env.run()
"""
from __future__ import annotations

import numpy as np

from dissmodel.geo.raster.backend import RasterBackend
from dissmodel.geo.raster.regular_grid import make_raster_grid
from dissmodel.geo.raster.cellular_automaton import RasterCellularAutomaton


class GameOfLife(RasterCellularAutomaton):
    """
    Raster cellular automaton implementing Conway's Game of Life.

    Symmetric counterpart of the vector GameOfLife — same rules,
    Moore neighborhood (8 directions), fully vectorized.

    Parameters
    ----------
    backend : RasterBackend
        Shared backend. Must contain a ``"state"`` array (or the name
        set via ``state_attr``) with values 0 (dead) or 1 (alive).
    density : float, optional
        Proportion of cells initially alive, by default 0.3.
        Only used if ``initialize()`` is called.
    seed : int, optional
        Random seed for initialization, by default 42.
    state_attr : str, optional
        Name of the state array in the backend, by default ``"state"``.

    Examples
    --------
    >>> from dissmodel.core import Environment
    >>> from dissmodel.geo.raster_grid import make_raster_grid
    >>> import numpy as np
    >>> rng = np.random.default_rng(0)
    >>> b = make_raster_grid(20, 20, attrs={"state": rng.integers(0, 2, (20, 20))})
    >>> env = Environment(start_time=1, end_time=10)
    >>> GameOfLife(backend=b)
    """

    def setup(
        self,
        backend:    RasterBackend,
        density:    float = 0.3,
        seed:       int   = 42,
        state_attr: str   = "state",
    ) -> None:
        super().setup(backend, state_attr=state_attr)
        self.density = density
        self.seed    = seed

    def initialize(self) -> None:
        """
        Fill the grid with a random initial state.

        Uses :attr:`density` to determine the proportion of live cells.
        Only needed when the backend array is not already initialized.
        """
        rng   = np.random.default_rng(self.seed)
        state = (rng.random(self.shape) < self.density).astype(np.int8)
        self.backend.set(self.state_attr, state)

    def rule(self, arrays: dict) -> dict:
        """
        Vectorized Conway transition rule.

        Applied once per step over the entire grid using Moore neighborhood
        (8 directions — all 8 neighbors counted via focal_sum_mask).

        Parameters
        ----------
        arrays : dict[str, np.ndarray]
            Snapshot of backend arrays (past state).

        Returns
        -------
        dict[str, np.ndarray]
            Updated ``"state"`` array (0 = dead, 1 = alive).
        """
        state     = arrays[self.state_attr]
        neighbors = self.backend.focal_sum_mask(state == 1)

        survive   = (state == 1) & np.isin(neighbors, [2, 3])
        born      = (state == 0) & (neighbors == 3)

        return {self.state_attr: np.where(survive | born, 1, 0).astype(np.int8)}
