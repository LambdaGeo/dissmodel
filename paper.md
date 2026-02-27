---
title: 'DisSModel: A Discrete Spatial Modeling Framework for Python'
tags:
  - Python
  - spatial modeling
  - cellular automata
  - system dynamics
  - geospatial
  - simulation
authors:
  - name: Sérgio Costa
    orcid: 0000-0002-3637-296X
    affiliation: 1
  - name: Nerval Santos Junior
    affiliation: 1
affiliations:
 - name: LambdaGeo, Federal University of Maranhão (UFMA)
   index: 1
date: 20 February 2025
bibliography: paper.bib
---

# Summary

DisSModel is a modular, open-source Python framework designed for spatially explicit dynamic modeling. It provides a unified environment for building **Cellular Automata (CA)** and **System Dynamics (SysDyn)** models, leveraging the modern Python geospatial ecosystem. By integrating `GeoPandas` [@jordana2024geopandas] for spatial data handling, `Libpysal` [@rey2022pysal] for neighborhood analysis, and `Salabim` [@salabim] for discrete event simulation, DisSModel offers researchers and students a robust toolset for simulating complex spatial phenomena.

The framework supports flexible grid generation, various neighborhood strategies (Queen, Rook, KNN), and advanced fill strategies for model initialization. It includes built-in visualization tools that work seamlessly with `Matplotlib` [@hunter2007matplotlib] and `Streamlit` [@streamlit], enabling the creation of interactive web applications for model exploration.

# Statement of Need

Spatial modeling is a critical methodology in geography, ecology, epidemiology, and urban planning. While there are existing tools for spatial simulation (e.g., NetLogo, TerraME), many are either language-specific, require learning a domain-specific language (DSL), or lack seamless integration with the modern Python data science stack.

DisSModel addresses this gap by providing a Python-native solution that:

1.  **Eliminates the need for DSLs:** Users can build models using standard Python classes and functions.
2.  **Integrates with the geospatial ecosystem:** Direct support for `GeoDataFrame` allows users to easily import real-world data and perform spatial operations.
3.  **Facilitates reproducibility and sharing:** By supporting Jupyter Notebooks and Streamlit apps, models can be easily shared, visualized, and interactively explored by a broader audience.
4.  **Modernizes legacy workflows:** DisSModel serves as a modern alternative to the TerraME framework, replacing the TerraLib/Lua stack with widely adopted Python libraries.

This framework is particularly useful for researchers who need to develop custom spatial models without the overhead of learning a new proprietary environment, and for educators teaching spatial simulation concepts.

# Features

*   **Cellular Automata Engine:** Efficient handling of grid-based simulations with configurable neighborhood strategies.
*   **System Dynamics Support:** Compartmental modeling capabilities with automatic live plotting.
*   **Flexible Initialization:** Tools for generating grids from dimensions or bounds and initializing cell states using random sampling, zonal statistics, or pattern-based strategies.
*   **Interactive Visualization:** A reactive UI component (`display_inputs`) that automatically generates sidebar widgets from model type annotations, streamlining the creation of interactive simulation apps.
*   **Three Execution Modes:** Models can be run as standalone CLI scripts, interactive Jupyter Notebooks, or deployed as Streamlit web applications.

# Example Usage

Below is a simple example of a System Dynamics SIR (Susceptible-Infected-Recovered) model:

```python
from dissmodel.core import Environment
from dissmodel.models.sysdyn import SIR
from dissmodel.visualization import Chart

env = Environment()
SIR(susceptible=9998, infected=2, recovered=0, duration=2, contacts=6, probability=0.25)
Chart(show_legend=True)
env.run(30)
```

And a Cellular Automaton Forest Fire model:

```python
from dissmodel.core import Environment
from dissmodel.geo import regular_grid
from dissmodel.models.ca import FireModel
from dissmodel.models.ca.fire_model import FireState

gdf = regular_grid(dimension=(30, 30), resolution=1, attrs={"state": FireState.FOREST})
env = Environment(end_time=20)
fire = FireModel(gdf=gdf)
fire.initialize()
env.run()
```

# Acknowledgements

DisSModel is developed by the [LambdaGeo](https://github.com/LambdaGeo) group at the Federal University of Maranhão (UFMA). We acknowledge the contributions of the open-source community, particularly the developers of the libraries upon which this framework depends.

# References
