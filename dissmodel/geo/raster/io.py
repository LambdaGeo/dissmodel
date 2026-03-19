"""
dissmodel/geo/raster/io.py
===========================
I/O utilities for RasterBackend — load from vector files and GeoTIFFs,
save back to GeoTIFF.

Public API
----------
shapefile_to_raster_backend(path, resolution, attrs, ...)
    Rasterize a vector file (Shapefile, GeoJSON, GPKG, …) into a
    RasterBackend. Each attribute column becomes a named array.

load_geotiff(path, band_spec)
    Read a GeoTIFF (plain or zipped) into a RasterBackend.

save_geotiff(backend, path, band_spec, crs, transform)
    Write selected RasterBackend arrays to a multi-band GeoTIFF.

save_raster_backend(backend, path, bands, crs, transform)
    Convenience wrapper — writes all (or selected) arrays without
    requiring a band_spec.

Notes
-----
All functions are domain-agnostic: no land-use classes, no CRS
assumptions, no project-specific constants.
"""
from __future__ import annotations

import pathlib
import zipfile
from typing import Any

import numpy as np

from dissmodel.geo.raster.backend import RasterBackend

try:
    import rasterio
    import rasterio.features
    import rasterio.transform
    HAS_RASTERIO = True
except ImportError:
    HAS_RASTERIO = False

try:
    import geopandas as gpd
    HAS_GEOPANDAS = True
except ImportError:
    HAS_GEOPANDAS = False


# ── vector → RasterBackend ────────────────────────────────────────────────────

def shapefile_to_raster_backend(
    path: str | pathlib.Path,
    resolution: float,
    attrs: list[str] | dict[str, Any],
    crs: str | int | None = None,
    all_touched: bool = False,
    nodata: int | float = 0,
    nodata_value: int | float | None = None,
    add_mask: bool = True,
) -> RasterBackend:
    """
    Load a vector file and rasterize attribute columns into a RasterBackend.

    Reads any format supported by GeoPandas (Shapefile, GeoJSON, GPKG, …),
    optionally reprojects to ``crs``, derives the grid shape from the bounding
    box and ``resolution``, and rasterizes each requested attribute column
    with ``rasterio.features.rasterize``.

    Cells not covered by any geometry receive the ``nodata`` fill value.
    When ``add_mask=True`` (default), a ``"mask"`` band is added to the
    backend — ``1`` where a cell is covered by at least one geometry, ``0``
    elsewhere. Models use this band to skip cells outside the study area.

    Parameters
    ----------
    path : str or Path
        Vector file path. Accepts Shapefile, GeoJSON, GeoPackage, or a
        ``.zip`` archive containing any of these formats.
    resolution : float
        Cell size in the units of the CRS (metres for metric CRS).
    attrs : list[str] or dict[str, Any]
        Columns to rasterize.

        - ``list[str]``  — rasterize each column with ``nodata`` as fill.
        - ``dict[str, Any]`` — keys are column names, values are per-column
          fill defaults for cells outside the geometries.
    crs : str, int, or None
        Target CRS for reprojection before rasterization (e.g. ``"EPSG:31984"``).
        If ``None``, the file's native CRS is used.
    all_touched : bool
        If ``True``, burn all cells touched by a geometry.
        If ``False`` (default), burn only cells whose centre falls inside.
    nodata : int or float
        Default fill value for cells outside geometries. Default: ``0``.
    nodata_value : int or float or None
        When provided, cells outside geometries are set to this sentinel
        value instead of ``nodata``. Useful to distinguish "outside extent"
        from "valid zero" (e.g. ``nodata_value=-1`` for proportion arrays
        where ``0.0`` is a legitimate value). Default: ``None``.
    add_mask : bool
        If ``True`` (default), adds a ``"mask"`` band (``float32``, values
        ``0.0`` / ``1.0``) marking valid cells.

    Returns
    -------
    RasterBackend
        Backend with one array per requested attribute, plus an optional
        ``"mask"`` band. Shape is ``(rows, cols)`` derived from the bounding
        box and ``resolution``.

    Raises
    ------
    ImportError
        If ``geopandas`` or ``rasterio`` are not installed.
    FileNotFoundError
        If ``path`` does not exist.
    ValueError
        If ``attrs`` is empty or a requested column is not in the file.

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
    >>> b.get("mask").sum()
    94704
    """
    if not HAS_RASTERIO:
        raise ImportError("rasterio is required — pip install rasterio")
    if not HAS_GEOPANDAS:
        raise ImportError("geopandas is required — pip install geopandas")

    path = pathlib.Path(path) if not str(path).startswith("zip://") else path
    if isinstance(path, pathlib.Path) and not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    # ── load and optionally reproject ─────────────────────────────────────────
    gdf = gpd.read_file(str(path))
    if crs is not None:
        gdf = gdf.to_crs(crs)

    # ── resolve attrs → {column: fill_default} ────────────────────────────────
    if isinstance(attrs, list):
        attr_defaults: dict[str, Any] = {col: nodata for col in attrs}
    else:
        attr_defaults = dict(attrs)

    if not attr_defaults:
        raise ValueError("attrs must not be empty")

    missing = [col for col in attr_defaults if col not in gdf.columns]
    if missing:
        raise ValueError(f"Columns not found in file: {missing}")

    # ── compute grid shape from bounding box ──────────────────────────────────
    xmin, ymin, xmax, ymax = gdf.total_bounds
    n_cols = int(np.ceil((xmax - xmin) / resolution))
    n_rows = int(np.ceil((ymax - ymin) / resolution))

    transform = rasterio.transform.from_bounds(
        xmin, ymin, xmax, ymax, n_cols, n_rows
    )

    backend = RasterBackend(
        shape=(n_rows, n_cols),
        nodata_value=nodata_value,   # stored for nodata_mask property
    )

    # ── rasterize geometry coverage → "mask" band ─────────────────────────────
    valid_geoms = [geom for geom in gdf.geometry if geom is not None]
    coverage = rasterio.features.rasterize(
        shapes=((geom, 1) for geom in valid_geoms),
        out_shape=(n_rows, n_cols),
        transform=transform,
        fill=0,
        all_touched=all_touched,
        dtype=np.uint8,
    )
    mask = coverage.astype(bool)   # True = cell covered by at least one polygon

    if add_mask:
        backend.set("mask", mask.astype(np.float32))

    # ── rasterize each attribute column ───────────────────────────────────────
    for col, default in attr_defaults.items():
        values = gdf[col]

        # preserve integer dtypes when possible
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
            out_shape=(n_rows, n_cols),
            transform=transform,
            fill=float(default),
            all_touched=all_touched,
            dtype=dtype,
        )

        # apply sentinel for out-of-extent cells if requested
        sentinel = nodata_value if nodata_value is not None else default
        arr = np.where(mask, arr, sentinel).astype(dtype)

        backend.set(col, arr)

    n_valid = int(mask.sum())
    n_total = n_rows * n_cols
    print(
        f"  rasterized: {n_valid:,} valid cells"
        f" / {n_total:,} total"
        f" ({100 * n_valid / n_total:.1f}% coverage)"
    )

    return backend


# ── GeoTIFF → RasterBackend ───────────────────────────────────────────────────

def load_geotiff(
    path: str | pathlib.Path,
    band_spec: list[tuple[str, str, float]],
) -> tuple[RasterBackend, dict]:
    """
    Read a GeoTIFF into a RasterBackend.

    Supports plain ``.tif`` files and ``.zip`` archives containing a single
    GeoTIFF. Bands are mapped to named arrays in the backend using
    ``band_spec``.

    Parameters
    ----------
    path : str or Path
        Path to a ``.tif`` or ``.zip`` file.
    band_spec : list of (name, dtype, nodata)
        Mapping from band index (1-based) to array name and dtype.
        Bands whose data equals ``nodata`` everywhere are skipped.

        Example::

            [
                ("uso",  "int8",    -1),
                ("alt",  "float32", -9999.0),
                ("solo", "int8",    -1),
            ]

    Returns
    -------
    (RasterBackend, dict)
        The backend with one array per non-empty band, and a metadata dict
        with keys ``"transform"``, ``"crs"``, and ``"tags"``.

    Raises
    ------
    ImportError
        If ``rasterio`` is not installed.
    """
    if not HAS_RASTERIO:
        raise ImportError("rasterio is required — pip install rasterio")

    path_str = str(path)

    # unwrap zip archives
    if path_str.endswith(".zip"):
        with zipfile.ZipFile(path_str) as z:
            tif_name = next(f for f in z.namelist() if f.endswith(".tif"))
        path_str = f"zip://{path_str}!{tif_name}"

    with rasterio.open(path_str) as ds:
        rows, cols = ds.height, ds.width
        backend = RasterBackend(shape=(rows, cols))

        for i, (name, dtype, nodata) in enumerate(band_spec, start=1):
            if i > ds.count:
                break

            arr = ds.read(i).astype(dtype)

            # skip bands that are entirely nodata (e.g. uninitialised saves)
            if np.all(arr == nodata):
                continue

            backend.arrays[name] = arr

        meta = {
            "transform": ds.transform,
            "crs":       ds.crs,
            "tags":      ds.tags(),
        }

    return backend, meta


# ── RasterBackend → GeoTIFF ───────────────────────────────────────────────────

def save_geotiff(
    backend: RasterBackend,
    path: str | pathlib.Path,
    band_spec: list[tuple[str, str, float]],
    crs: str | None = None,
    transform=None,
    compress: str = "deflate",
) -> None:
    """
    Write selected RasterBackend arrays to a multi-band GeoTIFF.

    Parameters
    ----------
    backend : RasterBackend
        Source backend.
    path : str or Path
        Output file path. Parent directories are created if needed.
    band_spec : list of (name, dtype, nodata)
        Bands to write, in order. Arrays missing from the backend are
        written as constant ``nodata`` fills.

        Example::

            [
                ("uso",  "int8",    -1),
                ("alt",  "float32", -9999.0),
            ]

    crs : str or None
        CRS string for the output file (e.g. ``"EPSG:31984"``).
        If ``None``, the GeoTIFF is written without a CRS.
    transform : Affine or None
        Affine geotransform. If ``None``, a pixel-coordinate identity
        transform is used.
    compress : str
        Compression algorithm. Default: ``"deflate"``.

    Raises
    ------
    ImportError
        If ``rasterio`` is not installed.
    """
    if not HAS_RASTERIO:
        raise ImportError("rasterio is required — pip install rasterio")

    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    rows, cols = backend.shape

    # build arrays — fill missing bands with nodata
    arrays = []
    for name, dtype, nodata in band_spec:
        arr = backend.arrays.get(
            name,
            np.full((rows, cols), nodata, dtype=dtype),
        )
        arrays.append(arr.astype(dtype))

    if transform is None:
        transform = rasterio.transform.from_bounds(0, 0, cols, rows, cols, rows)

    with rasterio.open(
        path, "w",
        driver   = "GTiff",
        height   = rows,
        width    = cols,
        count    = len(arrays),
        dtype    = str(arrays[0].dtype),
        crs      = crs,
        transform= transform,
        compress = compress,
    ) as dst:
        for i, (arr, (name, _, _)) in enumerate(zip(arrays, band_spec), start=1):
            dst.write(arr, i)
            dst.update_tags(i, name=name)


def save_raster_backend(
    backend: RasterBackend,
    path: str | pathlib.Path,
    bands: list[str] | None = None,
    crs: str | int | None = None,
    transform=None,
) -> None:
    """
    Convenience wrapper: write all (or selected) arrays to a GeoTIFF
    without requiring a band_spec.

    dtype and nodata are inferred from each array. Use ``save_geotiff``
    when you need explicit dtype control or nodata sentinels.

    Parameters
    ----------
    backend : RasterBackend
    path : str or Path
    bands : list[str] or None
        Arrays to write. If ``None``, all arrays in the backend are written
        in insertion order.
    crs : str, int, or None
    transform : Affine or None

    Raises
    ------
    ImportError
        If ``rasterio`` is not installed.
    """
    if not HAS_RASTERIO:
        raise ImportError("rasterio is required — pip install rasterio")

    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    bands = bands or list(backend.arrays.keys())
    rows, cols = backend.shape

    arrays = [backend.get(b) for b in bands]
    dtype  = arrays[0].dtype

    if transform is None:
        transform = rasterio.transform.from_bounds(0, 0, cols, rows, cols, rows)

    with rasterio.open(
        path, "w",
        driver   = "GTiff",
        height   = rows,
        width    = cols,
        count    = len(arrays),
        dtype    = dtype,
        crs      = crs,
        transform= transform,
    ) as dst:
        for i, (name, arr) in enumerate(zip(bands, arrays), start=1):
            dst.write(arr.astype(dtype), i)
            dst.update_tags(i, name=name)
