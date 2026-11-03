import numpy as np
import pytest

from ifte0007.scoring import block_indices, metrics, score


def test_exact_coursework_examples_and_actual_denominator():
    error, marks = score([100, 101, 110, 120], [100, 100, 100, 100])
    np.testing.assert_allclose(error, [0, 1, 10, 20])
    np.testing.assert_allclose(marks, [50, 45, 0, 0])
    assert score(100, 200)[0] == 50


@pytest.mark.parametrize("bad", [0, -1, np.nan, np.inf])
def test_invalid_levels_are_not_scored(bad):
    with pytest.raises(ValueError):
        score(bad, 100)
    with pytest.raises(ValueError):
        score(100, bad)


def test_summary_thresholds_are_strict_and_probabilities_are_fractions():
    result = metrics([101, 102, 106], [100, 100, 100])
    assert result["n"] == 3
    assert result["count_error_gt_1pct"] == 2
    assert result["count_error_gt_2pct"] == 1
    assert result["prob_error_gt_5pct"] == pytest.approx(1 / 3)
    assert result["median_ape"] == 2
    with pytest.raises(ValueError, match="Empty"):
        metrics([], [])


def test_block_indices_preserve_circular_registered_consecutive_rows():
    indices = block_indices(15, repetitions=8, block=4, seed=42)
    np.testing.assert_array_equal(indices, block_indices(15, 8, 4, 42))
    assert indices.shape == (8, 15)
    for start in (0, 4, 8):
        np.testing.assert_array_equal(
            (np.diff(indices[:, start : start + 4]) % 15), np.ones((8, 3))
        )
