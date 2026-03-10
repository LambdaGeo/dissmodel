"""
dissmodel.geo.raster_io
=======================

Generic GeoTIFF read/write utilities for RasterBackend.

No domain knowledge is included here.

The meaning of bands is defined by band_spec.

band_spec
---------
list of tuples:

    (name, dtype, nodata)

example:
    [
        ("landuse", "int8", -1),
        ("elevation", "float32", -9999),
    ]
"""

from __future__ import annotations

import pathlib
import numpy as np

from dissmodel.geo.raster_backend import RasterBackend

try:
    import rasterio
    HAS_RASTERIO = True
except ImportError:
    HAS_RASTERIO = False


def load_geotiff(
    path: str | pathlib.Path,
    band_spec: list[tuple[str, str, float]],
) -> tuple[RasterBackend, dict]:

    if not HAS_RASTERIO:
        raise ImportError("rasterio is required")

    with rasterio.open(path) as ds:

        rows, cols = ds.height, ds.width
        backend = RasterBackend((rows, cols))

        for i, (name, dtype, nodata) in enumerate(band_spec, start=1):

            if i > ds.count:
                break

            arr = ds.read(i).astype(dtype)

            if np.all(arr == nodata):
                continue

            backend.arrays[name] = arr

        meta = dict(
            transform=ds.transform,
            crs=ds.crs,
            tags=ds.tags(),
        )

    return backend, meta


def save_geotiff(
    backend: RasterBackend,
    path: str | pathlib.Path,
    band_spec: list[tuple[str, str, float]],
    crs: str,
    transform,
    compress: str = "deflate",
):

    if not HAS_RASTERIO:
        raise ImportError("rasterio is required")

    rows, cols = backend.shape

    arrays = []

    for name, dtype, nodata in band_spec:

        arr = backend.arrays.get(
            name,
            np.full((rows, cols), nodata, dtype=dtype)
        )

        arrays.append(arr.astype(dtype))

    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=rows,
        width=cols,
        count=len(arrays),
        dtype=str(arrays[0].dtype),
        crs=crs,
        transform=transform,
        compress=compress,
    ) as dst:

        for i, arr in enumerate(arrays, start=1):
            dst.write(arr, i)