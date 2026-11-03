"""Destination, attribution, traversal and deterministic packaging tests."""

import hashlib
import json
import zipfile

import pytest

from ifte0007.evidence import EvidenceError, package_evidence, verify_evidence


def make_evidence(tmp_path):
    (tmp_path / "proof.txt").write_text("Synthetic authored example\n")
    digest = hashlib.sha256((tmp_path / "proof.txt").read_bytes()).hexdigest()
    register = {
        "schema_version": 1,
        "artifacts": [
            {
                "path": "proof.txt",
                "sha256": digest,
                "status": "approved",
                "destinations": ["github", "submission"],
                "origin": "invented test material",
                "licence_basis": "Test fixture, no external content",
                "required_notices": [],
                "reviewer": "automated TEST fixture",
                "reviewed_at": "2026-11-03T13:00:00+00:00",
            }
        ],
    }
    (tmp_path / "rights.json").write_text(json.dumps(register))
    manifest = {
        "schema_version": 1,
        "destination": "github",
        "rights_register": "rights.json",
        "files": [{"path": "proof.txt", "sha256": digest}],
    }
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest))
    return path, register, manifest


def test_valid_manifest_and_modified_file(tmp_path):
    path, _, _ = make_evidence(tmp_path)
    assert verify_evidence(path, tmp_path)["file_count"] == 1
    (tmp_path / "proof.txt").write_text("changed")
    with pytest.raises(EvidenceError, match="hash mismatch"):
        verify_evidence(path, tmp_path)


@pytest.mark.parametrize(
    "name",
    ["../proof.txt", "/proof.txt", "a/../proof.txt", "a//b", ".env", "private_wrds/file.csv"],
)
def test_unsafe_paths_fail_closed(tmp_path, name):
    path, _, manifest = make_evidence(tmp_path)
    manifest["files"][0]["path"] = name
    path.write_text(json.dumps(manifest))
    with pytest.raises(EvidenceError):
        verify_evidence(path, tmp_path)


def test_symlink_is_not_an_export(tmp_path):
    path, _, _ = make_evidence(tmp_path)
    target = tmp_path / "target.txt"
    (tmp_path / "proof.txt").rename(target)
    (tmp_path / "proof.txt").symlink_to(target)
    with pytest.raises(EvidenceError, match="Symlink"):
        verify_evidence(path, tmp_path)


def test_pending_wrong_destination_and_missing_notice(tmp_path):
    path, register, _ = make_evidence(tmp_path)
    register["artifacts"][0]["status"] = "pending"
    (tmp_path / "rights.json").write_text(json.dumps(register))
    with pytest.raises(EvidenceError, match="approved"):
        verify_evidence(path, tmp_path)
    register["artifacts"][0]["status"] = "approved"
    register["artifacts"][0]["destinations"] = ["submission"]
    (tmp_path / "rights.json").write_text(json.dumps(register))
    with pytest.raises(EvidenceError, match="Destination"):
        verify_evidence(path, tmp_path)
    register["artifacts"][0]["destinations"] = ["github"]
    (tmp_path / "notice.txt").write_text("Required notice")
    register["artifacts"][0]["required_notices"] = ["notice.txt"]
    (tmp_path / "rights.json").write_text(json.dumps(register))
    with pytest.raises(EvidenceError, match="not included"):
        verify_evidence(path, tmp_path)


def test_deterministic_package_commit_binding_and_no_overwrite(tmp_path, monkeypatch):
    path, _, manifest = make_evidence(tmp_path)
    import ifte0007.evidence as evidence

    commit = "a" * 40
    monkeypatch.setattr(evidence, "_git_commit", lambda root: commit)
    monkeypatch.setattr(evidence, "_verify_committed_file", lambda *args: None)
    first, second = tmp_path / "first.zip", tmp_path / "second.zip"
    a = package_evidence(path, first, tmp_path)
    b = package_evidence(path, second, tmp_path)
    assert a["sha256"] == b["sha256"]
    with zipfile.ZipFile(first) as archive:
        metadata = json.loads(archive.read("PACKAGE_METADATA.json"))
        assert metadata["source_commit"] == commit
        assert archive.read("proof.txt") == (tmp_path / "proof.txt").read_bytes()
    with pytest.raises(EvidenceError, match="cannot be overwritten"):
        package_evidence(path, first, tmp_path)
    manifest["source_commit"] = "b" * 40
    path.write_text(json.dumps(manifest))
    with pytest.raises(EvidenceError, match="disagrees"):
        package_evidence(path, tmp_path / "wrong.zip", tmp_path)


def test_duplicate_allowlist_and_approval_hash_mismatch(tmp_path):
    path, register, manifest = make_evidence(tmp_path)
    manifest["files"].append(manifest["files"][0])
    path.write_text(json.dumps(manifest))
    with pytest.raises(EvidenceError, match="Duplicate"):
        verify_evidence(path, tmp_path)
    manifest["files"].pop()
    path.write_text(json.dumps(manifest))
    register["artifacts"][0]["sha256"] = "0" * 64
    (tmp_path / "rights.json").write_text(json.dumps(register))
    with pytest.raises(EvidenceError, match="these bytes"):
        verify_evidence(path, tmp_path)


def test_package_exports_only_selected_known_rights_fields(tmp_path, monkeypatch):
    path, register, manifest = make_evidence(tmp_path)
    manifest["unapproved_extra"] = "DO_NOT_EXPORT_MANIFEST_EXTRA"
    path.write_text(json.dumps(manifest))
    register["artifacts"][0]["unreviewed_private_field"] = "DO_NOT_EXPORT_THIS_VALUE"
    register["artifacts"].append(
        {
            "path": "not-exported.txt",
            "sha256": "0" * 64,
            "status": "pending",
            "private_note": "DO_NOT_EXPORT_PENDING_MATERIAL",
        }
    )
    (tmp_path / "rights.json").write_text(json.dumps(register))
    import ifte0007.evidence as evidence

    monkeypatch.setattr(evidence, "_git_commit", lambda root: "a" * 40)
    monkeypatch.setattr(evidence, "_verify_committed_file", lambda *args: None)
    output = tmp_path / "allowed.zip"
    package_evidence(path, output, tmp_path)
    with zipfile.ZipFile(output) as archive:
        assert b"DO_NOT_EXPORT" not in archive.read("PACKAGE_MANIFEST.json")
        assert b"DO_NOT_EXPORT" not in archive.read("manifest.json")
        assert b"DO_NOT_EXPORT" not in archive.read("rights.json")
        content = archive.read("PACKAGE_RIGHTS_REGISTER.json")
        assert b"DO_NOT_EXPORT" not in content
        exported = json.loads(content)
        assert [entry["path"] for entry in exported["artifacts"]] == ["proof.txt"]
        metadata = json.loads(archive.read("PACKAGE_METADATA.json"))
        assert metadata["rights_register_export_sha256"] == hashlib.sha256(content).hexdigest()
        assert (
            metadata["rights_register_sha256"]
            == hashlib.sha256((tmp_path / "rights.json").read_bytes()).hexdigest()
        )
        assert (
            metadata["manifest_export_sha256"]
            == hashlib.sha256(archive.read("PACKAGE_MANIFEST.json")).hexdigest()
        )
        assert metadata["payload_file_count"] == 1
        assert metadata["derived_control_count"] == 5
        assert metadata["archive_file_count"] == len(archive.namelist()) == 6
        for name, digest in metadata["derived_controls"].items():
            assert hashlib.sha256(archive.read(name)).hexdigest() == digest
        extracted = tmp_path / "extracted"
        archive.extractall(extracted)
    assert verify_evidence(extracted / "PACKAGE_MANIFEST.json", extracted)["file_count"] == 1
    assert verify_evidence(extracted / "manifest.json", extracted)["file_count"] == 1
    assert json.loads((extracted / "manifest.json").read_text())["rights_register"] == "rights.json"


def test_package_rejects_a_dirty_rights_register(tmp_path, monkeypatch):
    path, register, _ = make_evidence(tmp_path)
    committed = {
        name: hashlib.sha256((tmp_path / name).read_bytes()).hexdigest()
        for name in ("proof.txt", "rights.json")
    }
    register["artifacts"][0]["reviewer"] = "Changed after committed review"
    (tmp_path / "rights.json").write_text(json.dumps(register))
    import ifte0007.evidence as evidence

    monkeypatch.setattr(evidence, "_git_commit", lambda root: "a" * 40)

    def match_committed(root, commit, name, digest):
        if committed.get(name) != digest:
            raise EvidenceError(f"Included file differs from source commit: {name}")

    monkeypatch.setattr(evidence, "_verify_committed_file", match_committed)
    with pytest.raises(EvidenceError, match="source commit"):
        package_evidence(path, tmp_path / "not-produced.zip", tmp_path)
    assert not (tmp_path / "not-produced.zip").exists()


@pytest.mark.parametrize(
    "reserved_path", ["PACKAGE_MANIFEST.json", "PACKAGE_METADATA.json/child.txt"]
)
def test_package_control_collision_is_rejected(tmp_path, monkeypatch, reserved_path):
    path, register, manifest = make_evidence(tmp_path)
    candidate = tmp_path / reserved_path
    candidate.parent.mkdir(exist_ok=True)
    candidate.write_text("An authored payload still cannot occupy package control paths\n")
    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    manifest["files"].append({"path": reserved_path, "sha256": digest})
    register["artifacts"].append(
        {
            **register["artifacts"][0],
            "path": reserved_path,
            "sha256": digest,
        }
    )
    path.write_text(json.dumps(manifest))
    (tmp_path / "rights.json").write_text(json.dumps(register))
    import ifte0007.evidence as evidence

    monkeypatch.setattr(evidence, "_git_commit", lambda root: "a" * 40)
    monkeypatch.setattr(evidence, "_verify_committed_file", lambda *args: None)
    with pytest.raises(EvidenceError, match="reserved|collide"):
        package_evidence(path, tmp_path / "not-produced.zip", tmp_path)
    assert not (tmp_path / "not-produced.zip").exists()
