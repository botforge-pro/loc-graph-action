.PHONY: install test lint

venv:  ## Create virtual environment
	python3 -m venv venv

install: venv  ## Install dependencies
	./venv/bin/pip install pytest ruff

test:  ## Run tests
	./venv/bin/python -m pytest test_loc_graph.py -v

lint:  ## Run linter
	./venv/bin/ruff check scripts/loc_graph.py

lint-fix:  ## Run linter with auto-fix
	./venv/bin/ruff check scripts/loc_graph.py --fix

run:  ## Run the script locally (for testing)
	THEME=dark python3 scripts/loc_graph.py

all: lint test  ## Run lint and test