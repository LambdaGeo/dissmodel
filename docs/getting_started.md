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

## Instantiation order

The `Environment` must always be created **before** any model.
Models connect to the active environment automatically when instantiated.

```
Environment  →  Model  →  Visualization
     ↑             ↑            ↑
  first         second        third
```

## Minimal example

```python
from dissmodel.core import Environment
from dissmodel.models.sysdyn import SIR
from dissmodel.visualization import Chart

env = Environment()
SIR()
Chart(show_legend=True)
env.run(30)
```
