"""Replay RV20 from the included invented sample."""

import csv
import json
from math import fsum, isclose, isfinite, log
from pathlib import Path

SAMPLE = Path(__file__).with_name("invented_cash_closes.csv")
CONFIG = Path(__file__).with_name("feature_example.json")


def realised_variance(closes):
    if len(closes) != 21 or any(not isfinite(value) or value <= 0 for value in closes):
        raise ValueError("Expected 21 positive finite cash closes")
    return 252 * fsum(log(current / prior) ** 2 for prior, current in zip(closes, closes[1:])) / 20


def read_closes(path, dates):
    with path.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        for date_column, value_column in (
            ("date", "close"),
            ("observation_date", "SP500"),
            ("DATE", "SP500"),
        ):
            if {date_column, value_column}.issubset(reader.fieldnames or []):
                break
        else:
            raise ValueError("Expected date,close or observation_date,SP500 column headers")
        rows = {}
        for row in reader:
            date = row[date_column]
            if date in dates:
                if date in rows:
                    raise ValueError(f"Duplicate required session {date}")
                rows[date] = float(row[value_column])
    if missing := set(dates) - rows.keys():
        raise ValueError(f"Missing required sessions: {', '.join(sorted(missing))}")
    return [rows[date] for date in dates]


def main():
    config = json.loads(CONFIG.read_text())
    closes = read_closes(SAMPLE, config["sessions"])
    vix, expected = config["invented_vix"], config["invented_expected_rv20"]
    scope = "Invented prices and VIX, demonstrating the feature calculation"
    rv20 = realised_variance(closes)
    if not isclose(rv20, expected, rel_tol=0, abs_tol=1e-14):
        raise ValueError(f"RV20 mismatch for {scope}")
    print(
        json.dumps(
            {
                "scope": scope,
                "last_cash_session": config["sessions"][-1],
                "close_count": len(closes),
                "return_count": len(closes) - 1,
                "annualised_rv20": rv20,
                "variance_gap": (vix / 100) ** 2 - rv20,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
