VENV := .venv
BIN := $(VENV)/bin

.PHONY: setup data detect test clean

setup:                ## create a venv and install deps
	python3 -m venv $(VENV)
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install -r requirements.txt

data:                 ## generate labelled synthetic metrics (stdlib only)
	$(BIN)/python generate_data.py

detect: data          ## run Isolation Forest and score it against ground truth
	$(BIN)/python detect.py

test:                 ## run the precision/recall tests (no sklearn needed)
	$(BIN)/pip install pytest >/dev/null 2>&1 || true
	$(BIN)/pytest -q

clean:
	rm -rf $(VENV) .pytest_cache __pycache__ tests/__pycache__ metrics_sample.csv
