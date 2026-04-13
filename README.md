# DisSModel 🌍

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![PyPI version](https://badge.fury.io/py/dissmodel.svg)](https://pypi.org/project/dissmodel/)
[![LambdaGeo](https://img.shields.io/badge/LambdaGeo-Research-green.svg)](https://github.com/LambdaGeo)

---

## 📖 About

**DisSModel** is a modular Python framework for spatially explicit dynamic simulation models. Developed by the [LambdaGeo](https://github.com/LambdaGeo) group at the Federal University of Maranhão (UFMA), it provides the simulation layer that connects domain models (LUCC, coastal dynamics) to a reproducible, cloud-native execution platform.

| INPE / TerraME Ecosystem | LambdaGeo Ecosystem | Role |
|--------------------------|---------------------|------|
| **TerraME** | `dissmodel` | Generic framework for dynamic spatial modeling |
| **LUCCME** | `DisSLUCC` | LUCC domain models built on dissmodel |
| — | `coastal-dynamics` | Coastal domain models built on dissmodel |
| **TerraLib** | `geopandas` / `rasterio` | Geographic data handling |

---

## 🌟 Key Features

- **Dual substrate** — same model logic runs on vector (`GeoDataFrame`) and raster (`RasterBackend`/NumPy).
- **Discrete Event Simulation** — built on [Salabim](https://salabim.org/); time advances to the next relevant event, not millisecond by millisecond.
- **Executor pattern** — strict separation between science (models) and infrastructure (I/O, cloud, queues).
- **Experiment tracking** — every run generates an immutable `ExperimentRecord` with SHA-256 checksums, TOML snapshot, and full provenance.
- **Storage-agnostic I/O** — `dissmodel.io` handles local paths and `s3://` URIs transparently.
- **CLI + Platform** — the same executor runs locally via CLI and on the DisSModel Platform via API.

---

## 🏗 Architecture

```
┌──────────────────────────────────────────────────────────┐
│  Science Layer  (Model / Salabim)                        │
│  FloodModel, AllocationCClueLike, MangroveModel, ...     │
│  → only knows math, geometry and time                    │
├──────────────────────────────────────────────────────────┤
│  Infrastructure Layer  (ModelExecutor)                   │
│  CoastalRasterExecutor, LUCCVectorExecutor, ...          │
│  → only knows URIs, MinIO, column_map, parameters        │
├──────────────────────────────────────────────────────────┤
│  Core modules                                            │
│  dissmodel.core      — Environment, SpatialModel         │
│  dissmodel.geo       — RasterBackend, neighborhoods      │
│  dissmodel.executor  — ModelExecutor ABC, ExperimentRecord│
│  dissmodel.io        — load_dataset / save_dataset       │
│  dissmodel.visualization — Map, RasterMap, Chart         │
└──────────────────────────────────────────────────────────┘
```

"A ciência não deve ser reescrita para ir para a produção."

---

## 🚀 Quick Start

### Writing a model

```python
# my_model.py
from dissmodel.core import SpatialModel, Environment

class ForestFireModel(SpatialModel):

    def setup(self, prob_spread=0.3):
        self.prob_spread = prob_spread

    def execute(self):
        # Called every step by Salabim — only math here, no I/O
        burning = self.gdf["state"] == "burning"
        ...

env = Environment(end_time=50)
ForestFireModel(gdf=gdf, prob_spread=0.4)
env.run()
```

### Writing an executor

```python
# my_executor.py
from dissmodel.executor     import ExperimentRecord, ModelExecutor
from dissmodel.executor.cli import run_cli
from dissmodel.io           import load_dataset, save_dataset

class ForestFireExecutor(ModelExecutor):
    name = "forest_fire"

    def load(self, record: ExperimentRecord):
        gdf, checksum = load_dataset(record.source.uri)
        record.source.checksum = checksum
        return gdf

    def run(self, record: ExperimentRecord):
        from dissmodel.core import Environment
        gdf     = self.load(record)
        env     = Environment(end_time=record.parameters.get("end_time", 50))
        ForestFireModel(gdf=gdf, **record.parameters)
        env.run()
        return gdf

    def save(self, result, record: ExperimentRecord) -> ExperimentRecord:
        uri      = record.output_path or "output.gpkg"
        checksum = save_dataset(result, uri)
        record.output_path   = uri
        record.output_sha256 = checksum
        record.status        = "completed"
        return record

if __name__ == "__main__":
    run_cli(ForestFireExecutor)
```

### Running via CLI

```bash
# Run
python my_executor.py run \
  --input  data/forest.gpkg \
  --output data/result.gpkg \
  --param  end_time=50 \
  --toml   model.toml

# Validate data contract without running
python my_executor.py validate --input data/forest.gpkg

# Show resolved parameters
python my_executor.py show --toml model.toml
```

### Running via Platform API

```bash
curl -X POST http://localhost:8000/submit_job \
  -H "X-API-Key: chave-sergio" \
  -H "Content-Type: application/json" \
  -d '{"model_name": "forest_fire", "input_dataset": "s3://inputs/forest.gpkg"}'
```

---

## 📦 ExperimentRecord

Every run produces an immutable provenance record:

```json
{
  "experiment_id":  "abc123",
  "model_commit":   "a3f9c12",
  "code_version":   "0.1.5",
  "resolved_spec":  { "...TOML snapshot..." },
  "source":         { "uri": "s3://...", "checksum": "e3b0c44..." },
  "artifacts":      { "output": "sha256...", "profiling": "sha256..." },
  "metrics":        { "time_run_sec": 2.15, "time_total_sec": 2.34 },
  "status":         "completed"
}
```

Reproduce any past experiment exactly:

```bash
curl -X POST http://localhost:8000/experiments/abc123/reproduce \
  -H "X-API-Key: chave-sergio"
```

---

## 📊 Performance Telemetry

Every platform run generates a `profiling_{id}.md` alongside the output:

| Phase | Time (s) | % |
|-------|----------|---|
| Validate | 0.005 | 0.2% |
| Run | 2.150 | 92.1% |
| Save | 0.180 | 7.7% |
| **Total** | **2.335** | **100%** |

---

## 📖 Examples & Ecosystem
DisSModel is a core framework. To maintain a clean and specialized environment, all simulation models and implementation examples are hosted in separate repositories within the LambdaGeo ecosystem.
### 🧩 Specialized Model Libraries
Download and install these libraries to get ready-to-use models:
 * **DisSModel-CA** — Classic Cellular Automata (Game of Life, Forest Fire, Growth, etc.).
 * **DisSModel-SysDyn** — System Dynamics (SIR, Predator-Prey, Lorenz Attractor).
 * **coastal-dynamics** — Specialized models for coastal flooding and mangrove succession.

### 🚀 Implementation Templates
Since DisSModel uses the **Executor Pattern**, you can find implementation templates for CLI and API integration in the documentation or by exploring the repositories above. Each repository demonstrates how to:
 1. **Define a Model**: Using SpatialModel and Environment.
 2. **Wrap an Executor**: Using ModelExecutor for I/O and provenance.
 3. **Deploy**: Running via CLI or the DisSModel Platform.
 





Documentation: [https://lambdageo.github.io/dissmodel/](https://lambdageo.github.io/dissmodel/)

---

## 📦 Installation

```bash
pip install dissmodel

# Latest development version
pip install "git+https://github.com/LambdaGeo/dissmodel.git@main"
```

---

## 🎓 Citation

```
Costa, S. & Santos Junior, N. (2026). DisSModel: A Discrete Spatial Modeling
Framework for Python. LambdaGeo, Federal University of Maranhão (UFMA).
```

---

## ⚖️ License

MIT © [LambdaGeo — UFMA](https://github.com/LambdaGeo)
