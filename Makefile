CYAN ?= \033[0;36m
COFF ?= \033[0m

.PHONY: deps lint check test help test_app
.EXPORT_ALL_VARIABLES:

.DEFAULT: help
help: ## Display help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(CYAN)%-30s$(COFF) %s\n", $$1, $$2}'

deps: ## Install dependencies
	@printf "$(CYAN)Updating python deps$(COFF)\n"
	pip3 install -U pip poetry
	@poetry install

lint: ## Lint the code
	@printf "$(CYAN)Auto-formatting with black$(COFF)\n"
	poetry run autoflake -ir basic_shopify_api tests
	poetry run isort basic_shopify_api tests
	poetry run black basic_shopify_api tests

check: ## Check code quality
	@printf "$(CYAN)Running static code analysis$(COFF)\n"
	poetry run flake8p basic_shopify_api tests
	poetry run black --check basic_shopify_api tests
	poetry run mypy basic_shopify_api tests --ignore-missing-imports
	poetry run run isort cli.py basic_shopify_api tests --check

test: ## Run the test suite
	@printf "$(CYAN)Running test suite$(COFF)\n"
	poetry run pytest
