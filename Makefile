.PHONY: install test lint clean

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

clean:  ## Clean cache files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

run:  ## Run the script locally (for testing)
	THEME=dark python3 scripts/loc_graph.py

all: lint test  ## Run lint and test