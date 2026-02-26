# Getting Started

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
