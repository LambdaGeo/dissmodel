from __future__ import annotations

import hashlib
import pathlib


VECTOR_EXTENSIONS  = {".shp", ".gpkg", ".geojson", ".json", ".zip"}
RASTER_EXTENSIONS  = {".tif", ".tiff"}
XARRAY_EXTENSIONS  = {".zarr", ".nc", ".nc4"}


def detect_format(uri: str) -> str:
    """
    Infer dataset format from URI extension.
    Raises ValueError if extension is not recognized.
    """
    path = uri.split("?")[0]   # strip query string
    ext  = pathlib.Path(path).suffix.lower()

    if ext in VECTOR_EXTENSIONS:  return "vector"
    if ext in RASTER_EXTENSIONS:  return "raster"
    if ext in XARRAY_EXTENSIONS:  return "xarray"

    raise ValueError(
        f"Cannot detect format from extension '{ext}' in URI: {uri}\n"
        f"Supported: "
        f"vector {sorted(VECTOR_EXTENSIONS)}, "
        f"raster {sorted(RASTER_EXTENSIONS)}, "
        f"xarray {sorted(XARRAY_EXTENSIONS)}"
    )


def sha256_bytes(data: bytes) -> str:
    """Return sha256 hex digest of bytes."""
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str) -> str:
    """Return sha256 hex digest of a local file using chunked reads."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def resolve_uri(uri: str, minio_client=None) -> tuple[bytes, str]:
    """
    Fetch raw bytes from any URI.
    Returns (content_bytes, sha256_checksum).

    Supported schemes:
        s3://bucket/key     — MinIO / S3
        http(s)://...       — HTTP download
        /local/path         — local file
    """
    if uri.startswith("s3://"):
        if minio_client is None:
            from dissmodel.io._storage import get_default_client
            minio_client = get_default_client()
        bucket, key = uri[5:].split("/", 1)
        obj         = minio_client.get_object(bucket, key)
        content     = obj.read()
        return content, sha256_bytes(content)

    if uri.startswith("http://") or uri.startswith("https://"):
        import urllib.request
        with urllib.request.urlopen(uri) as r:
            content = r.read()
        return content, sha256_bytes(content)

    # Local path
    with open(uri, "rb") as f:
        content = f.read()
    return content, sha256_bytes(content)
