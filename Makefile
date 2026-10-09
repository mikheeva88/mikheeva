PYTHON ?= python3
ARGS ?=

.PHONY: run test

run:
	PYTHONPATH=src $(PYTHON) -m emulator $(ARGS)

test:
	PYTHONPATH=src $(PYTHON) -m unittest discover -s tests -v
