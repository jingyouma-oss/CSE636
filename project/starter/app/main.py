"""CSE636 starter service — a tiny web app you can build, test, containerize, and ship.

This file is deliberately small. It exists so beginners can exercise the whole
DevOps loop (code -> test -> build -> CI) on something real but not overwhelming,
and so AI coding agents have a concrete repo to act on in the Week 1+ labs.

Two things live here:
  1. `deployment_risk_score` — a pure function (easy to unit-test).
  2. A Flask web app with a few endpoints (something to run and containerize).
"""

from flask import Flask, jsonify, request


def deployment_risk_score(files_changed: int, lines_changed: int, tests_passing: bool) -> float:
    """Estimate how risky a deployment is, on a 0.0 (safe) to 1.0 (risky) scale.

    This is a teaching toy, not real science — Week 4 covers how real ML risk
    models work. The point is to have a deterministic function we can test.

    Risk grows with the size of the change and jumps if tests are failing.
    """
    if files_changed < 0 or lines_changed < 0:
        raise ValueError("files_changed and lines_changed must be non-negative")

    size_risk = min(1.0, (files_changed * 0.05) + (lines_changed * 0.001))
    test_penalty = 0.0 if tests_passing else 0.5
    return round(min(1.0, size_risk + test_penalty), 3)


def create_app() -> Flask:
    app = Flask(__name__)

    @app.get("/")
    def index():
        return jsonify(
            message="Welcome to the CSE636 starter service.",
            try_these=["/health", "/risk?files_changed=3&lines_changed=120&tests_passing=true"],
        )

    @app.get("/health")
    def health():
        # Health checks are how orchestrators (Kubernetes, load balancers) know
        # whether to send traffic to this instance. You'll meet these in Week 6.
        return jsonify(status="ok")

    @app.get("/risk")
    def risk():
        files_changed = request.args.get("files_changed", default=0, type=int)
        lines_changed = request.args.get("lines_changed", default=0, type=int)
        tests_passing = request.args.get("tests_passing", default="true").lower() == "true"
        try:
            score = deployment_risk_score(files_changed, lines_changed, tests_passing)
        except ValueError as exc:
            return jsonify(error=str(exc)), 400
        return jsonify(
            files_changed=files_changed,
            lines_changed=lines_changed,
            tests_passing=tests_passing,
            risk_score=score,
        )

    return app


app = create_app()


if __name__ == "__main__":
    # 0.0.0.0 so the app is reachable from outside a container.
    app.run(host="0.0.0.0", port=8000)
