# Getting Started

## Why Python?

Python has become the standard language for data science and geographic analysis,
with a rich ecosystem of libraries that complement each other naturally:

- **Greater flexibility** — NumPy, SciPy, Pandas, GeoPandas, rasterio, and
  machine learning frameworks can all be integrated into the same workflow,
  allowing models of arbitrary complexity.
- **Active development** — the Python geospatial community is extremely active,
  with frequent updates, extensive documentation, and strong support for
  reproducible research practices.
- **Accessibility** — Python is widely considered one of the easiest languages
  to learn, making spatial modeling more approachable for environmental scientists
  and territorial planners who are not primarily software developers.

DisSModel builds on this ecosystem rather than replacing it. A DisSModel simulation
is just Python — the full power of the scientific stack is available at every step.

---

## Installation

```bash
pip install dissmodel
```

Or in editable mode for development:

```bash
git clone https://github.com/lambdageo/dissmodel
cd dissmodel
pip install -e .
```

---

## Instantiation order

The `Environment` must always be created **before** any model.
Models connect to the active environment automatically when instantiated.

```
Environment  →  Model  →  Visualization  →  env.run()
     ↑             ↑            ↑                ↑
  first         second        third           fourth
```

---

## Minimal example

```python
from dissmodel.core import Environment
from dissmodel.models.sysdyn import SIR
from dissmodel.visualization import Chart

env = Environment()
SIR(susceptible=9998, infected=2, recovered=0,
    duration=2, contacts=6, probability=0.25)
Chart(show_legend=True)
env.run(30)
```

---

## Execution modes

DisSModel supports three execution strategies. All three follow the same
`Environment → Model → Visualization → env.run()` pattern — only the
entry point and how results are displayed differ.

### Command Line (CLI)

Best for automation, batch experiments, and integration with processing pipelines.

```bash
python examples/cli/sir_model.py
```

CLI examples are located in `examples/cli/`.

### Jupyter Notebook

Best for incremental exploration, teaching, and visual analysis. DisSModel
detects the Jupyter environment automatically and renders visualizations inline.

```python
from dissmodel.core import Environment
from dissmodel.geo import regular_grid
from dissmodel.models.ca import GameOfLife
from dissmodel.visualization.map import Map
from matplotlib.colors import ListedColormap

gdf = regular_grid(dimension=(30, 30), resolution=1)

env = Environment(end_time=20)
model = GameOfLife(gdf=gdf)
model.initialize()

Map(
    gdf=gdf,
    plot_params={
        "column": "state",
        "cmap": ListedColormap(["white", "black"]),
        "ec": "gray",
    },
)

env.run()
```

Notebook examples are located in `examples/notebooks/`.

### Streamlit Web Application

Best for interactive demos and non-technical users. Parameters are configured
via sliders and input fields directly in the browser.

```bash
streamlit run examples/streamlit/sir_model.py

# or run all models in a single interface:
streamlit run examples/streamlit/run_all.py
```

Streamlit examples are located in `examples/streamlit/`.

---

## Choosing a substrate

DisSModel provides two spatial substrates for cellular automata. Choose based
on your performance and flexibility requirements:

| | Vector | Raster |
|---|---|---|
| **Data structure** | GeoDataFrame | NumPy 2D array |
| **Neighbourhood** | Queen / Rook (libpysal) | Moore / Von Neumann (shift2d) |
| **Rule pattern** | `rule(idx)` per cell | `rule(arrays) → dict` vectorized |
| **Performance** | ~2,700 ms/step @ 10k cells | ~0.6 ms/step @ 10k cells |
| **Best for** | Irregular grids, GIS integration | Large grids, performance-critical models |

See the [API Reference](api/geo/vector.md) for full details on each substrate.