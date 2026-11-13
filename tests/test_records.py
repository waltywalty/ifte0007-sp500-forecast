"""Independent arithmetic and final-record failure tests, all invented inputs."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil

import pytest

from ifte0007.cli import demo
from ifte0007.records import (
    RecordError,
    replay_document,
    replay_record,
    snapshot_digest,
    verify_final,
)


def example():
    return demo()["record"]


def test_independent_replay_and_wrapper():
    record = example()
    assert replay_record(record)["forecast"] == 100.45
    assert replay_document({"forecasts": [record, deepcopy(record)]})["count"] == 2
    assert replay_record(record)["source_authority_verified"] is False


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("forecast", 100.46),
        ("displayed_forecast", "100.46"),
        ("variance_gap_available_at", "2026-11-13T12:01:00+00:00"),
        ("max_training_label", "2026-11-13T12:01:00+00:00"),
        ("origin", "2026-11-13T11:45:00"),
        ("n_train", 139),
        ("train_start", "2025-01-01T12:00:00+00:00"),
        ("baseline", float("nan")),
    ],
)
def test_bad_arithmetic_or_chronology_fails(field, value):
    record = example()
    record[field] = value
    with pytest.raises(RecordError):
        replay_record(record)


def test_log_return_formula_and_changed_shrinkage_fail():
    record = example()
    record["model_fit"]["kind"] = "ridge"
    with pytest.raises(RecordError, match="log-return"):
        replay_record(record)
    record = example()
    record["model_fit"]["shrinkage"] = 1.0
    with pytest.raises(RecordError, match="shrinkage"):
        replay_record(record)


def final_example(tmp_path):
    # These are TEST attestations and invented inputs, not actual human sign-offs.
    record = example()
    record.update(
        kind="final_forecast",
        market="SP500",
        currency="USD",
        index_variant="price",
        information_cutoff="2026-11-13T12:00:00+00:00",
        issued_at="2026-11-13T11:46:00+00:00",
        nonbinding=False,
    )
    from ifte0007.timing import cash_calendar

    sessions = cash_calendar().sessions_in_range("2026-09-01", "2026-11-11")[-21:]
    labels = [session.strftime("%Y-%m-%d") for session in sessions] + ["2026-11-12"]
    record.update(rv20=0.0, variance_gap=0.04, forecast=100.35, displayed_forecast="100.35")
    repository = Path(__file__).resolve().parents[1]
    for source_name, target_name, path_field, hash_field in (
        (
            "variance_lad_v6_1_timing.json",
            "model-protocol.json",
            "protocol_path",
            "protocol_sha256",
        ),
        (
            "friday_operations.json",
            "acquisition-protocol.json",
            "acquisition_protocol_path",
            "acquisition_protocol_sha256",
        ),
    ):
        source = repository / "research/protocols" / source_name
        target = tmp_path / target_name
        shutil.copyfile(source, target)
        record[path_field] = target_name
        record[hash_field] = hashlib.sha256(target.read_bytes()).hexdigest()
    record["model_version"] = "SP500-final-bounded-v6.1"
    record["sources"] = []
    for identity in ("SP500", "VIXCLS", "VXVCLS"):
        path = tmp_path / f"{identity}-raw.csv"
        value = {"SP500": record["baseline"], "VIXCLS": record["vix"], "VXVCLS": record["vix3m"]}[
            identity
        ]
        rows = labels if identity == "SP500" else ["2026-11-11"]
        path.write_text(
            "observation_date," + identity + "\n" + "".join(f"{label},{value}\n" for label in rows)
        )
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        receipt = {
            "series": identity,
            "status": "validated_acquisition",
            "status_code": 200,
            "protocol_sha256": record["acquisition_protocol_sha256"],
            "raw_path": path.name,
            "raw_sha256": digest,
            "requested_start": labels[0],
            "requested_end": "2026-11-12",
            "source_url": f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={identity}&cosd={labels[0]}&coed=2026-11-12",
            "final_url": f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={identity}&cosd={labels[0]}&coed=2026-11-12",
            "started_at": "2026-11-13T11:43:00+00:00",
            "received_at": "2026-11-13T11:44:00+00:00",
        }
        receipt_path = tmp_path / f"{identity}-receipt.json"
        receipt_path.write_text(json.dumps(receipt))
        record["sources"].append(
            {
                "identity": identity,
                "path": path.name,
                "sha256": digest,
                "value": value,
                "receipt_path": receipt_path.name,
                "receipt_sha256": hashlib.sha256(receipt_path.read_bytes()).hexdigest(),
                "observed_at": record["baseline_at"]
                if identity == "SP500"
                else record["variance_gap_observed_at"],
                "available_at": record["baseline_available_at"]
                if identity == "SP500"
                else record["variance_gap_available_at"],
                "retrieved_at": "2026-11-13T11:44:00+00:00",
            }
        )
    digest = snapshot_digest(record)
    record["snapshot_sha256"] = digest
    record["signoffs"] = [
        {
            "member": name,
            "actor_type": "human",
            "decision": "approved",
            "snapshot_sha256": digest,
            "reviewed_at": "2026-11-13T11:50:00+00:00",
            "checks": ["instrument", "baseline", "factors", "arithmetic"],
        }
        for name in ("TEST reviewer A", "TEST reviewer B")
    ]
    return record


def test_final_attestation_validation_and_hash_binding(tmp_path):
    record = final_example(tmp_path)
    assert verify_final(record, tmp_path)["human_attestations"] == 2
    record["qualification"] = "Changed after review"
    with pytest.raises(RecordError, match="snapshot hash"):
        verify_final(record, tmp_path)


def test_final_requires_real_recorded_reviews_and_sources(tmp_path):
    record = final_example(tmp_path)
    record["signoffs"] = []
    with pytest.raises(RecordError, match="Two genuine"):
        verify_final(record, tmp_path)
    record = final_example(tmp_path)
    record["signoffs"][1]["member"] = "TEST reviewer A"
    with pytest.raises(RecordError, match="distinct"):
        verify_final(record, tmp_path)
    record = final_example(tmp_path)
    record["signoffs"][1]["actor_type"] = "ai"
    with pytest.raises(RecordError, match="human"):
        verify_final(record, tmp_path)
    record = final_example(tmp_path)
    (tmp_path / "SP500-raw.csv").write_text("altered")
    with pytest.raises(RecordError, match="source evidence hash"):
        verify_final(record, tmp_path)


def test_rehearsal_cannot_be_final(tmp_path):
    with pytest.raises(RecordError, match="final_forecast"):
        verify_final(example(), tmp_path)


def resign(record):
    record["snapshot_sha256"] = snapshot_digest(record)
    for signoff in record["signoffs"]:
        signoff["snapshot_sha256"] = record["snapshot_sha256"]


def test_final_source_value_and_duplicate_identity_fail(tmp_path):
    record = final_example(tmp_path)
    record["sources"][0]["value"] += 1
    resign(record)
    with pytest.raises(RecordError, match="source value"):
        verify_final(record, tmp_path)
    record = final_example(tmp_path)
    record["sources"].append(deepcopy(record["sources"][0]))
    resign(record)
    with pytest.raises(RecordError, match="unique"):
        verify_final(record, tmp_path)


def test_final_future_receipt_and_rv20_mismatch_fail(tmp_path):
    record = final_example(tmp_path)
    record["sources"][0]["retrieved_at"] = "2026-11-13T11:45:30+00:00"
    resign(record)
    with pytest.raises(RecordError, match="receipt"):
        verify_final(record, tmp_path)
    record = final_example(tmp_path)
    record["rv20"] += 0.01
    resign(record)
    with pytest.raises(RecordError, match="variance gap"):
        verify_final(record, tmp_path)


def alter_raw_and_resign(record, tmp_path, identity, body):
    source = next(row for row in record["sources"] if row["identity"] == identity)
    path = tmp_path / source["path"]
    path.write_text(body)
    source["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    receipt_path = tmp_path / source["receipt_path"]
    receipt = json.loads(receipt_path.read_text())
    receipt["raw_sha256"] = source["sha256"]
    receipt_path.write_text(json.dumps(receipt))
    source["receipt_sha256"] = hashlib.sha256(receipt_path.read_bytes()).hexdigest()
    resign(record)


@pytest.mark.parametrize(
    "body",
    [
        "Arbitrary prose is not financial source evidence\n",
        "date,value\n2026-11-11,20\n",
        "observation_date,SP500\n2026-11-11,20\n",
        "observation_date,VIXCLS\n2026-11-10,20\n",
        "observation_date,VIXCLS\n2026-11-11,20\n2026-11-11,20\n",
        "observation_date,VIXCLS\n2026-11-11,21\n",
    ],
)
def test_rehashed_forged_raw_payloads_still_fail(tmp_path, body):
    record = final_example(tmp_path)
    alter_raw_and_resign(record, tmp_path, "VIXCLS", body)
    with pytest.raises(RecordError):
        verify_final(record, tmp_path)


def test_raw_cash_rv20_and_receipt_url_are_checked(tmp_path):
    record = final_example(tmp_path)
    path = tmp_path / "SP500-raw.csv"
    body = path.read_text().replace("2026-11-10,100.0", "2026-11-10,101.0")
    alter_raw_and_resign(record, tmp_path, "SP500", body)
    with pytest.raises(RecordError, match="RV20 disagrees"):
        verify_final(record, tmp_path)
    record = final_example(tmp_path)
    source = record["sources"][0]
    receipt_path = tmp_path / source["receipt_path"]
    receipt = json.loads(receipt_path.read_text())
    receipt["source_url"] = receipt["source_url"].replace(
        "fred.stlouisfed.org", "unregistered.example"
    )
    receipt_path.write_text(json.dumps(receipt))
    source["receipt_sha256"] = hashlib.sha256(receipt_path.read_bytes()).hexdigest()
    resign(record)
    with pytest.raises(RecordError, match="FRED endpoint"):
        verify_final(record, tmp_path)


def test_final_method_version_and_protocol_bytes_are_pinned(tmp_path):
    record = final_example(tmp_path)
    record["model_version"] = "unregistered-method"
    resign(record)
    with pytest.raises(RecordError, match="model version"):
        verify_final(record, tmp_path)
    record = final_example(tmp_path)
    path = tmp_path / record["protocol_path"]
    body = json.loads(path.read_text())
    body["version"] = "unregistered-method"
    path.write_text(json.dumps(body))
    record["protocol_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    resign(record)
    with pytest.raises(RecordError, match="pinned frozen protocol"):
        verify_final(record, tmp_path)
