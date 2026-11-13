"""Build a destination manifest from already reviewed, hash-current entries.

This never approves material, refreshes a rights hash or changes its destination.
An edited artifact needs a new rights review before its manifest can be rebuilt.
"""

import argparse
import hashlib
import json
from pathlib import Path

from ifte0007.evidence import contained_file


def build(root: Path, destination: str, output: Path) -> dict:
    register_name = "evidence/manifests/rights_register.json"
    register = json.loads((root / register_name).read_text())
    files = []
    for artifact in register["artifacts"]:
        if artifact["status"] != "approved" or destination not in artifact["destinations"]:
            continue
        path = contained_file(root, artifact["path"])
        if hashlib.sha256(path.read_bytes()).hexdigest() != artifact["sha256"]:
            raise ValueError(f"Changed artifact requires renewed review: {artifact['path']}")
        files.append({"path": artifact["path"], "sha256": artifact["sha256"]})
    if not files:
        raise ValueError("No approved artifacts for destination")
    result = {
        "schema_version": 1,
        "destination": destination,
        "rights_register": register_name,
        "files": sorted(files, key=lambda x: x["path"]),
    }
    output.write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument(
        "--destination", choices=["github", "submission", "group", "public"], required=True
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(f"Wrote {len(build(args.root, args.destination, args.output)['files'])} reviewed entries")
