from __future__ import annotations

import io

import geopandas as gpd

from dissmodel.io._utils import resolve_uri, sha256_bytes


def load_gdf(
    uri:          str,
    minio_client = None,
    **kwargs,
) -> tuple[gpd.GeoDataFrame, str]:
    """
    Load a GeoDataFrame from any URI.

    Supports: local path, s3://, http(s)://.
    Returns (gdf, sha256_checksum).
    """
    content, checksum = resolve_uri(uri, minio_client)
    gdf = gpd.read_file(io.BytesIO(content), **kwargs)
    return gdf, checksum


def save_gdf(
    gdf:          gpd.GeoDataFrame,
    uri:          str,
    minio_client = None,
    layer:        str = "result",
    **kwargs,
) -> str:
    """
    Save a GeoDataFrame as GeoPackage to any URI.

    Supports: local path, s3://.
    Returns sha256 checksum of the saved file.
    """
    buffer = io.BytesIO()
    gdf.to_file(buffer, driver="GPKG", layer=layer, **kwargs)
    buffer.seek(0)
    content = buffer.getvalue()

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
            content_type = "application/geopackage+sqlite3",
        )
    else:
        with open(uri, "wb") as f:
            f.write(content)

    return sha256_bytes(content)
