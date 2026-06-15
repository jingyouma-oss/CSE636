VENV := .venv
BIN := $(VENV)/bin

.PHONY: setup data forecast test clean

setup:                ## create a venv and install deps (Prophet may take a few minutes)
	python3 -m venv $(VENV)
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install -r requirements.txt

data:                 ## generate synthetic cpu_metrics.csv (no deps beyond stdlib)
	$(BIN)/python generate_data.py

forecast: data        ## train Prophet, forecast, and print a scaling recommendation
	$(BIN)/python forecast.py

test:                 ## run the scaling-logic tests (no Prophet needed)
	$(BIN)/pip install pytest >/dev/null 2>&1 || true
	$(BIN)/pytest -q

clean:
	rm -rf $(VENV) .pytest_cache __pycache__ tests/__pycache__ cpu_metrics.csv
