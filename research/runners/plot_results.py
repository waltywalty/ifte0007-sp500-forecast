"""Render transparent comparison charts from one explicit reproduction directory.

Requires results.json and predictions.csv produced by the assessment CLI.
Generated empirical charts inherit the input data's sharing restrictions.
"""

import argparse
import json
import os
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")

import matplotlib.pyplot as plt
import pandas as pd

from ifte0007.cli import offline_calculation


def render(results: Path, output: Path) -> list[str]:
    if output.exists():
        raise ValueError("Choose a new chart directory; previous runs are preserved")
    metadata = json.loads((results / "results.json").read_text())
    kind = metadata.get("kind")
    if kind not in {"synthetic", "empirical"}:
        raise ValueError("Input must identify synthetic or empirical reproduction")
    table = pd.read_csv(results / "predictions.csv")
    table["origin"] = pd.to_datetime(table.origin, utc=True)
    selected = table[table.candidate.eq("variance_lad")].sort_values("origin")
    if selected.empty:
        raise ValueError("No selected-method predictions")
    label = (
        "SYNTHETIC INPUTS — mechanics only"
        if kind == "synthetic"
        else "Exposed retrospective evidence"
    )
    output.mkdir(parents=True, exist_ok=False)
    names = []

    def save(fig, name):
        fig.suptitle(label, fontsize=11)
        fig.tight_layout()
        fig.savefig(output / name, dpi=170)
        plt.close(fig)
        names.append(name)

    fig, ax = plt.subplots(figsize=(10, 4))
    for column in ("actual", "forecast", "baseline"):
        ax.plot(selected.origin, selected[column], label=column, linewidth=1)
    ax.set(
        title="Weekly forecast, realised target and unchanged-price baseline",
        ylabel="Index level",
        xlabel="Forecast origin",
    )
    ax.legend()
    save(fig, "weekly_levels.png")
    fig, ax = plt.subplots(figsize=(10, 4))
    for candidate, rows in table.groupby("candidate"):
        rows = rows.sort_values("origin")
        ax.plot(rows.origin, rows.ape.rolling(13, min_periods=13).mean(), label=candidate)
    ax.set(
        title="Trailing 13-origin mean absolute percentage error",
        ylabel="APE (%)",
        xlabel="Forecast origin",
    )
    ax.legend()
    save(fig, "rolling_error.png")
    fig, ax = plt.subplots(figsize=(11, 4))
    summary = table.groupby("candidate")[["train_score", "score"]].mean()
    summary = summary.rename(
        index={
            "unchanged": "Unchanged",
            "variance_lad": "Variance-gap LAD",
            "weighted_median_constant": "Refitted drift",
        }
    )
    summary.rename(
        columns={"train_score": "Apparent training mean", "score": "Chronological evaluation mean"}
    ).plot.bar(ax=ax)
    ax.set(
        title="Training and evaluation: descriptive comparison",
        ylabel="Mean marks out of 50",
        xlabel="Candidate",
    )
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1), fontsize=9)
    ax.tick_params(axis="x", rotation=15)
    save(fig, "training_vs_evaluation.png")
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    table.groupby("candidate").ape.quantile(0.9).plot.bar(ax=axes[0])
    axes[0].set(title="90th-percentile error", ylabel="APE (%)")
    b = selected.fit.map(lambda value: json.loads(value)["coefficients"][0])
    axes[1].plot(selected.origin, b)
    axes[1].axhline(0, color="black", linewidth=0.8)
    axes[1].set(title="Fitted variance-gap slope", ylabel="Gross return per training SD")
    axes[0].tick_params(axis="x", rotation=15)
    save(fig, "tail_error_and_slope.png")
    (output / "README.txt").write_text(
        label
        + "\nTraining and evaluation samples differ; this plot alone is not a formal overfitting test.\n"
        "Intervals and uncertainty are in results.json. Charts inherit input sharing restrictions.\n"
    )
    return names


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    with offline_calculation():
        print(json.dumps(render(args.results, args.output), indent=2))
