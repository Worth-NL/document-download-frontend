SHELL := /bin/bash
DATE = $(shell date +%Y-%m-%d:%H:%M:%S)

APP_VERSION_FILE = app/version.py

GIT_BRANCH ?= $(shell git symbolic-ref --short HEAD 2> /dev/null || echo "detached")
GIT_COMMIT ?= $(shell git rev-parse HEAD)


## DEVELOPMENT

.PHONY: help
help:
	@cat $(MAKEFILE_LIST) | grep -E '^[a-zA-Z_-]+:.*?## .*$$' | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: run-flask
run-flask:
	FLASK_APP=application.py FLASK_DEBUG=1 flask run -p 7001

.PHONY: run-flask-with-docker
run-flask-with-docker: ## Run flask with docker
	FLASK_APP=application.py FLASK_DEBUG=1 ./scripts/run_locally_with_docker.sh web-local

.PHONY: test
test:
	ruff check .
	black --check .
	py.test tests/

.PHONY: test-with-docker
test-with-docker: ## Run tests in Docker container
	FLASK_APP=application.py FLASK_DEBUG=1 ./scripts/run_locally_with_docker.sh make test

.PHONY: bump-utils
bump-utils:  # Bump notifications-utils package to latest version
	python -c "from notifications_utils.version_tools import upgrade_version; upgrade_version()"

.PHONY: bootstrap
bootstrap: generate-version-file
	uv pip install -r requirements_for_test.txt
	source $(HOME)/.nvm/nvm.sh && nvm install && npm ci --no-audit && npm rebuild node-sass && npm run build


.PHONY: npm-audit
npm-audit:
	source $(HOME)/.nvm/nvm.sh && npm run audit

.PHONY: bootstrap-with-docker
bootstrap-with-docker: generate-version-file
	docker build -f docker/Dockerfile --target test -t document-download-frontend .

.PHONY: freeze-requirements
freeze-requirements: ## create static requirements.txt
	uv pip compile requirements.in -o requirements.txt
	uv pip sync requirements.txt
	python -c "from notifications_utils.version_tools import copy_config; copy_config()"
	uv pip compile requirements_for_test.in -o requirements_for_test.txt
	uv pip sync requirements_for_test.txt

.PHONY: generate-version-file
generate-version-file: ## Generates the app version file
	@echo -e "__git_commit__ = \"${GIT_COMMIT}\"\n__time__ = \"${DATE}\"" > ${APP_VERSION_FILE}
