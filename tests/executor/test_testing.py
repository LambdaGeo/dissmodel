from __future__ import annotations

import pytest

from dissmodel.executor.testing        import ExecutorTestHarness
from dissmodel.executor.model_executor import ModelExecutor
from tests.executor.conftest import MinimalExecutor


# ── Harness passes on a valid executor ───────────────────────────────────────

class TestHarnessHappyPath:

    def test_contract_tests_pass_for_valid_executor(self):
        assert ExecutorTestHarness(MinimalExecutor).run_contract_tests() is True

    def test_sample_data_run_passes_for_valid_executor(self, make_record):
        harness = ExecutorTestHarness(MinimalExecutor)
        assert harness.run_with_sample_data(make_record()) is True

    def test_sample_data_uses_minimal_record_when_none_given(self):
        # MinimalExecutor.save does not set output_sha256, so run_with_sample_data
        # returns False on the sha256 check — but it must not raise.
        harness = ExecutorTestHarness(MinimalExecutor)
        result  = harness.run_with_sample_data(None)
        assert isinstance(result, bool)


# ── name checks ───────────────────────────────────────────────────────────────

class TestHarnessNameChecks:

    def test_fails_when_name_has_whitespace(self):
        class _SpaceName(MinimalExecutor):
            name = "bad name"
        assert ExecutorTestHarness(_SpaceName).run_contract_tests() is False

    def test_passes_when_name_uses_underscores(self):
        class _GoodName(MinimalExecutor):
            name = "_test_good_name"
        assert ExecutorTestHarness(_GoodName).run_contract_tests() is True


# ── run() signature check ─────────────────────────────────────────────────────

class TestHarnessRunSignature:

    def test_fails_when_run_uses_old_single_param_signature(self):
        """run(self, record) is the pre-0.4.0 signature — harness must reject it."""
        class _OldSig(ModelExecutor):
            name = "_test_old_sig_harness"
            def load(self, record): return None
            def run(self, record): return None          # old — missing data
            def save(self, result, record):
                record.status = "completed"
                return record

        assert ExecutorTestHarness(_OldSig).run_contract_tests() is False

    def test_fails_when_run_has_no_params(self):
        class _NoParms(ModelExecutor):
            name = "_test_no_params"
            def load(self, record): return None
            def run(self): return None                  # wrong
            def save(self, result, record):
                record.status = "completed"
                return record

        assert ExecutorTestHarness(_NoParms).run_contract_tests() is False

    def test_passes_when_run_uses_correct_two_param_signature(self):
        class _CorrectSig(ModelExecutor):
            name = "_test_correct_sig"
            def load(self, record): return None
            def run(self, data, record): return None    # correct
            def save(self, result, record):
                record.status = "completed"
                return record

        assert ExecutorTestHarness(_CorrectSig).run_contract_tests() is True


# ── save() signature check ────────────────────────────────────────────────────

class TestHarnessSaveSignature:

    def test_fails_when_save_has_wrong_param_count(self):
        class _BadSave(ModelExecutor):
            name = "_test_bad_save"
            def load(self, record): return None
            def run(self, data, record): return None
            def save(self, record):                     # missing result param
                record.status = "completed"
                return record

        assert ExecutorTestHarness(_BadSave).run_contract_tests() is False


# ── run_with_sample_data failure paths ───────────────────────────────────────

class TestHarnessSampleDataFailures:

    def test_returns_false_when_validate_raises(self, make_record):
        class _FailValidate(MinimalExecutor):
            name = "_test_h_fail_validate"
            def validate(self, record):
                raise ValueError("bad config")

        assert ExecutorTestHarness(_FailValidate).run_with_sample_data(make_record()) is False

    def test_returns_false_when_load_raises(self, make_record):
        class _FailLoad(MinimalExecutor):
            name = "_test_h_fail_load"
            def load(self, record):
                raise RuntimeError("file not found")

        assert ExecutorTestHarness(_FailLoad).run_with_sample_data(make_record()) is False

    def test_returns_false_when_run_raises(self, make_record):
        class _FailRun(MinimalExecutor):
            name = "_test_h_fail_run"
            def run(self, data, record):
                raise RuntimeError("simulation crashed")

        assert ExecutorTestHarness(_FailRun).run_with_sample_data(make_record()) is False

    def test_returns_false_when_save_raises(self, make_record):
        class _FailSave(MinimalExecutor):
            name = "_test_h_fail_save"
            def save(self, result, record):
                raise IOError("disk full")

        assert ExecutorTestHarness(_FailSave).run_with_sample_data(make_record()) is False

    def test_returns_false_when_status_not_completed(self, make_record):
        class _BadStatus(MinimalExecutor):
            name = "_test_h_bad_status"
            def save(self, result, record):
                record.status        = "running"   # forgot to set completed
                record.output_sha256 = "abc123"
                return record

        assert ExecutorTestHarness(_BadStatus).run_with_sample_data(make_record()) is False

    def test_returns_false_when_output_sha256_not_set(self, make_record):
        class _NoSha(MinimalExecutor):
            name = "_test_h_no_sha"
            def save(self, result, record):
                record.status        = "completed"
                record.output_sha256 = ""           # empty — harness must catch this
                return record

        assert ExecutorTestHarness(_NoSha).run_with_sample_data(make_record()) is False

    def test_not_implemented_error_returns_false_gracefully(self, make_record):
        class _NotImpl(MinimalExecutor):
            name = "_test_h_not_impl"
            def run(self, data, record):
                raise NotImplementedError

        assert ExecutorTestHarness(_NotImpl).run_with_sample_data(make_record()) is False


# ── load → run data passthrough (via harness) ─────────────────────────────────

class TestHarnessDataPassthrough:

    def test_run_receives_data_from_load(self, make_record):
        """
        run_with_sample_data must pass the return value of load() into run().
        Verified by an executor that asserts data identity inside run().
        """
        sentinel = object()

        class _PassthroughExecutor(MinimalExecutor):
            name = "_test_h_passthrough"

            def load(self, record):
                return sentinel

            def run(self, data, record):
                assert data is sentinel, (
                    f"run() received {data!r} — expected the sentinel from load()"
                )
                return super().run(data, record)

        harness = ExecutorTestHarness(_PassthroughExecutor)
        # run_with_sample_data will call load then run(data, record)
        # if the harness still calls run(record) directly, AssertionError is raised
        # and run_with_sample_data returns False
        assert harness.run_with_sample_data(make_record()) is True
