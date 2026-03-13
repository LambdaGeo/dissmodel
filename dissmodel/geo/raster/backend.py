"""
dissmodel/geo/raster/backend.py
================================
Vectorized engine for cellular automata on raster grids (NumPy 2D arrays).

Responsibility
--------------
Provide generic spatial operations (shift, dilate, focal_sum, snapshot)
with no domain knowledge — no land-use classes, no CRS, no I/O, no
project-specific constants.

Domain models (FloodRasterModel, MangroveRasterModel, …) import
RasterBackend and operate on named arrays stored in ``self.arrays``.

Minimal example
---------------
    from dissmodel.geo.raster.backend import RasterBackend, DIRS_MOORE

    b = RasterBackend(shape=(100, 100))
    b.set("state", np.zeros((100, 100), dtype=np.int8))

    state    = b.get("state").copy()          # equivalent to cell.past[attr]
    contact  = b.neighbor_contact(state == 1)
    for dr, dc in DIRS_MOORE:
        neighbour = RasterBackend.shift2d(state, dr, dc)
        ...
    b.arrays["state"] = new_state
"""
from __future__ import annotations

import numpy as np
from scipy.ndimage import binary_dilation


# Moore neighbourhood (8 directions) — framework constant, not domain-specific.
# Models import from here; projects do not need to redefine it.
DIRS_MOORE: list[tuple[int, int]] = [
    (-1, -1), (-1, 0), (-1, 1),
    ( 0, -1),          ( 0, 1),
    ( 1, -1), ( 1, 0), ( 1, 1),
]

# Von Neumann neighbourhood (4 directions) — available for models that require it.
DIRS_VON_NEUMANN: list[tuple[int, int]] = [
    (-1, 0), (0, -1), (0, 1), (1, 0),
]


class RasterBackend:
    """
    Storage and vectorized operations for 2D raster grids.

    Replaces TerraME's ``forEachCell`` / ``forEachNeighbor`` with pure NumPy
    operations. The backend is shared across multiple models running in the
    same ``Environment`` — each model reads and writes named arrays every step.

    Arrays
    ------
    Stored in ``self.arrays`` as ``np.ndarray`` of shape ``(rows, cols)``.
    No names are reserved — domain models define their own
    (``"uso"``, ``"alt"``, ``"solo"``, ``"state"``, ``"temperature"``, …).

    Parameters
    ----------
    shape : tuple[int, int]
        Grid shape as ``(rows, cols)``.

    Examples
    --------
    >>> b = RasterBackend(shape=(10, 10))
    >>> b.set("state", np.zeros((10, 10), dtype=np.int8))
    >>> b.get("state").shape
    (10, 10)
    """

    def __init__(self, shape: tuple[int, int]) -> None:
        self.shape  = shape              # (rows, cols)
        self.arrays: dict[str, np.ndarray] = {}

    # ── read / write ──────────────────────────────────────────────────────────

    def set(self, name: str, array: np.ndarray) -> None:
        """Store a copy of ``array`` under ``name``."""
        self.arrays[name] = np.asarray(array).copy()

    def get(self, name: str) -> np.ndarray:
        """
        Return a direct reference to the named array.

        Use ``.copy()`` to obtain a snapshot equivalent to TerraME's ``.past``.

        Raises
        ------
        KeyError
            If ``name`` is not in ``self.arrays``.
        """
        return self.arrays[name]

    def snapshot(self) -> dict[str, np.ndarray]:
        """
        Return a deep copy of all arrays — equivalent to TerraME's ``.past`` mechanism.

        Typical usage::

            past     = backend.snapshot()
            uso_past = past["uso"]   # state at the beginning of the step

        Returns
        -------
        dict[str, np.ndarray]
            Dictionary mapping array names to independent copies.
        """
        return {k: v.copy() for k, v in self.arrays.items()}

    # ── spatial operations ────────────────────────────────────────────────────

    @staticmethod
    def shift2d(arr: np.ndarray, dr: int, dc: int) -> np.ndarray:
        """
        Shift ``arr`` by ``(dr, dc)`` rows/columns without wrap-around.
        Edges are filled with zero.

        Equivalent to reading the neighbour in direction ``(dr, dc)`` for every
        cell simultaneously — replaces ``forEachNeighbor`` with a vectorized
        operation.

        Parameters
        ----------
        arr : np.ndarray
            2D source array.
        dr : int
            Row offset (positive = down, negative = up).
        dc : int
            Column offset (positive = right, negative = left).

        Returns
        -------
        np.ndarray
            Shifted array of the same shape as ``arr``.

        Examples
        --------
        >>> shift2d(alt, -1, 0)   # altitude of the northern neighbour of each cell
        >>> shift2d(alt,  1, 1)   # altitude of the south-eastern neighbour
        """
        rows, cols = arr.shape
        out = np.zeros_like(arr)
        rs  = slice(max(0, -dr), min(rows, rows - dr))
        rd  = slice(max(0,  dr), min(rows, rows + dr))
        cs_ = slice(max(0, -dc), min(cols, cols - dc))
        cd  = slice(max(0,  dc), min(cols, cols + dc))
        out[rd, cd] = arr[rs, cs_]
        return out

    @staticmethod
    def neighbor_contact(
        condition: np.ndarray,
        neighborhood: list[tuple[int, int]] | None = None,
    ) -> np.ndarray:
        """
        Return a boolean mask where each cell has at least one neighbour
        satisfying ``condition``.

        Parameters
        ----------
        condition : np.ndarray
            Boolean array marking the source cells.
        neighborhood : list[tuple[int, int]] | None
            Directions to check. ``None`` uses Moore neighbourhood via
            ``binary_dilation`` with a 3×3 structuring element (includes the
            cell itself). Pass ``DIRS_VON_NEUMANN`` or a custom list for other
            neighbourhoods.

        Returns
        -------
        np.ndarray
            Boolean array; ``True`` where a cell neighbours at least one
            ``True`` cell in ``condition``.

        Notes
        -----
        Equivalent to ``forEachNeighbor`` checking membership in a set.
        """
        if neighborhood is None:
            return binary_dilation(condition.astype(bool), structure=np.ones((3, 3)))
        # custom neighbourhood via manual shifts
        result = np.zeros_like(condition, dtype=bool)
        for dr, dc in neighborhood:
            result |= RasterBackend.shift2d(condition.astype(np.int8), dr, dc) > 0
        return result

    def focal_sum(
        self,
        name: str,
        neighborhood: list[tuple[int, int]] = DIRS_MOORE,
    ) -> np.ndarray:
        """
        Focal sum: for each cell, sum the values of ``name`` across its neighbours.
        The cell itself is not included.

        Useful for counting neighbours in a given state, computing gradients, etc.

        Parameters
        ----------
        name : str
            Name of the array to aggregate.
        neighborhood : list[tuple[int, int]]
            Directions to include. Default: ``DIRS_MOORE``.

        Returns
        -------
        np.ndarray
            Float array with per-cell neighbour sums.
        """
        arr    = self.arrays[name]
        result = np.zeros_like(arr, dtype=float)
        for dr, dc in neighborhood:
            result += self.shift2d(arr, dr, dc)
        return result

    def focal_sum_mask(
        self,
        mask: np.ndarray,
        neighborhood: list[tuple[int, int]] = DIRS_MOORE,
    ) -> np.ndarray:
        """
        Count neighbours where ``mask`` is ``True``.

        Parameters
        ----------
        mask : np.ndarray
            Boolean array marking the cells to count.
        neighborhood : list[tuple[int, int]]
            Directions to include. Default: ``DIRS_MOORE``.

        Returns
        -------
        np.ndarray
            Integer array with per-cell neighbour counts.
        """
        result = np.zeros(self.shape, dtype=int)
        m = mask.astype(np.int8)
        for dr, dc in neighborhood:
            result += self.shift2d(m, dr, dc)
        return result

    # ── utilities ─────────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        bands = ", ".join(
            f"{k}:{v.dtype}[{v.shape}]" for k, v in self.arrays.items()
        )
        return f"RasterBackend(shape={self.shape}, arrays=[{bands}])"