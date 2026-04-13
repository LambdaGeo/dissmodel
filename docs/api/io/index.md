# IO

The `dissmodel.io` module provides a unified dataset abstraction for loading
and saving geospatial data. Format detection is automatic — the correct
backend (vector, raster, or Xarray) is selected based on the file extension
or an explicit `fmt` argument.

For cloud deployments, `s3://` URIs are resolved transparently via the
configured MinIO/S3 client — no changes to model code are required.

---

## `load_dataset`

```python
from dissmodel.io import load_dataset

# Vector — returns (GeoDataFrame, checksum)
gdf, checksum = load_dataset("data/grid.gpkg")
gdf, checksum = load_dataset("data/grid.zip")
gdf, checksum = load_dataset("s3://bucket/grid.gpkg")

# Raster — returns ((RasterBackend, meta), checksum)
(backend, meta), checksum = load_dataset("data/output.tif", fmt="raster")

# Explicit format
gdf, checksum = load_dataset("data/grid.zip", fmt="vector")
```

The returned `checksum` is the SHA-256 of the raw file bytes. Inside an
executor's `load()`, assign it to `record.source.checksum`:

```python
def load(self, record: ExperimentRecord):
    gdf, checksum = load_dataset(record.source.uri)
    record.source.checksum = checksum
    return gdf
```

---

## `save_dataset`

```python
from dissmodel.io import save_dataset

# Vector
checksum = save_dataset(gdf, "results/output.gpkg")
checksum = save_dataset(gdf, "s3://bucket/output.gpkg")

# Raster
checksum = save_dataset((backend, meta), "results/output.tif")
```

Returns the SHA-256 of the saved file. Inside an executor's `save()`,
assign it to `record.output_sha256`:

```python
def save(self, result, record: ExperimentRecord) -> ExperimentRecord:
    uri = record.output_path or "output.gpkg"
    checksum = save_dataset(result, uri)
    record.output_path   = uri
    record.output_sha256 = checksum
    record.status        = "completed"
    return record
```

---

## Format dispatch

| Extension | `fmt` | Backend | Returns |
|-----------|-------|---------|---------|
| `.gpkg`, `.shp`, `.geojson` | `"vector"` | GeoPandas | `(GeoDataFrame, checksum)` |
| `.zip` (containing shapefile) | `"vector"` | GeoPandas | `(GeoDataFrame, checksum)` |
| `.tif`, `.tiff` | `"raster"` | rasterio + RasterBackend | `((backend, meta), checksum)` |
| `.zip` (containing GeoTIFF) | `"raster"` | rasterio + RasterBackend | `((backend, meta), checksum)` |
| `"auto"` (default) | auto-detect | — | depends on extension |

---

## `vector_to_raster_backend`

Rasterizes a GeoDataFrame into a `RasterBackend`. Used inside executor
`load()` methods when the model requires a raster substrate but the input
is a vector file.

```python
from dissmodel.io.convert import vector_to_raster_backend

backend = vector_to_raster_backend(
    source      = gdf,
    resolution  = 100.0,      # metres
    attrs       = {"uso": 0, "alt": 0.0, "solo": 1},
    crs         = "EPSG:31984",
    nodata      = 0,
)
```

The resulting backend includes a `"mask"` band marking valid cells
(non-nodata).

---

## API Reference

::: dissmodel.io._dispatch.load_dataset

::: dissmodel.io._dispatch.save_dataset

::: dissmodel.io.convert.vector_to_raster_backend
