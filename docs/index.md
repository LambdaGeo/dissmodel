# DisSModel

**Discrete Spatial Modeling framework for Python**

DisSModel is a modular, open-source Python framework for spatially explicit dynamic modeling.
Developed by the [LambdaGeo](https://github.com/LambdaGeo) group at the Federal University of Maranhão (UFMA),
it provides a unified environment for building **Cellular Automata (CA)** and **System Dynamics (SysDyn)** models
on top of the Python geospatial ecosystem.

```bash
pip install dissmodel
```

---

## Why DisSModel?

DisSModel was designed as a modern, Pythonic alternative to the [TerraME](http://www.terrame.org/) framework,
replacing the TerraLib/Lua stack with the standardized GeoPandas/Python stack.
This transition gives researchers direct access to the full Python data science ecosystem
while maintaining the modeling expressiveness required for Land Use and Cover Change (LUCC) applications.

**Core objectives:**

- **Multi-paradigm support** — Cellular Automata, System Dynamics, and Agent-Based Models in a unified environment
- **Geospatial ecosystem integration** — GeoPandas, libpysal, and rasterstats for advanced spatial operations
- **Open science and reproducibility** — open-source, installable via PyPI, examples included
- **Standardized implementation** — pure Python lowers the barrier for interdisciplinary collaboration

---

## Architecture

DisSModel is organized into four modules:

| Module | Description |
|:---|:---|
| `dissmodel.core` | Simulation clock and execution lifecycle powered by [Salabim](https://www.salabim.org/) |
| `dissmodel.geo` | Spatial data structures — grid generation, fill strategies, neighborhood |
| `dissmodel.models` | Ready-to-use CA and SysDyn reference implementations |
| `dissmodel.visualization` | Observer-based visualization — `Chart`, `Map`, `display_inputs`, `@track_plot` |

---

## Quickstart

### System Dynamics

```python
from dissmodel.core import Environment
from dissmodel.models.sysdyn import SIR
from dissmodel.visualization import Chart

env = Environment()
SIR(susceptible=9998, infected=2, recovered=0, duration=2, contacts=6, probability=0.25)
Chart(show_legend=True)
env.run(30)
```

### Cellular Automaton

```python
from dissmodel.core import Environment
from dissmodel.geo import vector_grid
from dissmodel.models.ca import FireModel
from dissmodel.models.ca.fire_model import FireState

gdf = vector_grid(dimension=(30, 30), resolution=1, attrs={"state": FireState.FOREST})
env = Environment(end_time=20)
fire = FireModel(gdf=gdf)
fire.initialize()
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
| [libpysal](https://pysal.org/libpysal/) | Spatial weights and neighborhood analysis |
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