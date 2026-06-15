"""Tests for the pure scaling logic — runs without Prophet/pandas."""
import pytest

from scaling import ScalingDecision, decide, required_replicas


def test_scale_up_when_cpu_exceeds_target():
    # 5 pods predicted at 85% CPU, target 60% → ceil(5 * 85/60) = 8
    assert required_replicas(5, 85, target_cpu_per_replica=60) == 8


def test_clamps_to_minimum():
    assert required_replicas(5, 10, target_cpu_per_replica=60, min_replicas=2) == 2


def test_clamps_to_maximum():
    assert required_replicas(5, 99, target_cpu_per_replica=10, max_replicas=20) == 20


def test_no_change_when_at_target():
    assert required_replicas(5, 60, target_cpu_per_replica=60) == 5


def test_decision_action_text():
    d = decide(5, 85, target_cpu_per_replica=60)
    assert isinstance(d, ScalingDecision)
    assert d.delta == 3
    assert "Scale UP by 3" in d.action


def test_decision_scale_down():
    d = decide(10, 30, target_cpu_per_replica=60)  # ceil(10*30/60)=5
    assert d.recommended_replicas == 5
    assert "Scale DOWN by 5" in d.action


@pytest.mark.parametrize("bad", [
    dict(current_replicas=0, predicted_cpu=50),
    dict(current_replicas=5, predicted_cpu=-1),
    dict(current_replicas=5, predicted_cpu=50, target_cpu_per_replica=0),
])
def test_invalid_inputs_raise(bad):
    with pytest.raises(ValueError):
        required_replicas(**bad)
