"""Exercise the standalone report replay with invented values."""

import json
from pathlib import Path
import subprocess
import sys

import pytest

from tools.replay_report import main


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools/replay_report.py"
EXAMPLE = ROOT / "evidence/synthetic/report_replay_example.json"


def test_standalone_replay_uses_only_the_standard_library(tmp_path):
    result = subprocess.run(
        [sys.executable, "-I", "-S", str(TOOL), "--input", str(EXAMPLE)],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(result.stdout) == {
        "variance_gap": "0.01000000",
        "standardised_gap": "0.50000000",
        "intercept_points": "1.00",
        "factor_points": "0.50",
        "forecast": "101.50",
    }


def test_replay_accepts_report_style_minus(tmp_path, capsys):
    values = json.loads(EXAMPLE.read_text())
    values["slope"] = "−0.02"
    path = tmp_path / "inputs.json"
    path.write_text(json.dumps(values))
    assert main(["--input", str(path)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["factor_points"] == "-0.50"
    assert result["forecast"] == "100.50"


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("baseline", 0, "baseline must be positive"),
        ("baseline", True, "baseline must be a finite decimal number"),
        ("vix", -1, "vix must be positive"),
        ("realised_variance", "-0.01", "realised_variance must be nonnegative"),
        ("training_sd", 0, "training_sd must be positive"),
        ("training_sd", "Infinity", "training_sd must be a finite decimal number"),
        ("training_mean", float("nan"), "training_mean must be a finite decimal number"),
        ("intercept", "text", "intercept must be a finite decimal number"),
        ("intercept", -10, "Replayed forecast must be positive"),
    ],
)
def test_replay_rejects_invalid_input(tmp_path, capsys, field, value, message):
    values = json.loads(EXAMPLE.read_text())
    values[field] = value
    path = tmp_path / "inputs.json"
    path.write_text(json.dumps(values))
    assert main(["--input", str(path)]) == 2
    out, err = capsys.readouterr()
    assert not out
    assert message in err


def test_replay_reports_missing_fields(tmp_path, capsys):
    path = tmp_path / "inputs.json"
    path.write_text('{"baseline": 100}')
    assert main(["--input", str(path)]) == 2
    assert "Missing required fields:" in capsys.readouterr().err
