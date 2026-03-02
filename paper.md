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
    orcid: 0000-0000-0000-0000
    affiliation: "1"
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

DisSModel (Discrete Spatial Modeling) is a modular Python framework designed for spatially explicit dynamic modeling, specifically targeting the complexities of Land Use and Land Cover Change (LUCC). Developed to bridge the gap between static geospatial analysis and high-level dynamic simulations, DisSModel translates the modeling paradigms of the TerraME framework into the Python ecosystem. It enables researchers to simulate complex socio-environmental systems—including forest fires, epidemiological spreads, and urban expansion—by integrating the simulation clock of discrete-event engines with the spatial data structures of GeoPandas.

The framework provides a unified workflow for data ingestion, spatial homogenization via cellular grids, and interactive visualization. DisSModel is currently available for the research community through the LambdaGeo GitHub repository and for testing via TestPyPI.

## Statement of Need

In the Geographic Information Systems (GIS) landscape, Python has become the lingua franca for data science, supported by libraries such as GeoPandas for vector manipulation and PySAL for spatial statistics. However, these tools are primarily designed for static analysis. Dynamic spatial modeling—simulating how landscapes evolve over time—has historically required specialized platforms like TerraME (built on Lua) or Dinamica EGO (utilizing visual programming).

While TerraME is conceptually robust, the requirement for Lua scripting creates a barrier for data scientists already invested in the Python ecosystem. Furthermore, while discrete-event simulation libraries like Salabim exist, they lack native "glue code" to synchronize a simulation clock (Environment) with the geographical state of a GeoDataFrame. DisSModel fulfills this need by providing a Pythonic implementation of the TerraME paradigm, democratizing access to complex modeling for territorial planners and environmental scientists. It offers native support for hybrid data types—Geo-fields (rasters) and Geo-objects (vectors)—allowing for complex simulations that remain interoperable with modern machine learning and GIS workflows.

## Software Architecture and Design

DisSModel is organized into four modules, following a strict separation of concerns that allows researchers to extend the framework through class inheritance. A critical architectural requirement for the framework is the instantiation order: the Environment must be created first, as all subsequent models and visualization components automatically connect to the active simulation clock.

- **Core:** The central engine that manages the simulation clock and discrete-event execution via Salabim integration. It handles temporal synchronization, ensuring that spatial states are updated and recorded correctly across time steps.  
- **Geo:** Manages spatial representations. The `regular_grid` function is used for spatial homogenization, aligning disparate rasters and vectors into a unified cellular space. This module also supports Generalized Proximity Matrices (GPM) to model anisotropic spaces, allowing for more realistic neighborhood interactions beyond standard Moore or von Neumann definitions.  
- **Models:** Provides templates for common paradigms. Current support includes Cellular Automata (CA) and System Dynamics. Users can implement specific rules for models such as Conway’s Game of Life, FireModelProb, and the Coffee model. Note: Support for Agent-Based Modeling (ABM) is currently under development and planned for future releases.  
- **Visualization:** Integrates Matplotlib for publication-quality static outputs and Streamlit for interactive dashboards. This allows for rapid hypothesis validation through real-time maps and time-series charts.

## Illustrative Examples

### Cellular Automata: Game of Life and Fire Models

DisSModel demonstrates emergent behavior through the classic Game of Life, where local rules produce complex global patterns on an abstract grid. More advanced spatial applications include the FireModelProb and Snow models. By integrating Rasterio, the FireModelProb simulates stochastic fire propagation across geographically referenced terrains, accounting for environmental variables like elevation and land use.

### System Dynamics: SIR and Coffee Models

The framework excels at coupling non-spatial mathematical models with spatial environments. The SIR (Susceptible, Infected, Recovered) model illustrates epidemiological spread across a population grid. Additionally, the Coffee model implementation showcases the framework’s ability to handle complex system interactions and state transitions, aiding in the analysis of agricultural and socio-economic dynamics.

## Mentions and Comparisons

The following table highlights DisSModel's unique positioning as a "glue" framework between discrete simulation and Pythonic GIS.

| Aspect | TerraME | Dinamica EGO | DisSModel |
|--------|---------|--------------|-----------|
| Language | Lua | Visual/Internal | Python |
| Simulation Engine | Discrete Event | Cellular Automata | Integrated Salabim (DES) |
| Spatial Structure | CellularSpace (Fixed) | Cellular Grid | GeoDataFrame (Dynamic) |
| GIS Integration | TerraLib | Native Raster | GeoPandas / Rasterio |
| Extensibility | Script-based | Block-based | Class Inheritance (Pythonic) |
| Anisotropy | GPM Support | Limited | GPM Support |

## AI usage disclosure

This submission used generative AI tools to assist with specific aspects of the manuscript and software documentation. Specifically:

- **Claude Sonnet 4.6** ([claude.ai](https://claude.ai/)) was used to help structure and format the **documentation of the Python code**, following standard coding and documentation conventions.  
- **NotebookLM** (version unspecified) was used to **synthesize prior work and draft text sections** summarizing the library, as included in the manuscript.
- **Google Jules** (version unspecified) was used to **generate an initial checklist of tasks and best practices** for preparing the software repository for submission.


All outputs generated by these AI tools were **reviewed, edited, and validated by the human authors**, who made all core design and writing decisions. The authors take **full responsibility** for the accuracy, originality, licensing, and ethical compliance of all submitted materials.

## References

Bezerra, F. G. S., Sousa, L. F., Medeiros, L. F., Andrade, M. J., & Silva, R. M. (2022). New land-use change scenarios for Brazil: refining global SSPs with a regional spatially-explicit allocation model. PLOS ONE, 17(4). https://doi.org/10.1371/journal.pone.0256052

Carneiro, T. G. S., Aguiar, A. P. D., Escada, M. I. S., & Câmara, G. (2013). TerraME: A multi-paradigm simulation framework for environmental modeling. Environmental Modelling & Software.

Jordahl, K., et al. (2021). geopandas/geopandas: v0.5.0. Zenodo. https://doi.org/10.5281/zenodo.3946767

Santos Junior, N. J. (2025). Discrete Spatial Modeling: Uma proposta de arcabouço para construção de modelos dinâmicos espacialmente explícitos baseado no ecossistema Python. (Monograph, Federal University of Maranhão).

Turner, B., et al. (1995). Land-Use and Land-Cover Change: science/research plan.

Varnier, M., & Weber, E. J. (2025). Evaluating the accuracy of land-use change models for predicting vegetation loss across brazilian biomes. Land, 14(3). https://doi.org/10.3390/land14030560

Verburg, P. H., et al. (2006). Land use change modelling: current practice and research priorities. GeoJournal, 61(4).