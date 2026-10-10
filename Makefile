PYTHON ?= python3
ARGS ?=

.PHONY: run test vfs

run:
	PYTHONPATH=src $(PYTHON) -m emulator $(ARGS)

test:
	PYTHONPATH=src $(PYTHON) -m unittest discover -s tests -v

vfs:
	$(PYTHON) tools/make_vfs.py
