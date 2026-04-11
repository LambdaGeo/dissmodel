from __future__ import annotations

from pathlib import Path
from types  import SimpleNamespace

import pytest

from dissmodel.executor.cli import _parse_params, _apply_output_path_intelligence


# ── _parse_params ─────────────────────────────────────────────────────────────

class TestParseParams:

    def test_empty_input_returns_empty_dict(self):
        assert _parse_params(None) == {}
        assert _parse_params([])   == {}

    def test_integer_values_are_cast(self):
        result = _parse_params(["steps=10", "start=0"])
        assert result["steps"] == 10
        assert result["start"] == 0
        assert isinstance(result["steps"], int)

    def test_float_values_are_cast(self):
        result = _parse_params(["rate=0.5", "threshold=1.0"])
        assert result["rate"] == 0.5
        assert isinstance(result["rate"], float)

    def test_integer_takes_precedence_over_float(self):
        """'10' should become int 10, not float 10.0."""
        result = _parse_params(["n=10"])
        assert isinstance(result["n"], int)

    def test_boolean_true_is_cast(self):
        result = _parse_params(["interactive=true", "verbose=True"])
        assert result["interactive"] is True
        assert result["verbose"] is True

    def test_boolean_false_is_cast(self):
        result = _parse_params(["interactive=false", "debug=False"])
        assert result["interactive"] is False
        assert result["debug"] is False

    def test_plain_string_stays_as_string(self):
        result = _parse_params(["crs=EPSG:4326", "label=test"])
        assert result["crs"] == "EPSG:4326"
        assert result["label"] == "test"

    def test_multiple_equals_signs_partition_on_first(self):
        """KEY=a=b should map key → 'a=b'."""
        result = _parse_params(["uri=s3://bucket/key=value"])
        assert result["uri"] == "s3://bucket/key=value"

    def test_duplicate_keys_last_wins(self):
        result = _parse_params(["rate=0.1", "rate=0.9"])
        assert result["rate"] == 0.9


# ── _apply_output_path_intelligence ──────────────────────────────────────────

class TestOutputPathIntelligence:

    def _run(self, make_record, output_path: str):
        record          = make_record()
        record.output_path = output_path
        args            = SimpleNamespace(output=output_path)
        _apply_output_path_intelligence(record, args)
        return record, args

    # Scenario A — directory paths

    def test_trailing_slash_generates_filename(self, make_record):
        record, _ = self._run(make_record, "outputs/")
        exp_id = record.experiment_id[:8]
        assert record.output_path == f"outputs/simulacao_{exp_id}.tif"

    def test_backslash_generates_filename(self, make_record):
        record, _ = self._run(make_record, "outputs\\")
        exp_id = record.experiment_id[:8]
        assert record.output_path == f"outputs\\simulacao_{exp_id}.tif"

    def test_existing_directory_generates_filename(self, make_record, tmp_path):
        record          = make_record()
        record.output_path = str(tmp_path)   # tmp_path is a real existing directory
        args            = SimpleNamespace(output=str(tmp_path))
        _apply_output_path_intelligence(record, args)
        exp_id = record.experiment_id[:8]
        assert record.output_path == str(tmp_path / f"simulacao_{exp_id}.tif")

    # Scenario B — file paths without experiment ID

    def test_file_without_id_gets_id_injected(self, make_record):
        record, _ = self._run(make_record, "outputs/result.tif")
        exp_id = record.experiment_id[:8]
        assert record.output_path == f"outputs/result_{exp_id}.tif"

    def test_extension_is_preserved_after_id_injection(self, make_record):
        record, _ = self._run(make_record, "outputs/result.gpkg")
        assert record.output_path.endswith(".gpkg")

    def test_file_already_containing_id_is_not_modified(self, make_record):
        record     = make_record()
        exp_id     = record.experiment_id[:8]
        original   = f"outputs/result_{exp_id}.tif"
        record.output_path = original
        args       = SimpleNamespace(output=original)
        _apply_output_path_intelligence(record, args)
        assert record.output_path == original

    # args.output synchronisation

    def test_args_output_is_synced_after_scenario_a(self, make_record):
        record, args = self._run(make_record, "outputs/")
        assert args.output == record.output_path

    def test_args_output_is_synced_after_scenario_b(self, make_record):
        record, args = self._run(make_record, "outputs/result.tif")
        assert args.output == record.output_path

    # No-op when output_path is not set

    def test_no_output_path_is_noop(self, make_record):
        record          = make_record()
        record.output_path = None
        args            = SimpleNamespace(output=None)
        _apply_output_path_intelligence(record, args)
        assert record.output_path is None
        assert args.output is None
