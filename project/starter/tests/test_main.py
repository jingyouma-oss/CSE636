"""Tests for the starter service.

Run them with:  pytest -q   (or:  make test)

These tests are intentionally readable. In Week 3 you'll have an AI agent
generate and extend tests like these.
"""

import pytest

from app.main import create_app, deployment_risk_score


# --- Unit tests for the pure function -------------------------------------

def test_small_change_with_passing_tests_is_low_risk():
    assert deployment_risk_score(files_changed=1, lines_changed=10, tests_passing=True) < 0.2


def test_failing_tests_add_risk():
    passing = deployment_risk_score(files_changed=2, lines_changed=50, tests_passing=True)
    failing = deployment_risk_score(files_changed=2, lines_changed=50, tests_passing=False)
    assert failing > passing
    assert failing - passing == pytest.approx(0.5)


def test_large_change_is_clamped_to_one():
    assert deployment_risk_score(files_changed=100, lines_changed=100000, tests_passing=False) == 1.0


def test_negative_counts_raise():
    with pytest.raises(ValueError):
        deployment_risk_score(files_changed=-1, lines_changed=0, tests_passing=True)


# --- Tests for the web endpoints ------------------------------------------

@pytest.fixture
def client():
    app = create_app()
    app.config.update(TESTING=True)
    return app.test_client()


def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"


def test_risk_endpoint_returns_a_score(client):
    resp = client.get("/risk?files_changed=3&lines_changed=120&tests_passing=true")
    assert resp.status_code == 200
    assert 0.0 <= resp.get_json()["risk_score"] <= 1.0


def test_risk_endpoint_rejects_negative_input(client):
    resp = client.get("/risk?files_changed=-5&lines_changed=10&tests_passing=true")
    assert resp.status_code == 400
