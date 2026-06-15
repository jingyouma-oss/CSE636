"""
Translate a CPU forecast into a Kubernetes scaling recommendation.

This module is deliberately dependency-free and pure so it is easy to test and
reason about — it is the heart of the Week 4 lab. The Prophet forecasting code
that *feeds* these functions lives in forecast.py.
"""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class ScalingDecision:
    current_replicas: int
    recommended_replicas: int

    @property
    def delta(self) -> int:
        return self.recommended_replicas - self.current_replicas

    @property
    def action(self) -> str:
        if self.delta > 0:
            return f"Scale UP by {self.delta} replica(s) (pre-emptive)"
        if self.delta < 0:
            return f"Scale DOWN by {-self.delta} replica(s)"
        return "No change needed"


def required_replicas(
    current_replicas: int,
    predicted_cpu: float,
    target_cpu_per_replica: float = 60.0,
    min_replicas: int = 2,
    max_replicas: int = 50,
) -> int:
    """Return the replica count needed to keep CPU near the target.

    The intuition: if `current_replicas` pods are collectively predicted to run
    at `predicted_cpu`% and we want each to sit at `target_cpu_per_replica`%,
    we need ceil(current * predicted / target) pods — then clamp to [min, max].

    >>> required_replicas(5, 85, target_cpu_per_replica=60)
    8
    >>> required_replicas(5, 20, target_cpu_per_replica=60)  # clamps to min
    2
    """
    if current_replicas < 1:
        raise ValueError("current_replicas must be >= 1")
    if predicted_cpu < 0:
        raise ValueError("predicted_cpu must be >= 0")
    if target_cpu_per_replica <= 0:
        raise ValueError("target_cpu_per_replica must be > 0")
    if min_replicas > max_replicas:
        raise ValueError("min_replicas must be <= max_replicas")

    raw = math.ceil(current_replicas * predicted_cpu / target_cpu_per_replica)
    return max(min_replicas, min(max_replicas, raw))


def decide(
    current_replicas: int,
    predicted_cpu: float,
    target_cpu_per_replica: float = 60.0,
    min_replicas: int = 2,
    max_replicas: int = 50,
) -> ScalingDecision:
    """Bundle the replica calculation with a human-readable action."""
    rec = required_replicas(
        current_replicas,
        predicted_cpu,
        target_cpu_per_replica,
        min_replicas,
        max_replicas,
    )
    return ScalingDecision(current_replicas=current_replicas, recommended_replicas=rec)
