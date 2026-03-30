from __future__ import annotations

import io
import os
import shutil
import tempfile

from dissmodel.io._utils import resolve_uri, sha256_bytes


def load_geotiff(
    uri:          str,
    minio_client = None,
    band_spec    = None,
    **kwargs,
) -> tuple[tuple, str]:
    """
    Load a GeoTIFF into a RasterBackend from any URI.

    Downloads to a temporary file if URI is remote.
    Returns ((backend, meta), sha256_checksum).
    """
    from dissmodel.geo.raster.io import load_geotiff as _load

    content, checksum = resolve_uri(uri, minio_client)

    with tempfile.NamedTemporaryFile(suffix=".tif", delete=False) as f:
        f.write(content)
        tmp = f.name

    try:
        backend, meta = _load(tmp, band_spec=band_spec, **kwargs)
    finally:
        os.unlink(tmp)

    return (backend, meta), checksum


def save_geotiff(
    data,
    uri:          str,
    minio_client = None,
    band_spec    = None,
    crs          = None,
    transform    = None,
    **kwargs,
) -> str:
    """
    Save a RasterBackend as GeoTIFF to any URI.

    Supports: local path, s3://.
    Returns sha256 checksum of the saved file.
    """
    from dissmodel.geo.raster.io import save_geotiff as _save

    backend, meta = data

    with tempfile.NamedTemporaryFile(suffix=".tif", delete=False) as f:
        tmp = f.name

    try:
        _save(
            backend,
            tmp,
            band_spec = band_spec,
            crs       = crs or meta.get("crs"),
            transform = transform or meta.get("transform"),
            **kwargs,
        )

        with open(tmp, "rb") as f:
            content = f.read()

        if uri.startswith("s3://"):
            if minio_client is None:
                from dissmodel.io._storage import get_default_client
                minio_client = get_default_client()
            bucket, key = uri[5:].split("/", 1)
            minio_client.put_object(
                bucket_name  = bucket,
                object_name  = key,
                data         = io.BytesIO(content),
                length       = len(content),
                content_type = "image/tiff",
            )
        else:
            shutil.copy(tmp, uri)

    finally:
        os.unlink(tmp)

    return sha256_bytes(content)
