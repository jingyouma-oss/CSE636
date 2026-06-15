"""Tests for the pure precision/recall/F1 logic — runs without sklearn/pandas."""
import pytest

from evaluation import score


def test_perfect_detection():
    s = score([0, 0, 1, 1], [0, 0, 1, 1])
    assert s.precision == 1.0 and s.recall == 1.0 and s.f1 == 1.0


def test_half_precision_half_recall():
    # truth: anomalies at idx 2,3 ; pred: anomalies at idx 1,2
    s = score([0, 0, 1, 1], [0, 1, 1, 0])
    assert s.true_positives == 1
    assert s.false_positives == 1
    assert s.false_negatives == 1
    assert s.precision == 0.5
    assert s.recall == 0.5
    assert round(s.f1, 2) == 0.5


def test_misses_everything():
    s = score([1, 1, 1], [0, 0, 0])
    assert s.recall == 0.0
    assert s.f1 == 0.0


def test_accuracy_trap_all_normal():
    # 98 normal, 2 anomalies; predict all-normal → high "accuracy", zero recall
    y_true = [0] * 98 + [1, 1]
    y_pred = [0] * 100
    s = score(y_true, y_pred)
    assert s.recall == 0.0  # catches nothing despite 98% accuracy


def test_length_mismatch_raises():
    with pytest.raises(ValueError):
        score([0, 1], [0])


def test_empty_raises():
    with pytest.raises(ValueError):
        score([], [])
