# Why DisSModel?

Yes — you can build the same models using salabim, GeoPandas, NumPy, and libpysal
directly. DisSModel does not add new capabilities that are impossible without it.
What it adds is **structure, convention, and significantly less boilerplate**.

This page shows, side by side, what building a spatial CA looks like with and
without DisSModel.

---

## The raw approach

To build a simple flood propagation model using salabim + GeoPandas directly,
a researcher would need to:

```python
import math
import salabim as sim
import geopandas as gpd
from libpysal.weights import Queen

# 1. create the grid manually
gdf = gpd.read_file("grid.shp")
gdf["uso"] = 5
gdf["alt"] = 0.0

# 2. compute neighbourhood manually
w = Queen.from_dataframe(gdf)
neighs = {idx: list(w.neighbors[i]) for i, idx in enumerate(gdf.index)}

# 3. define the simulation clock
class FloodEnv(sim.Environment):
    def __init__(self, start, end):
        super().__init__()
        self._start = start
        self._end   = end

    def now(self):
        return super().now() + self._start

# 4. define the model as a Component
class FloodModel(sim.Component):
    def __init__(self, gdf, neighs, taxa, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gdf   = gdf
        self.neighs = neighs
        self.taxa  = taxa

    def process(self):
        env = self.env
        while env.now() < END_TIME:
            nivel = env.now() * self.taxa
            uso_past = self.gdf["uso"].copy()
            alt_past = self.gdf["alt"].copy()
            # ... flood logic here (50+ lines) ...
            self.hold(1)

# 5. wire everything together
env = FloodEnv(start=2012, end=2100)
model = FloodModel(gdf=gdf, neighs=neighs, taxa=0.011)
env.run(till=88)
```

This works. But the researcher is responsible for:

- Writing the `Environment` subclass with `start_time` / `end_time` / `now()` every time
- Manually computing and caching the neighbourhood
- Managing the `process()` loop and `hold()` calls
- Deciding where to store the grid, the neighbourhood, the snapshot
- Writing visualization from scratch for every project

---

## The DisSModel approach

```python
from dissmodel.core import Environment
from dissmodel.geo import vector_grid
from dissmodel.geo.vector.model import SpatialModel
from dissmodel.visualization.map  import Map
from libpysal.weights import Queen

gdf = vector_grid(dimension=(100, 100), resolution=100,
                  attrs={"uso": 5, "alt": 0.0})

class FloodModel(SpatialModel):
    def setup(self, taxa=0.011):
        self.taxa = taxa
        self.create_neighborhood(strategy=Queen, use_index=True)

    def execute(self):
        nivel    = self.env.now() * self.taxa
        uso_past = self.gdf["uso"].copy()
        alt_past = self.gdf["alt"].copy()
        # ... flood logic here (same lines) ...

env = Environment(start_time=2012, end_time=2100)
FloodModel(gdf=gdf, taxa=0.011)
Map(gdf=gdf, plot_params={"column": "uso"})
env.run()
```

Same result. The flood logic is identical. Everything else is handled.

---

## What DisSModel removes

| Concern | Raw salabim + libs | DisSModel |
|---|---|---|
| `start_time` / `end_time` / `now()` | Write every time | Built into `Environment` |
| Neighbourhood computation | Manual (`Queen.from_dataframe`, index mapping) | `create_neighborhood()` one call |
| Neighbourhood cache | Manual dict | `_neighs_cache` automatic |
| Snapshot semantics (`.past`) | Manual `.copy()` before loop | Convention enforced by framework |
| `process()` loop + `hold()` | Write every time | Handled by `Model.process()` |
| Visualization wiring | Bespoke per project | `Map`, `Chart`, `RasterMap` drop-in |
| Raster vectorization | Manual NumPy boilerplate | `RasterBackend`: `shift2d`, `focal_sum`, `neighbor_contact` |
| Headless PNG output | Manual `savefig` loop | `RasterMap` automatic |
| Streamlit integration | Full UI code per model | `display_inputs` one call |

---

## The raster substrate gain

The most significant gain is in the raster substrate. Without DisSModel, a
researcher writing a vectorized CA in NumPy must implement shift operations,
boundary handling, focal sums, and neighbour contact masks from scratch — and
get them right for every model.

With `RasterBackend`, these are solved once and reused everywhere:

```python
# without DisSModel — manual shift, every model
import numpy as np

def shift2d(arr, dr, dc):
    rows, cols = arr.shape
    out = np.zeros_like(arr)
    rs  = slice(max(0, -dr), min(rows, rows - dr))
    rd  = slice(max(0,  dr), min(rows, rows + dr))
    cs  = slice(max(0, -dc), min(cols, cols - dc))
    cd  = slice(max(0,  dc), min(cols, cols + dc))
    out[rd, cd] = arr[rs, cs]
    return out

# repeated in every project, every model
```

```python
# with DisSModel — already solved
from dissmodel.geo.raster.backend import RasterBackend

b = RasterBackend(shape=(100, 100))
# shift2d, focal_sum, focal_sum_mask, neighbor_contact — all available
```

---

## Reproducibility and convention

A less obvious but important benefit is **convention**. When a research group
builds multiple models over several years, the question is not whether a single
model works — it is whether a new student can read, modify, and extend a model
written two years ago.

DisSModel enforces:

- `Environment` always comes first
- `Model` subclasses always implement `execute()`
- Neighbourhood is always attached via `create_neighborhood()`
- Visualization components are always separate from model logic

This is a small constraint that pays large dividends in research group settings,
where code is written by graduate students with varying Python experience.

---

## When raw salabim is better

DisSModel is not always the right choice:

- **Non-spatial models** — pure System Dynamics or agent-based models without
  a spatial grid benefit less; salabim directly is simpler.
- **Irregular agent movement** — models where agents move freely across space
  (not on a fixed grid) are not well served by the vector or raster substrate.
- **Custom performance requirements** — if you need GPU acceleration or
  distributed computation, you will eventually need to go below DisSModel.

For everything else — grid-based CA, LUCC, flood propagation, epidemic spread
on spatial grids — DisSModel removes the scaffolding and lets you focus on
the transition rule.
