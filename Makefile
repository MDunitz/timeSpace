VENV := /tmp/ts-build-test
DIST := dist

.PHONY: help build test test-package build-docs clean lint publish-test publish

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

build:  ## Build sdist and wheel
	@untracked=$$(git ls-files --others --exclude-standard data/local_data/*.csv 2>/dev/null | wc -l | tr -d ' '); \
	if [ "$$untracked" -gt 0 ]; then \
		echo "WARNING: $$untracked untracked CSVs in data/local_data/ will be included in the build."; \
		echo "Run 'git clean -n data/local_data/' to see them."; \
		echo "Run 'git clean -f data/local_data/' to remove them before building."; \
		echo ""; \
	fi
	pip install build
	python -m build
	@echo ""
	@echo "Built:"
	@ls -lh $(DIST)/timespace-*.tar.gz $(DIST)/timespace-*.whl
	@echo ""
	@echo "sdist CSV check:"
	@tar tzf $(DIST)/timespace-*.tar.gz | grep '\.csv$$' | wc -l | xargs echo "  CSVs:"
	@echo ""
	@echo "Run 'make test-package' to install and verify."

test:  ## Run pytest in current environment
	python -m pytest tests/ -v

lint:  ## Run black + flake8
	black --check .
	flake8 .

test-package: build  ## Build, install in clean venv, run smoke test
	rm -rf $(VENV)
	python -m venv $(VENV)
	$(VENV)/bin/pip install -q $(DIST)/timespace-*.tar.gz
	$(VENV)/bin/python tests/test_local_install.py
	@echo ""
	@echo "Run the test suite against installed package:"
	$(VENV)/bin/pip install -q pytest
	cd /tmp && $(VENV)/bin/python -m pytest $(CURDIR)/tests/ -v
	@echo ""
	@echo "Package is ready. Run 'make publish-test' for TestPyPI or 'make publish' for PyPI."

build-docs:  ## Regenerate all docs/*.html from build scripts
	python docs/build_desert_farm.py
	python docs/build_desert_farm_summary.py
	python docs/build_explorer.py
	@echo ""
	@echo "Regenerated:"
	@echo "  docs/desert_farm_stommel.html"
	@echo "  docs/desert_farm_summary.html"
	@echo "  docs/explorer.html"

publish-test: build  ## Upload to TestPyPI
	pip install twine
	twine check $(DIST)/*
	twine upload --repository testpypi $(DIST)/*
	@echo ""
	@echo "Test install with:"
	@echo "  pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ timeSpace"

publish: build  ## Upload to PyPI (production)
	pip install twine
	twine check $(DIST)/*
	@echo ""
	@echo "About to upload to PRODUCTION PyPI. Press Ctrl+C to cancel."
	@read -p "Continue? [y/N] " confirm && [ "$$confirm" = "y" ] || exit 1
	twine upload $(DIST)/*
	@echo ""
	@echo "Published! Test with: pip install timeSpace"

clean:  ## Remove build artifacts and test venv
	rm -rf $(DIST) build *.egg-info $(VENV) test_stommel.html
