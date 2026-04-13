# Executor

The `dissmodel.executor` module provides the standardised interface for packaging,
deploying, and reproducing simulations. It separates scientific logic from
execution infrastructure, so the same model code runs locally via CLI or
remotely via the platform API without modification.

The module exposes three building blocks:

| Component | Description |
|-----------|-------------|
| `ModelExecutor` | Abstract base class defining the four-phase lifecycle |
| `ExecutorRegistry` | Central registry mapping model names to executor classes |
| `execute_lifecycle` | Canonical orchestration function used by CLI and platform |

---

## Lifecycle

Every executor follows the same four-phase lifecycle, orchestrated by
`execute_lifecycle`:

```
validate(record)            # stateless pre-flight checks — no I/O
data = load(record)         # resolve URI, apply column/band maps, return data
result = run(data, record)  # simulation — no I/O here
record = save(result, record)
```

Each phase is timed independently. Timings are written to `record.metrics`
automatically (`time_validate_sec`, `time_load_sec`, `time_run_sec`,
`time_save_sec`, `time_total_sec`).

---

## Minimal implementation

```python
import geopandas as gpd
from dissmodel.executor import ModelExecutor, ExperimentRecord
from dissmodel.executor.cli import run_cli
from dissmodel.io import load_dataset, save_dataset


class MyExecutor(ModelExecutor):
    name = "my_model"

    def load(self, record: ExperimentRecord) -> gpd.GeoDataFrame:
        gdf, checksum = load_dataset(record.source.uri)
        record.source.checksum = checksum
        return gdf

    def run(self, data: gpd.GeoDataFrame, record: ExperimentRecord) -> gpd.GeoDataFrame:
        # data is already loaded — no I/O here
        params = record.parameters
        # ... simulation logic ...
        return data

    def save(self, result, record: ExperimentRecord) -> ExperimentRecord:
        uri = record.output_path or "output.gpkg"
        checksum = save_dataset(result, uri)
        record.output_path   = uri
        record.output_sha256 = checksum
        record.status        = "completed"
        return record


if __name__ == "__main__":
    run_cli(MyExecutor)
```

---

## Auto-registration

Subclasses of `ModelExecutor` that define a `name` class attribute are
registered automatically in `ExecutorRegistry` via Python's
`__init_subclass__`. No boilerplate is required:

```python
from dissmodel.executor import ExecutorRegistry

ExecutorRegistry.list()          # ["my_model", ...]
ExecutorRegistry.get("my_model") # → MyExecutor class
```

The `name` attribute is also the key used in the TOML model registry:

```toml
[model]
class   = "my_model"
package = "my_package"
```

---

## execute_lifecycle

`execute_lifecycle` is the single source of truth for orchestration. It is
used by both `dissmodel/executor/cli.py` and the platform `job_runner.py`,
ensuring behavioural parity without code duplication.

```python
from dissmodel.executor import execute_lifecycle

executor = MyExecutor()
record, timings = execute_lifecycle(executor, record)

print(timings)
# {
#   "time_validate_sec": 0.0,
#   "time_load_sec": 1.243,
#   "time_run_sec": 0.872,
#   "time_save_sec": 0.004,
#   "time_total_sec": 2.119
# }
```

---

## API Reference

::: dissmodel.executor.model_executor.ModelExecutor

::: dissmodel.executor.registry.ExecutorRegistry

::: dissmodel.executor.runner.execute_lifecycle
