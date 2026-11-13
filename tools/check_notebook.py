"""Execute reviewed Python notebook cells in-process with network disabled.

Avoids requiring a live Jupyter server or opening kernel sockets. This checker
is for the authored walkthrough, not for executing arbitrary downloaded code.
"""

import argparse
import contextlib
import io
from pathlib import Path

import nbformat

from ifte0007.cli import offline_calculation


def run(path: Path, write: bool = False) -> int:
    notebook = nbformat.read(path, as_version=4)
    nbformat.validate(notebook)
    namespace = {"__name__": "__main__"}
    count = 0
    with offline_calculation():
        for index, cell in enumerate(notebook.cells):
            if cell.cell_type != "code":
                continue
            count += 1
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exec(compile(cell.source, f"{path.name}:cell{index + 1}", "exec"), namespace)
            cell.execution_count = count
            cell.outputs = [nbformat.v4.new_output("stream", name="stdout", text=output.getvalue())]
    if write:
        nbformat.write(notebook, path)
    return count


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--notebook", type=Path, default=Path("notebooks/forecasting_walkthrough.ipynb")
    )
    parser.add_argument("--write", action="store_true", help="Refresh authored synthetic outputs")
    args = parser.parse_args()
    print(f"Executed {run(args.notebook, args.write)} synthetic notebook cells offline")
