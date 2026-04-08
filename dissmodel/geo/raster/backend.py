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
    nodata_value : float | int | None
        Sentinel value used to mark cells outside the study extent.
        When provided, ``nodata_mask`` derives the extent mask automatically,
        so ``RasterMap`` renders those cells as transparent without any extra
        configuration. Default: ``None``.

    Examples
    --------
    >>> b = RasterBackend(shape=(10, 10))
    >>> b.set("state", np.zeros((10, 10), dtype=np.int8))
    >>> b.get("state").shape
    (10, 10)

    >>> b = RasterBackend(shape=(10, 10), nodata_value=-1)
    >>> b.nodata_mask   # True = valid cell, False = outside extent
    """

    def __init__(
        self,
        shape: tuple[int, int],
        nodata_value: float | int | None = None,
        transform: Any = None,
        crs: Any = None,
    ) -> None:
        self.shape        = shape
        self.arrays: dict[str, np.ndarray] = {}
        self.nodata_value = nodata_value   # sentinel for out-of-extent cells

        self.transform    = transform
        self.crs          = crs

    # ── extent mask ───────────────────────────────────────────────────────────

    @property
    def nodata_mask(self) -> np.ndarray | None:
        """
        Boolean mask: ``True`` = valid cell, ``False`` = outside extent / nodata.

        Derived in priority order:
        1. ``arrays["mask"]``  — explicit mask band (dissluc / coastal convention:
                                 non-zero = valid).
        2. ``nodata_value``    — applied over the first available array.
        3. ``None``            — no information; ``RasterMap`` skips auto-masking.

        Used by ``RasterMap`` (``auto_mask=True``) to render out-of-extent pixels
        as transparent without any per-project configuration.
        """
        if "mask" in self.arrays:
            return self.arrays["mask"] != 0

        if self.nodata_value is not None and self.arrays:
            first = next(iter(self.arrays.values()))
            return first != self.nodata_value

        return None

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

        Parameters
        ----------
        arr : np.ndarray
        dr : int
            Row offset (positive = down, negative = up).
        dc : int
            Column offset (positive = right, negative = left).

        Returns
        -------
        np.ndarray
            Shifted array of the same shape as ``arr``.
        """
        rows, cols = arr.shape
        out = np.zeros_like(arr)
        rs  = slice(max(0, -dr), min(rows, rows - dr))
        rd  = slice(max(0,  dr), min(rows, rows + dr))
        cs_ = slice(max(0, -dc), min(cols, cols - dc))
        cd  = slice(max(0,  dc), min(cols, cols + dc))
        out[rd, cd] = arr[rs, cs_]
        return out

    def band_names(self) -> list[str]:
        """Return the names of all arrays currently stored in the backend."""
        return list(self.arrays.keys())

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
        neighborhood : list[tuple[int, int]] | None
            ``None`` uses Moore neighbourhood via ``binary_dilation``.

        Returns
        -------
        np.ndarray
            Boolean array.
        """
        if neighborhood is None:
            return binary_dilation(condition.astype(bool), structure=np.ones((3, 3)))
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

        Parameters
        ----------
        name : str
        neighborhood : list[tuple[int, int]]
            Default: ``DIRS_MOORE``.

        Returns
        -------
        np.ndarray
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
        neighborhood : list[tuple[int, int]]
            Default: ``DIRS_MOORE``.

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
