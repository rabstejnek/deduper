.PHONY: clean lint format test coverage build build-posit
.DEFAULT_GOAL := help

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

help:
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

clean: ## Remove build artifacts
	@rm -rf build/
	@rm -rf dist/

lint:  ## Check formatting issues
	@ruff format . --check && ruff .

format:  ## Fix formatting issues (where possible)
	@ruff format . && ruff . --fix --show-fixes

test:  ## Run tests
	@py.test

coverage: ## Generate coverage report
	@coverage run -m pytest
	@coverage html

build: clean ## Build python wheel package
	@flit build
	@ls -l dist

build-posit:  ## Build manifest for Posit Connect
	rsconnect write-manifest shiny --overwrite --entrypoint=deduper.app .
	python bin/clean_manifest.py