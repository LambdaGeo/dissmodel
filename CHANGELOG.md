# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.2.1] - 2026-03

### Changed
- `parse_idx` now returns `GridPos(row, col)` namedtuple instead of a plain tuple,
  eliminating the `(col, row)` vs `(row, col)` ambiguity. Tuple unpacking remains
  fully compatible — no breaking change for existing callers.
- `regular_grid()` renamed to `vector_grid()`. Old name kept as a `DeprecationWarning`
  alias and will be removed in v0.3.0.

### Added
- `GridPos` namedtuple exported from `dissmodel.geo.vector.regular_grid`.

### Fixed
- `RasterModel.setup()` and `RasterCellularAutomaton.setup()` no longer accept
  `**kwargs`, resolving a salabim incompatibility that raised
  `TypeError: parameter 'kwargs' not allowed`.

---

## [0.2.0] - 2026-03

### Added

#### Raster substrate
- `RasterBackend` — named NumPy array store with vectorized spatial operations:
  `shift2d`, `focal_sum`, `focal_sum_mask`, `neighbor_contact`, `snapshot`.
- `RasterModel` — base class for raster push models, providing `self.backend`,
  `self.shape`, `self.shift`, and `self.dirs` (Moore neighbourhood).
- `RasterCellularAutomaton` — vectorized CA base class; `rule(arrays) → dict`
  replaces per-cell iteration.
- `raster_grid()` / `make_raster_grid()` — `RasterBackend` factory.
- `DIRS_MOORE` and `DIRS_VON_NEUMANN` — neighbourhood direction constants.
- `RasterMap` — visualization component supporting categorical (`color_map`) and
  continuous (`cmap`) modes; renders to Streamlit, Jupyter, interactive window,
  or headless PNG frames.

#### Vector substrate
- `SpatialModel` — GeoDataFrame-based push model with `create_neighborhood()`,
  `neighs_id()`, `neighs()`, and `neighbor_values()`.
- `vector_grid()` — replaces `regular_grid()` as the canonical grid factory name.

#### Examples and benchmarks
- `GameOfLifeRaster` — Conway's Game of Life on raster substrate.
- `FireModelRaster` — forest fire spread on raster substrate.
- `benchmark_game_of_life.py` — vector vs raster benchmark with exact cell-by-cell
  validation; supports `--steps`, `--sizes`, `--no-validation` flags.
- `benchmark_raster_vs_vector.py` — flood model benchmark at realistic workload.
- CLI examples updated.

#### Tests
- Full test suite: `tests/vector/`, `tests/raster/`, `tests/integration/`.
- `tests/integration/test_game_of_life.py` — exact cell-by-cell validation across
  5×5, 10×10, 20×20 grids and 5 seeds.
- `tests/integration/test_flood_model.py` — cross-substrate equivalence with 95%
  match threshold.

### Changed
- Package reorganized: `dissmodel.geo.vector.*` and `dissmodel.geo.raster.*`
  replace the flat `dissmodel.geo.*` layout.
- Documentation migrated to MkDocs Material with separate API reference pages for
  vector and raster substrates.

### Fixed
- Import paths corrected across all examples after package reorganization.
- `celullar_automaton.py` filename typo fixed → `cellular_automaton.py`.

### Performance
Benchmarks on Conway's Game of Life (10 steps, Python 3.12, NumPy):

| Grid | Cells | Raster (ms/step) | Vector (ms/step) | Speedup |
|-----:|------:|-----------------:|-----------------:|--------:|
| 10×10 | 100 | 0.15 | 30.11 | 206× |
| 50×50 | 2,500 | 0.20 | 647.22 | 3,164× |
| 100×100 | 10,000 | 0.60 | 2,715.16 | 4,491× |
| 1,000×1,000 | 1,000,000 | 25.85 | — | — |

---

## [0.1.5] - 2026-02

### Added
- JOSS submission at this version.

### Fixed
- Minor documentation and packaging fixes.

---

## [0.1.0] - 2025

### Added
- Initial release.
- `CellularAutomaton` and `SpatialModel` on GeoDataFrame substrate.
- `regular_grid()`, `fill()`, `FillStrategy`.
- System Dynamics models: `SIR`, `PredatorPrey`, `PopulationGrowth`, `Lorenz`, `Coffee`.
- Cellular Automata models: `GameOfLife`, `FireModel`, `FireModelProb`, `Snow`, `Growth`,
  `Propagation`, `Anneal`.
- Salabim integration via `dissmodel.core.Environment` and `Model`.
- Streamlit examples.
