# CSE636 starter service — common tasks.
# Run `make help` to see what's available. Each target is one DevOps verb.

PYTHON ?= python3
VENV   := .venv
BIN    := $(VENV)/bin
IMAGE  := cse636-starter

.PHONY: help setup test run docker-build docker-run clean

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

setup:  ## Create a virtual environment and install dependencies
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install -r requirements.txt
	@echo "Done. Now run: make test"

test:  ## Run the test suite
	$(BIN)/pytest -q

run:  ## Start the web app on http://localhost:8000
	$(BIN)/python -m app.main

docker-build:  ## Build the container image
	docker build -t $(IMAGE) .

docker-run:  ## Run the app inside a container on http://localhost:8000
	docker run --rm -p 8000:8000 $(IMAGE)

clean:  ## Remove the virtual environment and caches
	rm -rf $(VENV) .pytest_cache **/__pycache__
