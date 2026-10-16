.PHONY: venv install run tui demo test lint clean export

VENV=.venv
PY=$(VENV)/bin/python
PIP=$(VENV)/bin/pip

venv:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip

install: venv
	$(PIP) install -e ".[dev]"

run:
	$(PY) main.py $(ARGS)

tui:
	$(PY) main.py

demo:
	$(PY) main.py seed
	$(PY) main.py list
	$(PY) main.py export --output ADR_LOG.md

test:
	$(VENV)/bin/pytest -v

clean:
	rm -f adr_buffer.db ADR_LOG.md
	rm -rf __pycache__ .pytest_cache *.egg-info build dist
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

export:
	$(PY) main.py export --output ADR_LOG.md
