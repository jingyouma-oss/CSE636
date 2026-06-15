"""
Precision / recall / F1 for anomaly detection — pure, dependency-free, tested.

Treats "anomaly" as the positive class. This is the metric that matters for
imbalanced detection problems (Week 5): raw accuracy is misleading when 98% of
points are normal, so we score how well we catch the rare anomalies.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Scores:
    precision: float
    recall: float
    f1: float
    true_positives: int
    false_positives: int
    false_negatives: int

    def __str__(self) -> str:
        return (
            f"precision={self.precision:.2f} recall={self.recall:.2f} "
            f"f1={self.f1:.2f} "
            f"(TP={self.true_positives} FP={self.false_positives} "
            f"FN={self.false_negatives})"
        )


def score(y_true, y_pred) -> Scores:
    """Compare ground-truth vs predicted anomaly flags.

    Both inputs are iterables of 0/1 (1 = anomaly). Returns precision, recall,
    and F1 for the anomaly (positive) class.

    >>> s = score([0, 0, 1, 1], [0, 1, 1, 0])
    >>> round(s.precision, 2), round(s.recall, 2)
    (0.5, 0.5)
    """
    y_true = list(y_true)
    y_pred = list(y_pred)
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must be the same length")
    if not y_true:
        raise ValueError("inputs must be non-empty")

    tp = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)
          if (precision + recall) else 0.0)

    return Scores(precision, recall, f1, tp, fp, fn)
