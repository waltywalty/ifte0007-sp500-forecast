"""Offline assessment commands. No command fetches prices or submits coursework."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime
import importlib.metadata
import json
import math
from pathlib import Path
import platform
import socket
import sys
from typing import Any

from .evidence import (
    EvidenceError,
    contained_file,
    load_json,
    package_evidence,
    sha256_file,
    verify_evidence,
)
from .records import replay_document, verify_final


@contextmanager
def offline_calculation():
    """Reject accidental network use during every CLI calculation."""

    def denied(*args: Any, **kwargs: Any) -> None:
        raise RuntimeError("Network access is disabled for offline assessment commands")

    original = (socket.socket, socket.create_connection, socket.getaddrinfo)
    socket.socket = denied  # type: ignore[assignment]
    socket.create_connection = denied  # type: ignore[assignment]
    socket.getaddrinfo = denied  # type: ignore[assignment]
    try:
        yield
    finally:
        socket.socket, socket.create_connection, socket.getaddrinfo = original


def json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, (str, int, bool)) or value is None:
        return value
    if isinstance(value, datetime):
        return value.isoformat()
    if hasattr(value, "item"):
        return json_safe(value.item())
    if hasattr(value, "tolist"):
        return json_safe(value.tolist())
    raise ValueError(f"Unsupported output type: {type(value).__name__}")


def versions() -> dict[str, str]:
    result = {"python": platform.python_version()}
    for name in ("numpy", "pandas", "scipy", "exchange-calendars", "ifte0007-forecast"):
        try:
            result[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            result[name] = "not installed as distribution"
    result["solver"] = "scipy.optimize.linprog(method='highs')"
    return result


def demo() -> dict[str, Any]:
    """Invented scalar example, deliberately independent of empirical market values."""
    record = {
        "schema_version": 1,
        "kind": "synthetic",
        "method": "variance_lad",
        "origin": "2026-11-13T11:45:00+00:00",
        "target_at": "2026-11-20T21:00:00+00:00",
        "baseline_at": "2026-11-12T21:00:00+00:00",
        "baseline_available_at": "2026-11-13T09:00:00+00:00",
        "variance_gap_observed_at": "2026-11-11T21:15:00+00:00",
        "variance_gap_available_at": "2026-11-13T09:15:00+00:00",
        "term_slope_observed_at": "2026-11-11T21:15:00+00:00",
        "term_slope_available_at": "2026-11-13T09:15:00+00:00",
        "baseline": 100.0,
        "vix": 20.0,
        "vix3m": 22.0,
        "rv20": 0.02,
        "variance_gap": 0.02,
        "term_slope": math.log(22.0 / 20.0),
        "model_fit": {
            "kind": "lad",
            "features": ["variance_gap"],
            "mean": [0.01],
            "scale": [0.02],
            "intercept": 1.01,
            "coefficients": [-0.002],
            "shrinkage": 0.5,
            "solver_success": True,
        },
        "forecast": 100.45,
        "displayed_forecast": "100.45",
        "n_train": 160,
        "train_start": "2017-02-03T12:00:00+00:00",
        "train_end": "2026-10-30T12:00:00+00:00",
        "max_training_label": "2026-11-07T09:00:00+00:00",
        "nonbinding": True,
        "qualification": "All numerical inputs are invented; no empirical fit, source acquisition or forecast issuance is claimed.",
    }
    return {
        "status": "synthetic_demonstration_only",
        "record": record,
        "verification": replay_document(record),
        "versions": versions(),
    }


def reproduce(snapshot_path: Path, output: Path) -> dict[str, Any]:
    """Run the frozen evaluator on the exact explicitly provided local feature table.

    Snapshot v1: {schema_version:1, kind:'synthetic'|'empirical', description,
    feature_table:{path:<relative to snapshot>,sha256}, permission_basis?;
    expected_origins?}. Empirical snapshots require permission_basis. This records
    caller-supplied use basis; it does not invent redistribution permission.
    """
    if output.exists() or output.is_symlink():
        raise EvidenceError("Output already exists; choose a new reproduction directory")
    if not output.parent.is_dir():
        raise EvidenceError("Output parent must already exist")
    snapshot_path = snapshot_path.resolve(strict=True)
    snapshot = load_json(snapshot_path)
    kind = snapshot.get("kind")
    if snapshot.get("schema_version") != 1 or kind not in {"synthetic", "empirical"}:
        raise EvidenceError(
            "Snapshot must explicitly declare schema v1 and synthetic/empirical kind"
        )
    if not isinstance(snapshot.get("description"), str) or not snapshot["description"].strip():
        raise EvidenceError("Snapshot description is required")
    if kind == "empirical" and (
        not isinstance(snapshot.get("permission_basis"), str)
        or not snapshot["permission_basis"].strip()
    ):
        raise EvidenceError("Empirical use requires an explicit recorded permission basis")
    feature = snapshot.get("feature_table")
    if not isinstance(feature, dict):
        raise EvidenceError("Snapshot feature_table descriptor is missing")
    path = contained_file(snapshot_path.parent, feature.get("path"))
    digest = sha256_file(path)
    if feature.get("sha256") != digest:
        raise EvidenceError("Feature-table hash mismatch")
    # Lazy imports keep record replay and metadata checking usable without SciPy.
    import pandas as pd

    from .evaluation import evaluate

    table = pd.read_csv(path)
    if "dataset_kind" in table:
        kinds = table["dataset_kind"]
        if kinds.isna().any() or set(kinds.unique()) != {kind}:
            raise EvidenceError(
                "Feature-table dataset_kind conflicts with its snapshot; synthetic data cannot masquerade as empirical"
            )
    predictions, metrics = evaluate(table)
    if predictions.empty:
        raise EvidenceError("No eligible origins; this is not an empirical reproduction")
    count = int(predictions["origin"].nunique())
    if "expected_origins" in snapshot:
        expected = snapshot["expected_origins"]
        if isinstance(expected, bool) or not isinstance(expected, int) or expected != count:
            raise EvidenceError(f"Expected-origin mismatch: produced {count}")
    if sha256_file(path) != digest:
        raise EvidenceError("Feature table changed during reproduction")
    result = {
        "status": "completed_offline_reproduction",
        "kind": kind,
        "description": snapshot["description"],
        "origin_count": count,
        "prediction_rows": len(predictions),
        "snapshot_sha256": sha256_file(snapshot_path),
        "feature_table_sha256": digest,
        "versions": versions(),
        "metrics": metrics,
        "qualification": (
            "Invented-input mechanics only; no empirical accuracy claim."
            if kind == "synthetic"
            else "Saved-input retrospective reproduction; not a fresh holdout or prospective issue."
        ),
    }
    # Exclusive directory creation preserves all earlier attempts.
    output.mkdir(exist_ok=False)
    predictions.to_csv(output / "predictions.csv", index=False)
    (output / "results.json").write_text(
        json.dumps(json_safe(result), indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    (output / "input_snapshot.json").write_bytes(snapshot_path.read_bytes())
    result["output_hashes"] = {
        name: sha256_file(output / name)
        for name in ("predictions.csv", "results.json", "input_snapshot.json")
    }
    (output / "output_manifest.json").write_text(
        json.dumps(result["output_hashes"], indent=2) + "\n", encoding="utf-8"
    )
    return result


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    sub = result.add_subparsers(dest="command", required=True)
    sub.add_parser("demo", help="Invented scalar demonstration only")
    for name in ("replay", "verify-final"):
        command = sub.add_parser(name)
        command.add_argument("--record", required=True, type=Path)
        if name == "verify-final":
            command.add_argument(
                "--root",
                type=Path,
                help="Root for bound source paths; defaults to record directory",
            )
    reproduction = sub.add_parser("reproduce")
    reproduction.add_argument("--snapshot", required=True, type=Path)
    reproduction.add_argument("--output", required=True, type=Path)
    for name in ("verify-evidence", "package-evidence"):
        command = sub.add_parser(name)
        command.add_argument("--manifest", required=True, type=Path)
        command.add_argument("--root", type=Path)
        if name == "package-evidence":
            command.add_argument("--output", required=True, type=Path)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        with offline_calculation():
            if args.command == "demo":
                result = demo()
            elif args.command == "replay":
                result = replay_document(load_json(args.record))
            elif args.command == "verify-final":
                result = verify_final(
                    load_json(args.record), args.root or args.record.resolve().parent
                )
            elif args.command == "reproduce":
                result = reproduce(args.snapshot, args.output)
            elif args.command == "verify-evidence":
                result = verify_evidence(args.manifest, args.root)
            else:
                result = package_evidence(args.manifest, args.output, args.root)
        print(json.dumps(json_safe(result), indent=2, allow_nan=False))
        return 0
    except (ValueError, OSError, RuntimeError, KeyError, TypeError, ImportError) as exc:
        print(
            json.dumps({"status": "failed", "command": args.command, "error": str(exc)}),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
