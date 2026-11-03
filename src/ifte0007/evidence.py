"""Allowlisted, destination-specific evidence verification and deterministic ZIPs.

Manifest v1: {schema_version, destination, rights_register, files:[{path,sha256}],
source_commit?}. Paths are repository-relative POSIX file paths. The rights
register is {schema_version:1, artifacts:[{path,sha256,status,destinations,origin,
licence_basis,reviewer,reviewed_at,required_notices:[],citations?:[]}]}. A recorded
approval is evidence supplied by the reviewer, not automated legal certification.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import urlparse

from .records import canonical_json, timestamp

SHA256 = re.compile(r"^[0-9a-f]{64}$")
COMMIT = re.compile(r"^[0-9a-f]{40}(?:[0-9a-f]{24})?$")
DESTINATIONS = {"github", "submission", "group", "public"}
FORBIDDEN_PARTS = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    "private_wrds",
    "university_exports",
    "wrds_verification_2026-10-28",
    "protected_crypto",
    "protected_2026",
    "credentials",
    ".ssh",
    ".aws",
    ".pgpass",
    ".netrc",
}


class EvidenceError(ValueError):
    """Evidence cannot be verified or safely exported."""


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EvidenceError(f"Cannot read JSON evidence {path.name}: {exc}") from exc
    if not isinstance(value, dict):
        raise EvidenceError("JSON root must be an object")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_relative_path(value: Any) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise EvidenceError("An explicit repository-relative path is required")
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or "\\" in value
        or "\x00" in value
        or ":" in value
        or any(part in {"", ".", ".."} for part in value.split("/"))
        or path.as_posix() != value
    ):
        raise EvidenceError(f"Unsafe relative path: {value!r}")
    if any(
        part.casefold() in FORBIDDEN_PARTS or part.casefold().startswith(".env")
        for part in path.parts
    ):
        raise EvidenceError(f"Excluded path: {value}")
    return value


def contained_file(root: Path, value: Any) -> Path:
    """No traversal, symlinks, directories or restricted-path exports."""
    name = validate_relative_path(value)
    base = root.resolve(strict=True)
    candidate = base.joinpath(*PurePosixPath(name).parts)
    current = base
    for part in PurePosixPath(name).parts:
        current = current / part
        if current.is_symlink():
            raise EvidenceError(f"Symlink evidence is prohibited: {name}")
    try:
        resolved = candidate.resolve(strict=True)
    except FileNotFoundError as exc:
        raise EvidenceError(f"Missing evidence file: {name}") from exc
    if not resolved.is_relative_to(base) or not resolved.is_file():
        raise EvidenceError(f"Not a contained regular file: {name}")
    return resolved


def repository_root(start: Path) -> Path:
    parent = start.resolve().parent
    for candidate in (parent, *parent.parents):
        if (candidate / "pyproject.toml").is_file() and (candidate / "src/ifte0007").is_dir():
            return candidate
    raise EvidenceError("Cannot infer repository root; pass --root explicitly")


def _sha(value: Any, field: str) -> str:
    if not isinstance(value, str) or not SHA256.fullmatch(value):
        raise EvidenceError(f"{field} must be a lowercase SHA-256 digest")
    return value


def _rights(register: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if register.get("schema_version") != 1 or not isinstance(register.get("artifacts"), list):
        raise EvidenceError("Expected schema-v1 rights register with artifacts list")
    by_path = {}
    for entry in register["artifacts"]:
        if not isinstance(entry, dict):
            raise EvidenceError("Invalid rights-register entry")
        name = validate_relative_path(entry.get("path"))
        if name in by_path:
            raise EvidenceError(f"Duplicate rights entry: {name}")
        _sha(entry.get("sha256"), "rights.sha256")
        by_path[name] = entry
    return by_path


def verify_evidence(manifest_path: Path, root: Path | None = None) -> dict[str, Any]:
    """Verify each declared artifact and its destination-specific recorded basis."""
    manifest_path = manifest_path.resolve(strict=True)
    root = root.resolve(strict=True) if root else repository_root(manifest_path)
    # The supplied manifest may be outside the repo for local packaging, but files cannot.
    manifest = load_json(manifest_path)
    if manifest.get("schema_version") != 1:
        raise EvidenceError("Unsupported manifest schema")
    destination = manifest.get("destination")
    if destination not in DESTINATIONS:
        raise EvidenceError("Unknown intended destination")
    register_path = contained_file(root, manifest.get("rights_register"))
    register = load_json(register_path)
    entries = _rights(register)
    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        raise EvidenceError("Manifest files must be a nonempty explicit allowlist")
    included: dict[str, str] = {}
    obligations: set[str] = set()
    for item in files:
        if not isinstance(item, dict):
            raise EvidenceError("Invalid manifest file entry")
        name = validate_relative_path(item.get("path"))
        if name in included:
            raise EvidenceError(f"Duplicate included file: {name}")
        expected = _sha(item.get("sha256"), "files.sha256")
        actual = sha256_file(contained_file(root, name))
        if actual != expected:
            raise EvidenceError(f"Content hash mismatch: {name}")
        approval = entries.get(name)
        if approval is None or approval.get("status") != "approved":
            raise EvidenceError(f"No approved rights entry: {name}")
        if approval["sha256"] != actual:
            raise EvidenceError(f"Rights approval does not cover these bytes: {name}")
        destinations = approval.get("destinations")
        if not isinstance(destinations, list) or destination not in destinations:
            raise EvidenceError(f"Destination is not approved: {name}")
        for field in ("origin", "licence_basis", "reviewer", "reviewed_at"):
            if not isinstance(approval.get(field), str) or not approval[field].strip():
                raise EvidenceError(f"Missing rights {field}: {name}")
        timestamp(approval["reviewed_at"], "rights.reviewed_at")
        for field in ("required_notices", "citations"):
            links = approval.get(field, [])
            if not isinstance(links, list):
                raise EvidenceError(f"Invalid {field} list: {name}")
            for link in links:
                obligation = validate_relative_path(link)
                contained_file(root, obligation)
                obligations.add(obligation)
        included[name] = actual
    missing = obligations - included.keys()
    if missing:
        raise EvidenceError(
            "Required attribution/notice is not included: " + ", ".join(sorted(missing))
        )
    commit = manifest.get("source_commit")
    if commit is not None and (not isinstance(commit, str) or not COMMIT.fullmatch(commit)):
        raise EvidenceError("source_commit must be a complete commit digest")
    return {
        "status": "verified_manifest_and_recorded_permissions",
        "schema_version": 1,
        "destination": destination,
        "file_count": len(included),
        "files": dict(sorted(included.items())),
        "manifest_sha256": sha256_file(manifest_path),
        "rights_register_sha256": sha256_file(register_path),
        "rights_register_path": manifest["rights_register"],
        "source_commit": commit,
        "qualification": "Validates bytes, explicit allowlist and recorded approval; not legal certification or proof of reviewer identity.",
    }


def _git_commit(root: Path) -> str:
    try:
        command = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
            check=True,
            capture_output=True,
            text=True,
        )
        if Path(command.stdout.strip()).resolve() != root.resolve():
            raise EvidenceError(
                "Evidence root must be its own Git repository, not a parent workspace"
            )
        value = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise EvidenceError("Packaging requires a committed standalone Git repository") from exc
    if not COMMIT.fullmatch(value):
        raise EvidenceError("Cannot identify a full source commit")
    return value


def _verify_committed_file(root: Path, commit: str, name: str, expected: str) -> None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "show", f"{commit}:{name}"],
            check=True,
            capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise EvidenceError(f"Included file is not present in source commit: {name}") from exc
    if hashlib.sha256(result.stdout).hexdigest() != expected:
        raise EvidenceError(f"Included file differs from source commit: {name}")


def _rights_export(
    register: dict[str, Any], included: dict[str, str], destination: str
) -> dict[str, Any]:
    """Export selected approvals only; unknown/private register fields never travel."""
    entries = _rights(register)
    exported = []
    for name in sorted(included):
        entry = entries[name]
        clean = {
            "path": name,
            "sha256": included[name],
            "status": "approved",
            "destinations": [destination],
        }
        for field in ("origin", "licence_basis", "reviewer", "reviewed_at"):
            value = entry[field]
            if (
                not isinstance(value, str)
                or not value.strip()
                or len(value) > 4000
                or "\x00" in value
            ):
                raise EvidenceError(f"Unsafe or invalid exported rights field: {field}")
            clean[field] = value
        for field in ("required_notices", "citations"):
            clean[field] = [validate_relative_path(path) for path in entry.get(field, [])]
        url = entry.get("source_url")
        if url is not None:
            if not isinstance(url, str) or len(url) > 2048:
                raise EvidenceError("Unsafe rights source URL")
            parsed = urlparse(url)
            # Bibliographic landing-page links only; no signed or account URLs.
            if (
                parsed.scheme not in {"https", "http"}
                or not parsed.hostname
                or parsed.username is not None
                or parsed.password is not None
                or parsed.query
                or parsed.fragment
            ):
                raise EvidenceError(
                    "Exported rights source URL must be a credential-free landing page"
                )
            clean["source_url"] = url
        exported.append(clean)
    return {
        "schema_version": 1,
        "artifacts": exported,
        "qualification": "Destination-specific approved subset; unrelated and pending register entries are excluded. Recorded approvals are not legal certification.",
    }


def package_evidence(manifest_path: Path, output: Path, root: Path | None = None) -> dict[str, Any]:
    """Build a deterministic ZIP from verified committed files; never overwrite."""
    root = root.resolve(strict=True) if root else repository_root(manifest_path)
    verified = verify_evidence(manifest_path, root)
    output = output.absolute()
    if output.exists() or output.is_symlink():
        raise EvidenceError("Output already exists; frozen packages cannot be overwritten")
    if output.suffix.lower() != ".zip":
        raise EvidenceError("Package output must end in .zip")
    if not output.parent.is_dir():
        raise EvidenceError("Output parent directory must exist")
    if any(output.resolve() == (root / name).resolve() for name in verified["files"]):
        raise EvidenceError("Output cannot replace an input")
    commit = _git_commit(root)
    if verified["source_commit"] not in (None, commit):
        raise EvidenceError("Manifest source_commit disagrees with actual HEAD")
    for name, digest in verified["files"].items():
        _verify_committed_file(root, commit, name, digest)
    register_path = contained_file(root, verified["rights_register_path"])
    _verify_committed_file(
        root, commit, verified["rights_register_path"], verified["rights_register_sha256"]
    )
    exported_register = _rights_export(
        load_json(register_path), verified["files"], verified["destination"]
    )
    exported_rights_bytes = canonical_json(exported_register) + b"\n"
    # The extractable manifest must refer to the extractable rights subset, not
    # an omitted private register path. Unknown input JSON fields are not exports.
    exported_manifest = {
        "schema_version": 1,
        "destination": verified["destination"],
        "rights_register": "PACKAGE_RIGHTS_REGISTER.json",
        "source_commit": commit,
        "files": [
            {"path": name, "sha256": digest} for name, digest in sorted(verified["files"].items())
        ],
    }
    exported_manifest_bytes = canonical_json(exported_manifest) + b"\n"
    metadata = {
        "schema_version": 1,
        "source_commit": commit,
        "manifest_sha256": verified["manifest_sha256"],
        "manifest_export_sha256": hashlib.sha256(exported_manifest_bytes).hexdigest(),
        "rights_register_sha256": verified["rights_register_sha256"],
        "rights_register_export_sha256": hashlib.sha256(exported_rights_bytes).hexdigest(),
        "files": verified["files"],
        "destination": verified["destination"],
        "qualification": "Deterministic allowlisted evidence package; not automatic assessment submission.",
    }
    reserved = {"PACKAGE_MANIFEST.json", "PACKAGE_RIGHTS_REGISTER.json", "PACKAGE_METADATA.json"}
    if reserved.intersection(verified["files"]):
        raise EvidenceError("Manifest uses reserved package metadata names")
    descriptor, temporary = tempfile.mkstemp(prefix=".ifte0007-package-", dir=output.parent)
    os.close(descriptor)
    try:

        def add(archive: zipfile.ZipFile, name: str, content: bytes) -> None:
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, content)

        with zipfile.ZipFile(
            temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
        ) as archive:
            for name in sorted(verified["files"]):
                content = contained_file(root, name).read_bytes()
                if hashlib.sha256(content).hexdigest() != verified["files"][name]:
                    raise EvidenceError(f"Input changed during packaging: {name}")
                add(archive, name, content)
            manifest_bytes = manifest_path.read_bytes()
            rights_bytes = register_path.read_bytes()
            if hashlib.sha256(manifest_bytes).hexdigest() != verified["manifest_sha256"]:
                raise EvidenceError("Manifest changed during packaging")
            if hashlib.sha256(rights_bytes).hexdigest() != verified["rights_register_sha256"]:
                raise EvidenceError("Rights register changed during packaging")
            add(archive, "PACKAGE_MANIFEST.json", exported_manifest_bytes)
            add(archive, "PACKAGE_RIGHTS_REGISTER.json", exported_rights_bytes)
            add(archive, "PACKAGE_METADATA.json", canonical_json(metadata) + b"\n")
        # Hard-link is atomic and refuses an output created concurrently.
        os.link(temporary, output)
    finally:
        Path(temporary).unlink(missing_ok=True)
    return {
        "status": "packaged_not_submitted",
        "output": str(output),
        "sha256": sha256_file(output),
        "source_commit": commit,
        "file_count": verified["file_count"],
    }
