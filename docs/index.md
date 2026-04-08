# DisSModel

**Discrete Spatial Modeling framework for Python**

DisSModel is a modular, open-source Python framework for spatially explicit dynamic modeling.
Developed by the [LambdaGeo](https://github.com/LambdaGeo) group at the Federal University of Maranhão (UFMA),
it provides a unified environment for building **Cellular Automata (CA)** and **System Dynamics (SysDyn)** models
on top of the Python geospatial ecosystem.

Inspired by the [TerraME](http://www.terrame.org/) framework, DisSModel brings the same modeling
expressiveness to Python — replacing the TerraLib/Lua stack with GeoPandas, NumPy, and Salabim,
while remaining fully interoperable with the broader Python data science ecosystem.

```bash
pip install dissmodel
```

---

## Why DisSModel?

- **Multi-paradigm support** — Cellular Automata, System Dynamics, and Agent-Based Models in a unified environment
- **Dual-substrate architecture** — vector (GeoDataFrame) for spatial expressiveness, raster (NumPy) for high-performance vectorized computation
- **Geospatial ecosystem integration** — GeoPandas, libpysal, rasterio, and rasterstats for advanced spatial operations
- **Open science and reproducibility** — open-source, installable via PyPI, examples included
- **Standardized implementation** — pure Python lowers the barrier for interdisciplinary collaboration

---

## Architecture

DisSModel is organized into four modules:

| Module | Description |
|:---|:---|
| `dissmodel.core` | Simulation clock and execution lifecycle powered by [Salabim](https://www.salabim.org/) |
| `dissmodel.geo` | Spatial data structures — dual-substrate design (vector + raster) |
| `examples.models` | Ready-to-use CA and SysDyn reference implementations |
| `dissmodel.visualization` | Observer-based visualization — `Chart`, `Map`, `RasterMap`, `display_inputs` |

### `dissmodel.geo` — Dual Substrate

The `geo` module provides two independent spatial substrates that share the same simulation clock:

**Vector substrate** (`dissmodel.geo.vector`) — backed by GeoDataFrame. Supports irregular
geometries, direct GIS integration, and libpysal neighbourhoods (Queen, Rook).
Use for models that require spatial joins, real-world projections, or interoperability
with existing GIS workflows.

**Raster substrate** (`dissmodel.geo.raster`) — backed by `RasterBackend` (NumPy 2D arrays).
Replaces cell-by-cell iteration with fully vectorized operations (`shift2d`, `focal_sum`,
`neighbor_contact`). At 10,000 cells, the raster substrate is **~4,500× faster** than the
vector substrate.

| | Vector | Raster |
|---|---|---|
| Data structure | GeoDataFrame | NumPy 2D array (`RasterBackend`) |
| Neighbourhood | Queen / Rook (libpysal) | Moore / Von Neumann (shift2d) |
| Rule pattern | `rule(idx)` per cell | `rule(arrays) → dict` vectorized |
| Performance @ 10k cells | ~2,700 ms/step | ~0.6 ms/step |

---

## Quickstart

### System Dynamics

```python
from dissmodel.core import Environment
from examples.models.sysdyn import SIR
from dissmodel.visualization import Chart

env = Environment()
SIR(susceptible=9998, infected=2, recovered=0, duration=2, contacts=6, probability=0.25)
Chart(show_legend=True)
env.run(30)
```

### Cellular Automaton — Vector

```python
from dissmodel.core import Environment
from dissmodel.geo import vector_grid
from examples.models.ca import FireModel
from examples.models.ca.fire_model import FireState

gdf = vector_grid(dimension=(30, 30), resolution=1, attrs={"state": FireState.FOREST})
env = Environment(end_time=20)
fire = FireModel(gdf=gdf)
fire.initialize()
env.run()
```

### Cellular Automaton — Raster

```python
from dissmodel.core import Environment
from dissmodel.geo.raster.regular_grid import raster_grid
from examples.models.ca import GameOfLifeRaster
from dissmodel.visualization.raster_map import RasterMap

backend = raster_grid(rows=100, cols=100, attrs={"state": 0})

env = Environment(end_time=20)
model = GameOfLifeRaster(backend=backend)
model.initialize()
RasterMap(backend=backend, band="state")
env.run()
```

### Streamlit

```bash
streamlit run examples/streamlit/ca_all.py
streamlit run examples/streamlit/sysdyn_all.py
```

---

## Instantiation order

`Environment` must always be created **before** any model.
Models connect to the active environment automatically on creation.

```
Environment  →  Model  →  display_inputs  →  initialize()  →  Visualization
     ↑             ↑            ↑                  ↑               ↑
  first         second        third              fourth           fifth
```

---

## Included Models

### Cellular Automata

| Model | Description |
|:---|:---|
| `GameOfLife` | Conway's Game of Life with built-in classic patterns |
| `FireModel` | Forest fire spread |
| `FireModelProb` | Probabilistic fire with spontaneous combustion and regrowth |
| `Snow` | Snowfall and accumulation |
| `Growth` | Stochastic radial growth from a center seed |
| `Propagation` | Active state transmission with KNN neighborhood |
| `Anneal` | Binary system relaxation via majority-vote rule |

### System Dynamics

| Model | Description |
|:---|:---|
| `SIR` | Susceptible–Infected–Recovered epidemiological model |
| `PredatorPrey` | Lotka–Volterra ecological dynamics |
| `PopulationGrowth` | Exponential growth with variable rate |
| `Lorenz` | Deterministic chaos — Lorenz attractor |
| `Coffee` | Newton's Law of Cooling |

---

## Python Ecosystem

DisSModel builds on well-established, industry-standard libraries:

| Library | Role |
|:---|:---|
| [GeoPandas](https://geopandas.org/) | Vector data and GeoDataFrame operations |
| [Salabim](https://www.salabim.org/) | Discrete event simulation engine |
| [NumPy](https://numpy.org/) | Vectorized array operations — raster substrate |
| [libpysal](https://pysal.org/libpysal/) | Spatial weights and neighborhood analysis |
| [rasterio](https://rasterio.readthedocs.io/) | GeoTIFF I/O |
| [rasterstats](https://pythonhosted.org/rasterstats/) | Raster/vector zonal statistics |
| [Shapely](https://shapely.readthedocs.io/) | Geometric operations |
| [Matplotlib](https://matplotlib.org/) | Time-series and spatial visualization |
| [Streamlit](https://streamlit.io/) | Reactive web application UI |

---

## Links

- **Source code:** [github.com/LambdaGeo/dissmodel](https://github.com/LambdaGeo/dissmodel)
- **PyPI:** [pypi.org/project/dissmodel](https://pypi.org/project/dissmodel/)
- **LambdaGeo:** [github.com/LambdaGeo](https://github.com/LambdaGeo)

---

## License

MIT © 2026 Sérgio Costa & Nerval Santos Junior — [LambdaGeo/UFMA](https://github.com/LambdaGeo)