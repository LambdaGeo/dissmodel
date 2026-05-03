# Geo

The `dissmodel.geo` module provides the spatial infrastructure for building
simulation models. It handles grid generation, neighbourhood computation, and
attribute initialization — without imposing any domain logic.

```python
from dissmodel.geo import vector_grid, fill, FillStrategy
from dissmodel.geo.vector.neighborhood import attach_neighbors
from dissmodel.geo.raster.backend import RasterBackend
from dissmodel.geo.raster.raster_grid import raster_grid
```

---

## Dual-substrate design

The module provides two independent spatial substrates. Both share the same
`Environment` and clock — a vector model and a raster model can run
side by side in the same `env.run()`.

| | Vector | Raster |
|---|---|---|
| **Module** | `dissmodel.geo.vector` | `dissmodel.geo.raster` |
| **Data structure** | `GeoDataFrame` (GeoPandas) | `RasterBackend` (NumPy 2D arrays) |
| **Grid factory** | `vector_grid()` | `raster_grid()` |
| **Neighbourhood** | Queen / Rook (libpysal) | Moore / Von Neumann (`shift2d`) |
| **Rule pattern** | `rule(idx)` per cell | `rule(arrays) → dict` vectorized |
| **GIS integration** | CRS, projections, spatial joins | rasterio I/O, Xarray interop |
| **Best for** | Irregular grids, real-world data | Large grids, performance-critical models |

---

## Vector substrate

The vector substrate uses a `GeoDataFrame` as the spatial grid. Any model can
operate directly on real geographic data — shapefiles, GeoJSON, real CRS — with
no conversion step.

```python
import geopandas as gpd
from dissmodel.core import Model, Environment
from dissmodel.visualization.map import Map

gdf = gpd.read_file("area.shp")
gdf.set_index("object_id", inplace=True)

env = Environment(start_time=1, end_time=20)

class ElevationModel(Model):
    def setup(self, gdf, rate=0.01):
        self.gdf  = gdf
        self.rate = rate

    def execute(self):
        self.gdf["alt"] += self.rate

ElevationModel(gdf=gdf, rate=0.01)
Map(gdf=gdf, plot_params={"column": "alt", "cmap": "Blues", "legend": True})
env.run()
```

For abstract (non-georeferenced) grids, use `vector_grid()`:

```python
from dissmodel.geo import vector_grid

# from dimension + resolution
gdf = vector_grid(dimension=(10, 10), resolution=1)

# from bounding box + resolution
gdf = vector_grid(bounds=(0, 0, 1000, 1000), resolution=100)

# from an existing GeoDataFrame
gdf = vector_grid(gdf=base_gdf, resolution=50)
```

---

## Sync models

Both substrates provide a synchronised variant that manages `_past` snapshots
automatically — equivalent to TerraME's `cs:synchronize()`.

### `SyncSpatialModel`

Declare `self.land_use_types` in `setup()` and `<col>_past` columns are
created and updated before and after each step:

```python
from dissmodel.geo.vector.sync_model import SyncSpatialModel

class LUCCModel(SyncSpatialModel):
    def setup(self, gdf):
        self.gdf             = gdf
        self.land_use_types  = ["f", "d", "outros"]

    def execute(self):
        uso_past = self.gdf["f_past"]   # state at beginning of step
        # ... update self.gdf["f"] ...
```

### `SyncRasterModel`

Same semantics for the raster substrate. Copies each array in `land_use_types`
to `<n>_past` in the `RasterBackend`:

```python
from dissmodel.geo.raster.sync_model import SyncRasterModel

class LUCCRasterModel(SyncRasterModel):
    def setup(self, backend):
        self.backend         = backend
        self.land_use_types  = ["f", "d", "outros"]

    def execute(self):
        f_past = self.backend.get("f_past")   # state at beginning of step
        # ... update self.backend.arrays["f"] ...
```

Both expose `synchronize()` as a public method for manual use when the
automatic pre/post-step timing is not sufficient.

---

## Raster substrate

The raster substrate stores named NumPy arrays in a `RasterBackend`. All
operations (`shift2d`, `focal_sum`, `neighbor_contact`) are fully vectorized —
no Python loops over cells.

```python
from dissmodel.geo.raster.raster_grid import raster_grid
from dissmodel.geo.raster.backend import RasterBackend
import numpy as np

backend = raster_grid(rows=100, cols=100, attrs={"state": 0, "alt": 0.0})

# read / write arrays
state = backend.get("state").copy()    # snapshot — equivalent to .past in TerraME
backend.arrays["state"] = new_state

# vectorized neighbourhood operations
shifted    = RasterBackend.shift2d(state, -1, 0)   # northern neighbour of each cell
n_active   = backend.focal_sum_mask(state == 1)    # count active Moore neighbours
has_active = backend.neighbor_contact(state == 1)  # bool mask: any active neighbour?
```

### Xarray interoperability

`RasterBackend` can be converted to and from `xr.Dataset`, enabling integration
with the Pangeo ecosystem (Zarr, Dask, JupyterHub):

```python
# export — each array becomes a DataVariable with (y, x) dimensions
ds = backend.to_xarray(time=42)
ds.to_zarr("output.zarr")

# import — recovers arrays, transform, and CRS
backend2 = RasterBackend.from_xarray(ds)
```

Spatial coordinates are derived from `backend.transform` (rasterio Affine) when
available. CRS is stored as a `spatial_ref` coordinate following the CF-1.8
convention.

---

## Filling grid attributes

The `fill()` function initialises GeoDataFrame columns from spatial data sources,
avoiding manual cell-by-cell loops.

```python
from dissmodel.geo import fill, FillStrategy
```

### Zonal statistics from a raster

```python
import rasterio

with rasterio.open("altitude.tif") as src:
    raster = src.read(1)
    affine = src.transform

fill(
    FillStrategy.ZONAL_STATS,
    vectors=gdf, raster_data=raster, affine=affine,
    stats=["mean", "min", "max"], prefix="alt_",
)
# → adds columns alt_mean, alt_min, alt_max to gdf
```

### Minimum distance to features

```python
rivers = gpd.read_file("rivers.shp")

fill(FillStrategy.MIN_DISTANCE, from_gdf=gdf, to_gdf=rivers, attr_name="dist_river")
```

### Random sampling

```python
fill(
    FillStrategy.RANDOM_SAMPLE,
    gdf=gdf, attr="land_use",
    data={0: 0.7, 1: 0.3},   # 70% class 0, 30% class 1
    seed=42,
)
```

### Fixed pattern (useful for tests)

```python
pattern = [[1, 0, 0],
           [0, 1, 0],
           [0, 0, 1]]

fill(FillStrategy.PATTERN, gdf=gdf, attr="zone", pattern=pattern)
```

Custom strategies can be registered:

```python
from dissmodel.geo.vector.fill import register_strategy

@register_strategy("my_strategy")
def fill_my_strategy(gdf, attr, **kwargs):
    ...
```

---

## Neighbourhood

Spatial neighbourhoods are built via `attach_neighbors()` or directly through
`create_neighborhood()` on any `CellularAutomaton` or `SpatialModel`.

```python
from libpysal.weights import Queen, Rook, KNN
from dissmodel.geo.vector.neighborhood import attach_neighbors

# topological (Queen — edge or vertex contact)
gdf = attach_neighbors(gdf, strategy=Queen)

# topological (Rook — edge contact only)
gdf = attach_neighbors(gdf, strategy=Rook)

# distance-based (k nearest neighbours)
gdf = attach_neighbors(gdf, strategy=KNN, k=4)

# precomputed (from dict or JSON file — faster for large grids)
gdf = attach_neighbors(gdf, neighbors_dict="neighborhood.json")
```

| Strategy | Use case |
|----------|----------|
| `Queen` | Standard CA — cells share an edge or vertex |
| `Rook` | Von Neumann-style — edge contact only |
| `KNN` | Point data, non-contiguous polygons |
| `neighbors_dict` | Precomputed — skip recomputation on repeated runs |

---

## See also

- [Vector API Reference](vector.md)
- [Raster API Reference](raster.md)
