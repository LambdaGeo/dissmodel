# Loading Shapefiles into the Raster Substrate

DisSModel can load any vector file (Shapefile, GeoJSON, GeoPackage) and
convert it directly into a `RasterBackend`, making it possible to run
high-performance raster models on real geographic data without any
intermediate GIS steps.

## How it works

```
Shapefile → GeoDataFrame → rasterize → NumPy arrays → RasterBackend → raster model
```

The rasterization step (powered by `rasterio.features.rasterize`) is fast
and happens once — after that, the model runs entirely in NumPy at full
vectorized speed.

!!! note "Grid regularity"
    This workflow is most accurate when the input shapefile already contains
    a **regular grid** of equal-area polygons (e.g. 100×100m cells), which is
    the typical output of spatial homogenization tools. For irregular polygons
    (municipalities, watersheds), cell values are burned by centroid or by
    touch — inspect the result before running long simulations.

---

## `shapefile_to_raster_backend`

```python
from dissmodel.geo.raster.io import shapefile_to_raster_backend

b = shapefile_to_raster_backend(
    path       = "data/mangue_grid.shp",
    resolution = 100,               # 100m cells
    attrs      = ["uso", "alt", "solo"],
    crs        = "EPSG:31984",      # reproject if needed
)

print(b.shape)          # (rows, cols) derived from bounding box + resolution
print(b.get("uso").dtype)  # int32
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `path` | `str` or `Path` | Path to the vector file |
| `resolution` | `float` | Cell size in CRS units (metres for metric CRS) |
| `attrs` | `list[str]` or `dict[str, default]` | Columns to rasterize |
| `crs` | `str`, `int`, or `None` | Target CRS — reprojects if needed |
| `all_touched` | `bool` | Burn all touched cells (default: centre only) |
| `nodata` | `int` or `float` | Fill value for uncovered cells (default: `0`) |

To set per-column defaults for uncovered cells, pass a dict:

```python
b = shapefile_to_raster_backend(
    path       = "data/mangue_grid.shp",
    resolution = 100,
    attrs      = {"uso": 5, "alt": 0.0, "solo": 1},
    crs        = "EPSG:31984",
)
```

---

## Full example — flood model from shapefile

```python
from dissmodel.core import Environment
from dissmodel.geo.raster.io import shapefile_to_raster_backend
from dissmodel.visualization.raster_map import RasterMap

# from coastal_dynamics.raster import FloodRasterModel
# (or your own RasterModel subclass)
from myproject.flood import FloodRasterModel

# 1. load shapefile → RasterBackend
b = shapefile_to_raster_backend(
    path       = "data/mangue_grid.shp",
    resolution = 100,
    attrs      = {"uso": 5, "alt": 0.0, "solo": 1},
    crs        = "EPSG:31984",
)

print(f"Grid: {b.shape[0]} rows × {b.shape[1]} cols = {b.shape[0]*b.shape[1]:,} cells")

# 2. run the raster model
env = Environment(start_time=2012, end_time=2100)
FloodRasterModel(backend=b, taxa=0.011)
RasterMap(backend=b, band="uso", title="Land Use")
env.run()
```

---

## Saving results back to GeoTIFF

```python
from dissmodel.geo.raster.io import save_raster_backend

save_raster_backend(
    backend   = b,
    path      = "output/flood_result.tif",
    bands     = ["uso", "alt"],
    crs       = "EPSG:31984",
    transform = transform,   # rasterio Affine from original bounds
)
```

---

## Comparison: vector vs raster workflow from the same shapefile

```python
# ── vector workflow ───────────────────────────────────────────────────────────
import geopandas as gpd
from dissmodel.geo.vector.model import SpatialModel

gdf = gpd.read_file("data/mangue_grid.shp").to_crs("EPSG:31984")
# → GeoDataFrame with real geometries, Queen neighbourhood, ~2 min/step @ 94k cells

# ── raster workflow ───────────────────────────────────────────────────────────
from dissmodel.geo.raster.io import shapefile_to_raster_backend

b = shapefile_to_raster_backend(
    "data/mangue_grid.shp", resolution=100,
    attrs=["uso", "alt", "solo"], crs="EPSG:31984"
)
# → RasterBackend, same data, ~8 ms/step @ 94k cells  (≈ 4,500× faster)
```

The data source is the same shapefile. The only difference is the substrate.

---

## API Reference

::: dissmodel.geo.raster.io.shapefile_to_raster_backend

::: dissmodel.geo.raster.io.save_raster_backend
