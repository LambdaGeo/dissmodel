from __future__ import annotations

import pytest

from dissmodel.executor.registry       import ExecutorRegistry
from dissmodel.executor.model_executor import ModelExecutor


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_executor(executor_name: str) -> type[ModelExecutor]:
    """Dynamically create a minimal named executor subclass."""

    class _DynExecutor(ModelExecutor):
        name = executor_name

        def load(self, record):
            return None

        def run(self, data, record):
            return None

        def save(self, result, record):
            record.status = "completed"
            return record

    _DynExecutor.__name__     = f"DynExecutor_{executor_name}"
    _DynExecutor.__qualname__ = _DynExecutor.__name__
    return _DynExecutor


# ── Auto-registration via __init_subclass__ ───────────────────────────────────

class TestAutoRegistration:

    def test_subclass_with_name_is_registered_automatically(self):
        cls = _make_executor("_reg_auto_test")
        assert "_reg_auto_test" in ExecutorRegistry.list()

    def test_registered_class_is_the_same_object(self):
        cls = _make_executor("_reg_same_object")
        assert ExecutorRegistry.get("_reg_same_object") is cls

    def test_subclass_without_name_is_not_registered(self):
        before = set(ExecutorRegistry.list())

        class _NoName(ModelExecutor):
            # no `name` class attribute
            def load(self, record): return None
            def run(self, data, record): return None
            def save(self, result, record):
                record.status = "completed"
                return record

        after = set(ExecutorRegistry.list())
        assert before == after, "Unnamed subclass should not appear in the registry"


# ── get() ─────────────────────────────────────────────────────────────────────

class TestRegistryGet:

    def test_get_returns_registered_class(self):
        cls = _make_executor("_reg_get_test")
        assert ExecutorRegistry.get("_reg_get_test") is cls

    def test_get_unknown_name_raises_key_error(self):
        with pytest.raises(KeyError, match="not registered"):
            ExecutorRegistry.get("this_name_does_not_exist")

    def test_key_error_message_lists_available_executors(self):
        _make_executor("_reg_available_hint")
        with pytest.raises(KeyError) as exc_info:
            ExecutorRegistry.get("nonexistent")
        assert "_reg_available_hint" in str(exc_info.value)


# ── list() ────────────────────────────────────────────────────────────────────

class TestRegistryList:

    def test_list_returns_list_of_strings(self):
        result = ExecutorRegistry.list()
        assert isinstance(result, list)
        assert all(isinstance(n, str) for n in result)

    def test_list_includes_newly_registered_executor(self):
        _make_executor("_reg_list_test")
        assert "_reg_list_test" in ExecutorRegistry.list()

    def test_list_does_not_return_registry_internals(self):
        names = ExecutorRegistry.list()
        assert "_executors" not in names


# ── register() ───────────────────────────────────────────────────────────────

class TestRegistryRegister:

    def test_re_registering_same_name_overwrites(self):
        """Last writer wins — consistent with Python class redefinition semantics."""
        cls_a = _make_executor("_reg_overwrite")
        cls_b = _make_executor("_reg_overwrite")
        assert ExecutorRegistry.get("_reg_overwrite") is cls_b
