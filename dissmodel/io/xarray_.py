from __future__ import annotations

# Planned for BDC/STAC/WCPMS integration (post-MVP).
#
# Design notes for future implementation:
# - Dimensions follow Pangeo conventions: time, y, x
# - CRS: SIRGAS-2000 (EPSG:4674) for BDC compatibility
# - Storage: Zarr chunks on MinIO, compatible with xarray.open_zarr()
# - DataSource.type = "bdc_stac" | "wcpms" when loaded from BDC
#
# Example future usage:
#   ds, checksum = load_xarray("s3://bucket/data.zarr")
#   checksum     = save_xarray(ds, "s3://bucket/output.zarr")


def load_xarray(uri: str, minio_client=None, **kwargs):
    """
    Load an Xarray Dataset from any URI.
    Planned for post-MVP BDC/STAC integration.
    """
    raise NotImplementedError(
        "Xarray backend is planned for post-MVP BDC/STAC integration.\n"
        "Use vector or raster formats for now."
    )


def save_xarray(data, uri: str, minio_client=None, **kwargs) -> str:
    """
    Save an Xarray Dataset to any URI.
    Planned for post-MVP BDC/STAC integration.
    """
    raise NotImplementedError(
        "Xarray backend is planned for post-MVP BDC/STAC integration.\n"
        "Use vector or raster formats for now."
    )
