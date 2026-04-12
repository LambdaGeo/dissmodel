from __future__ import annotations

import pytest

from dissmodel.executor.schemas import DataSource, ExperimentRecord
from dissmodel.executor.model_executor import ModelExecutor


# ── Minimal valid record ──────────────────────────────────────────────────────

@pytest.fixture
def make_record():
    """
    Factory fixture for ExperimentRecord.
    Accepts keyword overrides for any field.
    """
    def _factory(**kwargs) -> ExperimentRecord:
        defaults = dict(
            model_name    = "test_model",
            model_commit  = "abc123",
            code_version  = "0.4.0",
            source        = DataSource(type="local", uri="data/test.gpkg"),
        )
        defaults.update(kwargs)
        return ExperimentRecord(**defaults)
    return _factory


# ── Reusable fake executors ───────────────────────────────────────────────────

class MinimalExecutor(ModelExecutor):
    """Simplest valid executor — returns a fixed payload through all phases."""

    name = "_test_minimal"

    def load(self, record: ExperimentRecord):
        return {"loaded": True}

    def run(self, data, record: ExperimentRecord):
        return {"result": True, "input": data}

    def save(self, result, record: ExperimentRecord) -> ExperimentRecord:
        record.output_path   = "output/test.gpkg"
        record.output_sha256 = "deadbeef"
        record.status        = "completed"
        return record


class OrderTrackingExecutor(ModelExecutor):
    """
    Records every lifecycle call in self.calls.
    Used to assert that execute_lifecycle respects phase order.
    """

    name = "_test_order_tracking"

    def __init__(self):
        self.calls: list[str] = []

    def validate(self, record: ExperimentRecord) -> None:
        self.calls.append("validate")

    def load(self, record: ExperimentRecord):
        self.calls.append("load")
        return "data"

    def run(self, data, record: ExperimentRecord):
        self.calls.append("run")
        return "result"

    def save(self, result, record: ExperimentRecord) -> ExperimentRecord:
        self.calls.append("save")
        record.status = "completed"
        return record


class FailingValidateExecutor(ModelExecutor):
    """Raises ValueError in validate — lifecycle must not proceed."""

    name = "_test_failing_validate"

    def validate(self, record: ExperimentRecord) -> None:
        raise ValueError("validation failed intentionally")

    def load(self, record: ExperimentRecord):
        return None  # must never be called

    def run(self, data, record: ExperimentRecord):
        return None  # must never be called

    def save(self, result, record: ExperimentRecord) -> ExperimentRecord:
        record.status = "completed"
        return record


class FailingLoadExecutor(ModelExecutor):
    """Raises RuntimeError in load — run and save must not be called."""

    name = "_test_failing_load"

    def load(self, record: ExperimentRecord):
        raise RuntimeError("load failed intentionally")

    def run(self, data, record: ExperimentRecord):
        return None  # must never be called

    def save(self, result, record: ExperimentRecord) -> ExperimentRecord:
        record.status = "completed"
        return record


@pytest.fixture
def minimal_executor():
    return MinimalExecutor()


@pytest.fixture
def order_executor():
    return OrderTrackingExecutor()


# ── Registry isolation ────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _isolate_registry():
    """
    Snapshot and restore ExecutorRegistry._executors around every test.

    Executors defined inside test functions register themselves via
    __init_subclass__ and would otherwise accumulate across the session,
    polluting list() output and potentially causing name collisions.
    """
    from dissmodel.executor.registry import ExecutorRegistry
    snapshot = dict(ExecutorRegistry._executors)
    yield
    ExecutorRegistry._executors = snapshot
