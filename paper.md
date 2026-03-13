---
title: "DisSModel: A Python Framework for Spatially Explicit Dynamic Modeling"
tags:
  - Python
  - Geographic Information Systems
  - Dynamic Spatial Modeling
  - Cellular Automata
  - Land Use and Cover Change (LUCC)
  - Discrete-Event Simulation
authors:
  - name: Sérgio Souza Costa
    orcid: 0000-0002-0232-4549
    affiliation: "1"
  - name: Nerval de Jesus Santos Junior
    affiliation: "1"
    orcid: 0009-0000-2339-3191
  - name: Felipe Martins Sousa
    affiliation: "1"
    orcid: 0009-0009-0505-4845
affiliations:
  - name: Universidade Federal do Maranhão (UFMA)
    index: "1"
    city: São Luís
    state: MA
    country: Brazil
date: 2 March 2026
bibliography: paper.bib
---

## Summary

DisSModel (Discrete Spatial Modeling) is a modular Python framework designed for spatially explicit dynamic modeling, specifically targeting the complexities of Land Use and Land Cover Change (LUCC). Developed to bridge the gap between static geospatial analysis and high-level dynamic simulations, DisSModel translates the modeling paradigms of the TerraME framework [@Carneiro2013] into the Python ecosystem. It enables researchers to simulate complex socio-environmental systems—including forest fires, epidemiological spreads, and urban expansion—by integrating the simulation clock of discrete-event engines with the spatial data structures of GeoPandas [@Jordahl2021].

The framework provides a **dual-substrate architecture**: a vector substrate backed by GeoDataFrame for flexibility and spatial expressiveness, and a raster substrate backed by NumPy 2D arrays for high-performance vectorized computation. DisSModel is available through the LambdaGeo GitHub repository and on PyPI.

## Statement of Need

In the Geographic Information Systems (GIS) landscape, Python has become the lingua franca for data science, supported by libraries such as GeoPandas for vector manipulation and PySAL for spatial statistics. However, these tools are primarily designed for static analysis. Dynamic spatial modeling—simulating how landscapes evolve over time—has historically required specialized platforms like TerraME [@Carneiro2013] or Dinamica EGO.

While TerraME is conceptually robust, the requirement for Lua scripting creates a barrier for data scientists already invested in the Python ecosystem. Furthermore, while discrete-event simulation libraries exist, they lack native "glue code" to synchronize a simulation clock with the geographical state of a GeoDataFrame. DisSModel fulfills this need by providing a Pythonic implementation of the TerraME paradigm, democratizing access to complex modeling for territorial planners and environmental scientists [@Verburg2006]. It offers native support for hybrid data types—Geo-fields and Geo-objects—allowing for simulations that remain interoperable with modern machine learning and GIS workflows [@Bezerra2022; @Varnier2025].

## State of the field

DisSModel occupies a unique niche between general-purpose agent-based modeling (ABM) libraries and specialized GIS simulation software. The following table highlights its positioning:

| Aspect | TerraME | Dinamica EGO | DisSModel |
|--------|---------|--------------|-----------|
| Language | Lua | Visual/Internal | Python |
| Simulation Engine | Discrete Event | Cellular Automata | Integrated Salabim (DES) |
| Spatial Structure | CellularSpace (Fixed) | Cellular Grid | GeoDataFrame + NumPy (Dual) |
| GIS Integration | TerraLib | Native Raster | GeoPandas / Rasterio |
| Extensibility | Script-based | Block-based | Class Inheritance |
| Anisotropy | GPM Support | Limited | GPM Support |

While frameworks like **NetLogo** and **Mesa** are excellent for ABM, they often require significant boilerplate to handle real-world spatial projections. DisSModel simplifies this by using GeoPandas as its core engine, following the discrete spatial modeling approach proposed by @SantosJunior2025.

## Software Design

DisSModel is organized into four modules, following a strict separation of concerns that allows researchers to extend the framework through class inheritance.

- **Core:** The central engine that manages the simulation clock and discrete-event execution via Salabim integration.
- **Geo:** Manages spatial representations through a dual-substrate design. The vector substrate (`vector_grid`, `SpatialModel`, `CellularAutomaton`) operates on GeoDataFrame structures with libpysal neighborhoods [@Rey2021]. The raster substrate (`raster_grid`, `RasterModel`, `RasterCellularAutomaton`) operates on named NumPy arrays via `RasterBackend`, enabling fully vectorized spatial operations — `shift2d`, `focal_sum`, and `neighbor_contact` — that replace cell-by-cell iteration loops.
- **Models:** Provides templates for common paradigms, including Cellular Automata (CA) and System Dynamics.
- **Visualization:** Integrates Matplotlib for static outputs, Streamlit for interactive dashboards, and `RasterMap` for step-by-step raster rendering in both headless and interactive modes.

## Performance

The dual-substrate design exposes a fundamental performance trade-off. The vector substrate offers spatial expressiveness and direct integration with GIS workflows, while the raster substrate achieves high throughput through NumPy vectorization.

Benchmarks running Conway's Game of Life under identical conditions on both substrates show the following results:

| Grid | Cells | Raster (ms/step) | Vector (ms/step) | Speedup |
|-----:|------:|-----------------:|-----------------:|--------:|
| 10×10 | 100 | 0.15 | 30.11 | 206× |
| 50×50 | 2,500 | 0.20 | 647.22 | 3,164× |
| 100×100 | 10,000 | 0.60 | 2,715.16 | 4,491× |
| 500×500 | 250,000 | 15.36 | — | — |
| 1,000×1,000 | 1,000,000 | 25.85 | — | — |

Results were validated cell-by-cell: both substrates produce identical output for all comparable grid sizes. The raster substrate processes grids of one million cells in approximately 26 ms per step, making it suitable for large-scale LUCC simulations such as the BR-MANGUE coastal dynamics model (94,704 cells, 88 time steps).

## Research impact statement

DisSModel provides a critical bridge for the environmental modeling community. By providing a Pythonic interface for complex spatial dynamics, it lowers the barrier for scientists to move from static GIS analysis to dynamic simulations. This framework has already been instrumental in academic research at the **LambdaGeo** group (UFMA), supporting studies on mangrove ecosystem dynamics and land-use change, building upon established spatial modeling practices [@Verburg2006; @SantosJunior2025].

## AI usage disclosure

This submission used generative AI tools (Claude Sonnet 4.6, NotebookLM, and Google Jules) to assist with structuring documentation, synthesizing prior work, and generating submission checklists. All outputs were reviewed and validated by the human authors.

## References
