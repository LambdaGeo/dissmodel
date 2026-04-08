
# DisSModel

**Discrete Spatial Modeling framework for Python**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![PyPI version](https://badge.fury.io/py/dissmodel.svg)](https://pypi.org/project/dissmodel/)

DisSModel is a modular Python framework for spatially explicit dynamic modeling. Developed by the [LambdaGeo](https://github.com/LambdaGeo) group at the Federal University of Maranhão (UFMA), it provides a unified environment for building **Cellular Automata (CA)** and **System Dynamics (SysDyn)** models on top of the modern Python geospatial ecosystem.

---

## 🌟 Key Features

- **Hybrid Modeling Engine** — Unified API for Cellular Automata (Raster/Vector) and System Dynamics.
- **Storage-Agnostic I/O** — Seamlessly switch between local files and **MinIO/S3** buckets.
- **Performance Profiling** — Automatic generation of execution metrics and Markdown telemetry reports.
- **Experiment Tracking** — Every run generates an `ExperimentRecord` (JSON) with SHA256 integrity checks.
- **Reactive UI** — Automatic Streamlit widget generation and live Matplotlib plotting.

---

## 🏗 Project Architecture

DisSModel is organized into decoupled modules to ensure flexibility:

- **`dissmodel.core`**: Simulation lifecycle and environment control (`Environment`, `Model`).
- **`dissmodel.geo`**: Spatial backends (Raster/Vector) and neighborhood strategies.
- **`dissmodel.executor`**: Command-line interface and standardized execution schemas.
- **`dissmodel.io`**: Generic I/O layer handling local paths and S3 protocols.
- **`dissmodel.visualization`**: Observer-based charts, maps, and interactive widgets.

---

## 🚀 Execution Modes

### 1. Command Line (CLI)
Run simulations with built-in experiment tracking and overwrite protection. The CLI automatically appends short IDs to results for better traceability.

```bash
# Example: Running Forest Fire from the project root
python -m examples.cli.ca.ca_fire_model run \
  --input data/forest.tif \
  --output ./results/ \
  --param end_time=50
```

### 2. Jupyter Notebooks
Ideal for researchers. Use the integrated I/O utils to fetch data directly from MinIO or local storage.

```python
from dissmodel.io._utils import read_text
import json

# Load metadata from a previous experiment
content = read_text("s3://bucket/experiments/9c218c92.record.json")
record = json.loads(content)
print(f"Metrics: {record['metrics']}")
```

### 3. Streamlit Apps
DisSModel can automatically generate sidebar widgets from your model's type annotations.

```bash
streamlit run examples/streamlit/ca_all.py
```

---

## 📊 Performance Telemetry

Every simulation executed via the standard pipeline generates a `profiling_{id}.md` report to help identify bottlenecks:

| Phase | Time (seconds) | % of Total |
|---|---|---|
| **Validate** | 0.005 | 0.2% |
| **Run** | 2.150 | 92.1% |
| **Save** | 0.180 | 7.7% |
| **Total** | **2.335** | **100%** |

---

## 📖 Examples & Reference Models

Full implementations are available in the [`examples/`](examples/) directory:
- **CA**: Game of Life, Forest Fire (Probabilistic), Snowfall, Growth.
- **System Dynamics**: SIR, Predator-Prey, Lorenz Attractor, Coffee Cooling.

Documentation: [https://lambdageo.github.io/dissmodel/](https://lambdageo.github.io/dissmodel/)

---

## 🎓 Citation

If you use DisSModel in your research, please cite:

```text
Costa, S. & Santos Junior, N. (2026). DisSModel: A Discrete Spatial Modeling
Framework for Python. LambdaGeo, Federal University of Maranhão (UFMA).
```

---

## ⚖️ License

MIT © [LambdaGeo — UFMA](https://github.com/LambdaGeo)
