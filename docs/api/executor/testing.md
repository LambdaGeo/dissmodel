# Testing

The `dissmodel.executor.testing` module provides `ExecutorTestHarness`, a
contract validator for `ModelExecutor` subclasses. It is designed to run
in Jupyter before opening a PR — the same checks are reused in CI via pytest,
so a passing notebook guarantees a passing pipeline.

---

## Contract tests

`run_contract_tests()` runs structural checks without loading any data:

```python
from dissmodel.executor.testing import ExecutorTestHarness
from my_package.my_executor import MyExecutor

harness = ExecutorTestHarness(MyExecutor)
harness.run_contract_tests()
```

```
ExecutorTestHarness — MyExecutor
────────────────────────────────────────────────────
  ✅ name attribute exists
  ✅ name is a non-empty string
  ✅ name has no whitespace
  ✅ load() is implemented
  ✅ run() is implemented
  ✅ save() is implemented
  ✅ run() signature is correct
  ✅ save() signature is correct
────────────────────────────────────────────────────
  All 8 checks passed ✅
```

The `run() signature is correct` check validates that the executor uses the
`0.4.0` signature `run(self, data, record)`. Executors still using the old
`run(self, record)` form will fail here with a clear message:

```
❌ run() signature is correct: run() must accept exactly two parameters
   (data, record), got ['record']. Did you update to the 0.4.0 signature?
```

---

## Full lifecycle test

`run_with_sample_data()` executes `validate → load → run(data, record) → save`
with a real record. Use it for smoke testing after migrating a model:

```python
from dissmodel.executor.schemas import DataSource, ExperimentRecord

record = ExperimentRecord(
    model_name   = "my_model",
    model_commit = "local-test",
    code_version = "dev",
    source       = DataSource(type="local", uri="data/sample.gpkg"),
)

harness.run_with_sample_data(record)
```

```
▶ Running my_model...
  validate()...
  load()...
  run()...
  save()...
  ✅ Cycle OK — status=completed  sha256=deadbeef123...
```

If no record is provided, the harness creates a minimal synthetic one:

```python
harness.run_with_sample_data()   # uses _minimal_record()
```

---

## Using in pytest

```python
# tests/test_contract.py
from dissmodel.executor.testing import ExecutorTestHarness
from my_package.my_executor import MyExecutor

def test_contract():
    assert ExecutorTestHarness(MyExecutor).run_contract_tests() is True
```

---

## API Reference

::: dissmodel.executor.testing.ExecutorTestHarness
