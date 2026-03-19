"""
dissmodel/geo/raster/io.py
===========================
Utilities for loading external spatial data into RasterBackend.

Functions
---------
shapefile_to_raster_backend(path, resolution, attrs, crs, all_touched, nodata)
    Load a shapefile (or any vector format) and rasterize one or more
    attribute columns into a RasterBackend.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import geopandas as gpd
import rasterio
import rasterio.features
import rasterio.transform

from dissmodel.geo.raster.backend import RasterBackend


def shapefile_to_raster_backend(
    path: str | Path,
    resolution: float,
    attrs: list[str] | dict[str, Any],
    crs: str | int | None = None,
    all_touched: bool = False,
    nodata: int | float = 0,
) -> RasterBackend:
    """
    Load a vector file and rasterize attribute columns into a RasterBackend.

    Reads any format supported by GeoPandas (Shapefile, GeoJSON, GPKG, …),
    reprojects to ``crs`` if provided, computes the grid dimensions from the
    bounding box and ``resolution``, and rasterizes each requested attribute
    column using ``rasterio.features.rasterize``.

    Parameters
    ----------
    path : str or Path
        Path to the vector file (Shapefile, GeoJSON, GeoPackage, …).
    resolution : float
        Cell size in the units of the coordinate reference system.
        For metric CRS (e.g. EPSG:31984) this is metres.
    attrs : list[str] or dict[str, Any]
        Column names to rasterize.

        - ``list[str]`` — rasterize each column using its own values.
        - ``dict[str, Any]`` — keys are column names, values are fill defaults
          used when a cell is not covered by any geometry.
    crs : str, int, or None
        Target CRS for reprojection before rasterization.
        If ``None``, the file's native CRS is used.
    all_touched : bool
        If ``True``, all cells touched by a geometry are burned.
        If ``False`` (default), only cells whose centre falls inside are burned.
    nodata : int or float
        Fill value for cells not covered by any geometry. Default: ``0``.

    Returns
    -------
    RasterBackend
        Backend with one array per requested attribute, shape ``(rows, cols)``.

    Raises
    ------
    ValueError
        If ``attrs`` is empty or a requested column is not in the GeoDataFrame.
    FileNotFoundError
        If ``path`` does not exist.

    Examples
    --------
    >>> b = shapefile_to_raster_backend(
    ...     path       = "data/mangue_grid.shp",
    ...     resolution = 100,
    ...     attrs      = ["uso", "alt", "solo"],
    ...     crs        = "EPSG:31984",
    ... )
    >>> b.shape
    (947, 1003)
    >>> b.get("uso").dtype
    dtype('int32')
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    # ── load and reproject ────────────────────────────────────────────────────
    gdf = gpd.read_file(path)
    if crs is not None:
        gdf = gdf.to_crs(crs)

    # ── resolve attrs ─────────────────────────────────────────────────────────
    if isinstance(attrs, list):
        attr_defaults: dict[str, Any] = {col: nodata for col in attrs}
    else:
        attr_defaults = dict(attrs)

    missing = [col for col in attr_defaults if col not in gdf.columns]
    if missing:
        raise ValueError(f"Columns not found in file: {missing}")

    # ── compute grid dimensions ───────────────────────────────────────────────
    xmin, ymin, xmax, ymax = gdf.total_bounds
    cols = int(np.ceil((xmax - xmin) / resolution))
    rows = int(np.ceil((ymax - ymin) / resolution))

    transform = rasterio.transform.from_bounds(
        xmin, ymin, xmax, ymax, cols, rows
    )

    backend = RasterBackend(shape=(rows, cols))

    # ── rasterize each attribute ──────────────────────────────────────────────
    for col, default in attr_defaults.items():
        values = gdf[col]

        # choose dtype from the column
        if np.issubdtype(values.dtype, np.integer):
            dtype = np.int32
        else:
            dtype = np.float32

        arr = rasterio.features.rasterize(
            shapes=(
                (geom, float(val))
                for geom, val in zip(gdf.geometry, values)
                if geom is not None
            ),
            out_shape=(rows, cols),
            transform=transform,
            fill=default,
            all_touched=all_touched,
            dtype=dtype,
        )

        backend.set(col, arr)

    return backend


def save_raster_backend(
    backend: RasterBackend,
    path: str | Path,
    bands: list[str] | None = None,
    crs: str | int | None = None,
    transform: rasterio.transform.Affine | None = None,
) -> None:
    """
    Save one or more RasterBackend arrays to a multi-band GeoTIFF.

    Parameters
    ----------
    backend : RasterBackend
        Source backend.
    path : str or Path
        Output file path (e.g. ``"output/result.tif"``).
    bands : list[str] or None
        Array names to write. If ``None``, all arrays are written.
    crs : str, int, or None
        CRS for the output file. If ``None``, the GeoTIFF has no CRS.
    transform : Affine or None
        Geotransform for the output file. If ``None``, an identity transform
        is used (pixel coordinates only).

    Examples
    --------
    >>> save_raster_backend(b, "result.tif", bands=["uso", "alt"],
    ...                     crs="EPSG:31984", transform=t)
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    bands = bands or list(backend.arrays.keys())
    rows, cols = backend.shape

    arrays = [backend.get(b) for b in bands]
    dtype  = arrays[0].dtype

    if transform is None:
        transform = rasterio.transform.from_bounds(0, 0, cols, rows, cols, rows)

    with rasterio.open(
        path, "w",
        driver="GTiff",
        height=rows, width=cols,
        count=len(bands),
        dtype=dtype,
        crs=crs,
        transform=transform,
    ) as dst:
        for i, (name, arr) in enumerate(zip(bands, arrays), start=1):
            dst.write(arr.astype(dtype), i)
            dst.update_tags(i, name=name)
