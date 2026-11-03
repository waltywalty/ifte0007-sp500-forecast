"""Offline checks of the export boundary, local links and workflow defaults.

These mechanical checks do not certify copyright compliance or validate the
financial claims. Only manifest-listed content is eligible for publication.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import unquote

from ifte0007.evidence import contained_file, verify_evidence


def check(root: Path) -> dict:
    manifest = root / "evidence/manifests/github_manifest.json"
    result = verify_evidence(manifest, root=root)
    value = json.loads(manifest.read_text())
    names = {entry["path"] for entry in value["files"]}
    metadata = {"evidence/manifests/github_manifest.json", value["rights_register"]}
    allowed = names | metadata
    tracked = (
        subprocess.run(["git", "ls-files", "-z"], cwd=root, capture_output=True, check=True)
        .stdout.decode()
        .split("\0")
    )
    unknown = set(filter(None, tracked)) - allowed
    if unknown:
        raise ValueError(f"Tracked files outside reviewed export: {sorted(unknown)}")
    failures = []
    links_checked = 0
    for name in sorted(allowed):
        file = contained_file(root, name)
        if file.suffix.lower() not in {
            ".md",
            ".py",
            ".json",
            ".toml",
            ".yml",
            ".yaml",
            ".bib",
            ".lock",
            ".ipynb",
            ".csv",
        }:
            continue
        text = file.read_text(encoding="utf-8")
        patterns = [
            r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
            r"\bgh[pousr]_[A-Za-z0-9]{30,}\b",
            r"\bgithub_pat_[A-Za-z0-9_]{40,}\b",
            r"https?://[^\s/@]+:[^\s/@]+@",
            r"/" + r"Users/[^\s/]+/",
        ]
        for pattern in patterns:
            if re.search(pattern, text):
                failures.append(f"Sensitive/personal pattern in {name}")
        if file.suffix == ".md":
            for raw in re.findall(r"(?<!!)\[[^\]]*\]\(([^\s)]+)(?:\s+[^)]*)?\)", text):
                target = raw.strip("<>").split("#", 1)[0]
                if not target or re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target):
                    continue
                resolved = (file.parent / unquote(target)).resolve()
                if not resolved.is_relative_to(root.resolve()) or not resolved.exists():
                    failures.append(f"Broken/escaping local link {raw!r} in {name}")
                links_checked += 1
    workflow = (root / ".github/workflows/ci.yml").read_text()
    if "pull_request_target" in workflow or "schedule:" in workflow:
        failures.append("Unsafe CI event")
    for action in re.findall(r"uses:\s*([^\s#]+)", workflow):
        if not re.fullmatch(r"[^@]+@[0-9a-f]{40}", action):
            failures.append(f"Unpinned CI action: {action}")
    if failures:
        raise ValueError("\n".join(failures))
    return {
        "status": "passed",
        "local_links_checked": links_checked,
        "publication": result,
        "limitation": "Mechanical checks; human writing, rights and financial review still required",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    print(json.dumps(check(parser.parse_args().root), indent=2))
