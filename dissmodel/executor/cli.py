from __future__ import annotations

import argparse
import importlib
import sys
import tomllib
from pathlib import Path


# ── Parameter helpers ─────────────────────────────────────────────────────────

def _parse_params(param_list: list[str] | None) -> dict:
    """Parse KEY=VALUE strings into a typed dict."""
    params = {}
    for item in param_list or []:
        key, _, raw = item.partition("=")
        for cast in (int, float):
            try:
                params[key] = cast(raw)
                break
            except ValueError:
                pass
        else:
            if raw.lower() in ("true", "false"):
                params[key] = raw.lower() == "true"
            else:
                params[key] = raw
    return params


def _load_local_params() -> dict:
    """
    Load default parameters from model.toml in the current directory.
    Returns empty dict if file not found.
    """
    path = Path("model.toml")
    if not path.exists():
        return {}
    with open(path, "rb") as f:
        config = tomllib.load(f)
    return config.get("model", {}).get("parameters", {})


# ── Record factory ────────────────────────────────────────────────────────────

def _build_record(args):
    from .schemas import DataSource, ExperimentRecord

    # TOML defaults merged with CLI overrides — CLI wins
    params = {**_load_local_params(), **_parse_params(args.param)}

    record = ExperimentRecord(
        model_name    = "local",
        model_commit  = "local-cli",
        code_version  = "dev",
        resolved_spec = {"model": {"parameters": params}},
        source        = DataSource(
            type = "s3" if args.input.startswith("s3://") else "local",
            uri  = args.input,
        ),
        input_format  = getattr(args, "format", "auto"),
        parameters    = params,
        column_map    = _parse_params(getattr(args, "column_map", None)),
        band_map      = _parse_params(getattr(args, "band_map", None)),
    )

    if getattr(args, "output", None):
        record.output_path = args.output

    return record


# ── Commands ──────────────────────────────────────────────────────────────────

def _cmd_run(executor_cls, args) -> None:
    record   = _build_record(args)
    executor = executor_cls()

    print("▶ Validating...")
    executor.validate(record)

    print("▶ Running...")
    result = executor.run(record)

    print("▶ Saving...")
    record = executor.save(result, record)

    print(f"\n✅ Completed")
    print(f"   output:  {record.output_path}")
    if record.output_sha256:
        print(f"   sha256:  {record.output_sha256[:16]}...")
    print(f"   status:  {record.status}")
    for log in record.logs:
        print(f"   {log}")


def _cmd_validate(executor_cls, args) -> None:
    from .testing import ExecutorTestHarness

    harness = ExecutorTestHarness(executor_cls)
    ok      = harness.run_contract_tests()

    if getattr(args, "input", None):
        record = _build_record(args)
        harness.run_with_sample_data(record)

    sys.exit(0 if ok else 1)


def _cmd_show(executor_cls, args) -> None:
    params = {**_load_local_params(), **_parse_params(getattr(args, "param", None))}

    print(f"Executor: {executor_cls.__module__}.{executor_cls.__name__}")
    if hasattr(executor_cls, "name"):
        print(f"Name:     {executor_cls.name}")

    print(f"\nResolved parameters (model.toml + CLI overrides):")
    if params:
        for k, v in params.items():
            print(f"  {k} = {v!r}")
    else:
        print("  (none — no model.toml found and no --param given)")


# ── Parser ────────────────────────────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description = "DisSModel CLI — run and validate executors locally",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # ── run ──────────────────────────────────────────────────────────────────
    run_p = sub.add_parser("run", help="Run the simulation locally")
    run_p.add_argument("--input",  "-i", required=True,
                       help="Input URI: local path or s3://bucket/key")
    run_p.add_argument("--output", "-o", default=None,
                       help="Output path: local file or s3://bucket/key")
    run_p.add_argument("--param",  "-p", action="append", metavar="KEY=VALUE",
                       help="Override model parameter (repeatable)")
    run_p.add_argument("--column-map", action="append", metavar="CANONICAL=REAL",
                       help="Column mapping for vector input (repeatable)")
    run_p.add_argument("--band-map",   action="append", metavar="CANONICAL=REAL",
                       help="Band mapping for raster input (repeatable)")
    run_p.add_argument("--format", choices=["vector", "raster", "auto"],
                       default="auto")
    run_p.set_defaults(func=_cmd_run)

    # ── validate ─────────────────────────────────────────────────────────────
    val_p = sub.add_parser("validate", help="Validate executor contract without running")
    val_p.add_argument("--input", "-i", default=None,
                       help="Optional input for full cycle test")
    val_p.add_argument("--param", "-p", action="append", metavar="KEY=VALUE")
    val_p.set_defaults(func=_cmd_validate)

    # ── show ─────────────────────────────────────────────────────────────────
    show_p = sub.add_parser("show", help="Show resolved parameters")
    show_p.add_argument("--param", "-p", action="append", metavar="KEY=VALUE")
    show_p.set_defaults(func=_cmd_show)

    return parser


# ── Public entry point ────────────────────────────────────────────────────────

def run_cli(executor_cls, args=None) -> None:
    """
    Entry point for running an executor from the command line.
    Called directly by the researcher's executor module.

    Usage
    -----
    # In your executor module:
    if __name__ == "__main__":
        from dissmodel.cli import run_cli
        run_cli(FloodVectorExecutor)

    Then from the terminal:
        python -m coastal_flood.flood_executor run  --input data/grid.zip
        python -m coastal_flood.flood_executor validate
        python -m coastal_flood.flood_executor show
    """
    parser    = _build_parser()
    parsed    = parser.parse_args(args)
    parsed.func(executor_cls, parsed)
