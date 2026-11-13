"""Attach official PyPI release hashes to a reviewed pip-tools resolution.

Only package metadata is requested; never fetches market data. Hashes cover all
published distribution files so the same pins work on Linux and macOS. Windows
is not a tested target. Review licence and version changes before committing.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import re
from urllib.request import urlopen

from packaging.requirements import Requirement

MARKERS = {
    "appnope": 'sys_platform == "darwin"',
    "pexpect": 'sys_platform != "win32"',
    "ptyprocess": 'sys_platform != "win32"',
}


def release(requirement: Requirement) -> tuple[str, list[str]]:
    specifiers = list(requirement.specifier)
    if len(specifiers) != 1 or specifiers[0].operator != "==":
        raise ValueError(f"Exact pin required: {requirement}")
    version = specifiers[0].version
    url = f"https://pypi.org/pypi/{requirement.name}/{version}/json"
    with urlopen(url, timeout=60) as response:
        metadata = json.load(response)
    hashes = sorted({item["digests"]["sha256"] for item in metadata["urls"]})
    if not hashes or not all(re.fullmatch(r"[0-9a-f]{64}", value) for value in hashes):
        raise ValueError(f"No valid official release hashes for {requirement}")
    marker = (
        str(requirement.marker) if requirement.marker else MARKERS.get(requirement.name.lower())
    )
    pin = f"{requirement.name}=={version}"
    if marker:
        pin += "; " + marker
    return pin, hashes


def generate(source: Path, output: Path) -> int:
    requirements = [
        Requirement(line.strip())
        for line in source.read_text().splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    with ThreadPoolExecutor(max_workers=8) as executor:
        rows = list(executor.map(release, requirements))
    lines = [
        "# Exact Python 3.12 Linux/macOS dependency lock; verify with --require-hashes.",
        "# Resolution: piptools compile --allow-unsafe --extra dev --extra report --strip-extras pyproject.toml",
        "# Hashes: official https://pypi.org/pypi/<package>/<version>/json via tools/lock_dependencies.py",
        "# Platform markers preserve macOS-only appnope and POSIX-only pexpect/ptyprocess.",
        "",
    ]
    for pin, hashes in sorted(rows, key=lambda row: row[0].lower()):
        lines.append(pin + " \\")
        for index, digest in enumerate(hashes):
            lines.append("    --hash=sha256:" + digest + (" \\" if index < len(hashes) - 1 else ""))
    output.write_text("\n".join(lines) + "\n")
    return len(rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resolved", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(f"Wrote official hashes for {generate(args.resolved, args.output)} pins")
