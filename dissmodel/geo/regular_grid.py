from __future__ import annotations

import numpy as np
import geopandas as gpd
from shapely.geometry import box
from typing import Any, Optional

# Reusable type aliases
Bounds = tuple[float, float, float, float]  # (xmin, ymin, xmax, ymax)
Dimension = tuple[int, int]                 # (n_cols, n_rows)


def parse_idx(idx: str) -> tuple[int, int]:
    """
    Extract x and y from an index string in ``'y-x'`` format.

    Parameters
    ----------
    idx : str
        Index string in ``'y-x'`` format, e.g. ``'0-0'``, ``'3-4'``.

    Returns
    -------
    tuple of int
        ``(x, y)`` as integers.

    Examples
    --------
    >>> parse_idx('3-4')
    (4, 3)
    >>> parse_idx('0-0')
    (0, 0)
    """
    y_str, x_str = idx.split("-")
    return int(x_str), int(y_str)


def regular_grid(
    gdf: Optional[gpd.GeoDataFrame] = None,
    bounds: Optional[Bounds] = None,
    resolution: Optional[float] = None,
    dimension: Optional[Dimension] = None,
    attrs: Optional[dict[str, Any]] = None,
    crs: Optional[str | int] = None,
) -> gpd.GeoDataFrame:
    """
    Create a regular grid of fixed-size cells.

    Exactly one of the following input combinations must be provided:

    - ``dimension`` + ``resolution`` — abstract grid with no geographic location
    - ``bounds`` + ``resolution`` — grid fitted to a bounding box by cell size
    - ``bounds`` + ``dimension`` — grid fitted to a bounding box by cell count
    - ``gdf`` — bounds are extracted from the GeoDataFrame

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame, optional
        GeoDataFrame used to extract the bounding box.
    bounds : tuple of float, optional
        Bounding box as ``(xmin, ymin, xmax, ymax)``.
    resolution : float, optional
        Cell size in coordinate units.
    dimension : tuple of int, optional
        Grid shape as ``(n_cols, n_rows)``.
    attrs : dict, optional
        Extra attributes added to every cell, e.g. ``{'state': 0}``.
    crs : str or int, optional
        Coordinate reference system. If ``None``, the grid is abstract
        (no geographic location).

    Returns
    -------
    geopandas.GeoDataFrame
        Regular grid where each row is a cell with a Polygon geometry,
        indexed by ``'id'`` in ``'row-col'`` format.

    Raises
    ------
    ValueError
        If the input combination is insufficient to define the grid.

    Examples
    --------
    >>> gdf = regular_grid(dimension=(3, 3), resolution=1.0)
    >>> len(gdf)
    9
    >>> gdf.index[0]
    '0-0'
    """
    attrs = attrs or {}

    resolution_x: float
    resolution_y: float
    n_cols: int
    n_rows: int
    xmin: float
    ymin: float
    xmax: float
    ymax: float

    if dimension is not None and resolution is not None and bounds is None and gdf is None:
        n_cols, n_rows = dimension
        xmin, ymin = 0.0, 0.0
        resolution_x = resolution_y = resolution
        xmax = xmin + n_cols * resolution_x
        ymax = ymin + n_rows * resolution_y

    elif bounds is not None:
        xmin, ymin, xmax, ymax = bounds
        width = xmax - xmin
        height = ymax - ymin

        if resolution is not None:
            resolution_x = resolution_y = resolution
            n_cols = int(np.ceil(width / resolution_x))
            n_rows = int(np.ceil(height / resolution_y))
        elif dimension is not None:
            n_cols, n_rows = dimension
            resolution_x = width / n_cols
            resolution_y = height / n_rows
        else:
            raise ValueError("Provide either `resolution` or `dimension`.")

    elif gdf is not None:
        return regular_grid(
            bounds=tuple(gdf.total_bounds),  # type: ignore[arg-type]
            resolution=resolution,
            dimension=dimension,
            attrs=attrs,
            crs=gdf.crs,
        )

    else:
        raise ValueError("Provide `gdf`, `bounds`, or `dimension` with `resolution`.")

    x_edges: np.ndarray = np.arange(xmin, xmax, resolution_x)
    y_edges: np.ndarray = np.arange(ymin, ymax, resolution_y)

    grid_cells = []
    ids = []
    for i, x0 in enumerate(x_edges):
        for j, y0 in enumerate(y_edges):
            grid_cells.append(box(x0, y0, x0 + resolution_x, y0 + resolution_y))
            ids.append(f"{j}-{i}")

    data: dict[str, Any] = {"geometry": grid_cells, "id": ids}
    for key, value in attrs.items():
        data[key] = [value] * len(grid_cells)

    return gpd.GeoDataFrame(data, crs=crs).set_index("id")
