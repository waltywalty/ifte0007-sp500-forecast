"""Offline CLI capability distinctions and missing-input rejection."""

import hashlib
import json
from pathlib import Path
import shutil
import socket

import pytest

from ifte0007.cli import demo, main, offline_calculation, reproduce
from ifte0007.evidence import EvidenceError


def test_demo_is_explicitly_synthetic():
    result = demo()
    assert result["status"] == "synthetic_demonstration_only"
    assert result["record"]["kind"] == "synthetic"
    assert result["verification"]["records"][0]["displayed_forecast"] == "100.45"


def test_network_denied_and_restored():
    original = socket.socket
    with offline_calculation():
        with pytest.raises(RuntimeError, match="Network access"):
            socket.socket()
    assert socket.socket is original


def test_reproduction_uses_exact_saved_invented_inputs(tmp_path):
    fixture = Path(__file__).parent / "fixtures/synthetic/feature_table.csv"
    shutil.copyfile(fixture, tmp_path / "features.csv")
    snapshot = {
        "schema_version": 1,
        "kind": "synthetic",
        "description": "Entirely invented test inputs",
        "feature_table": {
            "path": "features.csv",
            "sha256": hashlib.sha256(fixture.read_bytes()).hexdigest(),
        },
    }
    descriptor = tmp_path / "snapshot.json"
    descriptor.write_text(json.dumps(snapshot))
    with offline_calculation():
        result = reproduce(descriptor, tmp_path / "run1")
        repeat = reproduce(descriptor, tmp_path / "run2")
    assert result["kind"] == "synthetic"
    assert result["origin_count"] > 0
    assert result["output_hashes"] == repeat["output_hashes"]
    with pytest.raises(EvidenceError, match="already exists"):
        reproduce(descriptor, tmp_path / "run1")


def test_missing_empirical_snapshot_never_falls_back(tmp_path, capsys):
    assert (
        main(
            [
                "reproduce",
                "--snapshot",
                str(tmp_path / "absent.json"),
                "--output",
                str(tmp_path / "run"),
            ]
        )
        == 2
    )
    assert "failed" in capsys.readouterr().err
    assert not (tmp_path / "run").exists()
    descriptor = tmp_path / "snapshot.json"
    descriptor.write_text(
        json.dumps(
            {"schema_version": 1, "kind": "empirical", "description": "No permission supplied"}
        )
    )
    with pytest.raises(EvidenceError, match="permission basis"):
        reproduce(descriptor, tmp_path / "run")


def test_synthetic_cannot_be_labelled_empirical_and_basis_is_text(tmp_path):
    fixture = Path(__file__).parent / "fixtures/synthetic/feature_table.csv"
    shutil.copyfile(fixture, tmp_path / "features.csv")
    snapshot = {
        "schema_version": 1,
        "kind": "empirical",
        "description": "Incorrect metadata TEST",
        "permission_basis": True,
        "feature_table": {
            "path": "features.csv",
            "sha256": hashlib.sha256(fixture.read_bytes()).hexdigest(),
        },
    }
    descriptor = tmp_path / "snapshot.json"
    descriptor.write_text(json.dumps(snapshot))
    with pytest.raises(EvidenceError, match="permission basis"):
        reproduce(descriptor, tmp_path / "run")
    snapshot["permission_basis"] = "Invented test statement, not actual permission"
    descriptor.write_text(json.dumps(snapshot))
    with pytest.raises(EvidenceError, match="masquerade"):
        reproduce(descriptor, tmp_path / "run")


def test_mixed_feature_labels_are_rejected(tmp_path):
    import pandas as pd

    fixture = Path(__file__).parent / "fixtures/synthetic/feature_table.csv"
    table = pd.read_csv(fixture)
    table.loc[0, "dataset_kind"] = "empirical"
    path = tmp_path / "features.csv"
    table.to_csv(path, index=False)
    snapshot = {
        "schema_version": 1,
        "kind": "synthetic",
        "description": "Conflicting labels TEST",
        "feature_table": {
            "path": path.name,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        },
    }
    descriptor = tmp_path / "snapshot.json"
    descriptor.write_text(json.dumps(snapshot))
    with pytest.raises(EvidenceError, match="conflicts"):
        reproduce(descriptor, tmp_path / "run")
