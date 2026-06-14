# Manufacturing Operations Intelligence - common commands
#
# Override the interpreter if needed, e.g.:  make run PYTHON=.venv/bin/python

PYTHON ?= python

.PHONY: help setup run validate data clean

help:
	@echo "Targets:"
	@echo "  make setup     Install Python dependencies"
	@echo "  make run       Run the full analytics pipeline"
	@echo "  make validate  Check that all expected outputs exist and are valid"
	@echo "  make data      Regenerate the synthetic dataset only"
	@echo "  make clean     Remove generated tables, charts, and web exports"

setup:
	$(PYTHON) -m pip install -r requirements.txt

run:
	$(PYTHON) src/run_pipeline.py

validate:
	$(PYTHON) src/validate_outputs.py

data:
	$(PYTHON) src/generate_data.py

clean:
	rm -f outputs/tables/*.csv
	rm -f outputs/charts/*.png
	rm -f data/web_exports/*.json
	@echo "Removed generated tables, charts, and web exports."
