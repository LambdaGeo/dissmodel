# Getting Started

## Installation

```bash
pip install dissmodel
```

For development mode (including examples and tests):

```bash
git clone [https://github.com/lambdageo/dissmodel](https://github.com/lambdageo/dissmodel)
cd dissmodel
pip install -e .
```

---

## Instantiation Order

The `Environment` is the heart of the simulation. It must always be created **before** any model.

```text
Environment  →  Model  →  Visualization  →  env.run()
     ↑             ↑            ↑                ↑
  Step 1        Step 2        Step 3           Step 4
```

---

## Execution Modes

DisSModel 0.4.0 supports three main ways to interact with your models:

### 1. Command Line (CLI)
Standardized via the `dissmodel.executor`. Best for batch experiments and experiment tracking.

```bash
python -m examples.cli.ca.ca_fire_model run --param end_time=50
```

### 2. Jupyter Notebooks
Best for teaching and incremental analysis. DisSModel renders visualizations inline automatically. See `examples/notebooks/`.

### 3. Streamlit Apps
Reactive web interfaces with zero boilerplate. Parameters are automatically mapped to sidebar widgets.

```bash
streamlit run examples/streamlit/ca_all.py
```

---

## Storage & Reproducibility
Since version 0.2.0, DisSModel can read and write directly to **MinIO/S3**. Every execution via the standard CLI generates a `record.json` and a profiling report, ensuring your science is always traceable.