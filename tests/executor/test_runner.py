from __future__ import annotations

import pytest

from dissmodel.executor.runner import execute_lifecycle
from tests.executor.conftest import (
    MinimalExecutor,
    OrderTrackingExecutor,
    FailingValidateExecutor,
    FailingLoadExecutor,
)

EXPECTED_TIMING_KEYS = {
    "time_validate_sec",
    "time_load_sec",
    "time_run_sec",
    "time_save_sec",
    "time_total_sec",
}


# ── Happy path ────────────────────────────────────────────────────────────────

class TestExecuteLifecycleHappyPath:

    def test_returns_completed_record(self, make_record):
        record, _ = execute_lifecycle(MinimalExecutor(), make_record())
        assert record.status == "completed"

    def test_returns_timings_dict_with_all_keys(self, make_record):
        _, timings = execute_lifecycle(MinimalExecutor(), make_record())
        assert set(timings.keys()) == EXPECTED_TIMING_KEYS

    def test_all_timing_values_are_non_negative(self, make_record):
        _, timings = execute_lifecycle(MinimalExecutor(), make_record())
        for key, value in timings.items():
            assert value >= 0, f"{key} should be >= 0, got {value}"

    def test_total_equals_sum_of_phases(self, make_record):
        _, timings = execute_lifecycle(MinimalExecutor(), make_record())
        expected = round(
            timings["time_validate_sec"]
            + timings["time_load_sec"]
            + timings["time_run_sec"]
            + timings["time_save_sec"],
            3,
        )
        assert timings["time_total_sec"] == expected

    def test_timings_are_written_to_record_metrics(self, make_record):
        record, timings = execute_lifecycle(MinimalExecutor(), make_record())
        for key in EXPECTED_TIMING_KEYS:
            assert key in record.metrics
            assert record.metrics[key] == timings[key]

    def test_record_output_path_is_populated(self, make_record):
        record, _ = execute_lifecycle(MinimalExecutor(), make_record())
        assert record.output_path == "output/test.gpkg"

    def test_timings_are_rounded_to_three_decimal_places(self, make_record):
        _, timings = execute_lifecycle(MinimalExecutor(), make_record())
        for key, value in timings.items():
            # round(x, 3) == x  iff  x has at most 3 decimal places
            assert round(value, 3) == value, f"{key} has more than 3 decimal places"


# ── Phase ordering ────────────────────────────────────────────────────────────

class TestExecuteLifecycleOrder:

    def test_phases_run_in_correct_order(self, make_record):
        executor = OrderTrackingExecutor()
        execute_lifecycle(executor, make_record())
        assert executor.calls == ["validate", "load", "run", "save"]

    def test_load_output_is_passed_to_run(self, make_record):
        """
        run() must receive the exact object returned by load(), not record.
        Verified by MinimalExecutor.run asserting data == {"loaded": True}.
        """
        class _DataPassthroughExecutor(MinimalExecutor):
            name = "_test_data_passthrough"

            def run(self, data, record):
                assert data == {"loaded": True}, (
                    f"run() received {data!r} instead of load() return value"
                )
                return super().run(data, record)

        execute_lifecycle(_DataPassthroughExecutor(), make_record())

    def test_run_result_is_passed_to_save(self, make_record):
        class _SaveCheckExecutor(MinimalExecutor):
            name = "_test_save_check"

            def save(self, result, record):
                assert result == {"result": True, "input": {"loaded": True}}, (
                    f"save() received unexpected result: {result!r}"
                )
                return super().save(result, record)

        execute_lifecycle(_SaveCheckExecutor(), make_record())


# ── Failure propagation ───────────────────────────────────────────────────────

class TestExecuteLifecycleFailures:

    def test_validate_error_propagates(self, make_record):
        with pytest.raises(ValueError, match="validation failed intentionally"):
            execute_lifecycle(FailingValidateExecutor(), make_record())

    def test_load_not_called_when_validate_fails(self, make_record):
        """load() must not be called if validate() raises."""
        calls = []

        class _TrackingFailValidate(FailingValidateExecutor):
            name = "_test_track_fail_validate"

            def load(self, record):
                calls.append("load")
                return None

        with pytest.raises(ValueError):
            execute_lifecycle(_TrackingFailValidate(), make_record())

        assert "load" not in calls

    def test_load_error_propagates(self, make_record):
        with pytest.raises(RuntimeError, match="load failed intentionally"):
            execute_lifecycle(FailingLoadExecutor(), make_record())

    def test_run_not_called_when_load_fails(self, make_record):
        """run() must not be called if load() raises."""
        calls = []

        class _TrackingFailLoad(FailingLoadExecutor):
            name = "_test_track_fail_load"

            def run(self, data, record):
                calls.append("run")
                return None

        with pytest.raises(RuntimeError):
            execute_lifecycle(_TrackingFailLoad(), make_record())

        assert "run" not in calls


# ── Validate is optional ──────────────────────────────────────────────────────

class TestExecuteLifecycleValidateDefault:

    def test_default_validate_is_noop(self, make_record):
        """
        ModelExecutor.validate() is a no-op by default.
        An executor that does not override it must still complete successfully.
        """
        class _NoValidateExecutor(MinimalExecutor):
            name = "_test_no_validate"
            # validate not overridden — inherits the no-op default

        record, _ = execute_lifecycle(_NoValidateExecutor(), make_record())
        assert record.status == "completed"
