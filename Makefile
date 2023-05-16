SHELL := /bin/bash
DATE = $(shell date +%Y-%m-%d:%H:%M:%S)

APP_VERSION_FILE = app/version.py

GIT_BRANCH ?= $(shell git symbolic-ref --short HEAD 2> /dev/null || echo "detached")
GIT_COMMIT ?= $(shell git rev-parse HEAD)

CF_API ?= api.cloud.service.gov.uk
NOTIFY_CREDENTIALS ?= ~/.notify-credentials

CF_APP = document-download-frontend
CF_MANIFEST_PATH ?= /tmp/manifest.yml


## DEVELOPMENT

.PHONY: help
help:
	@cat $(MAKEFILE_LIST) | grep -E '^[a-zA-Z_-]+:.*?## .*$$' | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: run-flask
run-flask:
	FLASK_APP=application.py FLASK_DEBUG=1 flask run -p 7001

.PHONY: run-flask-with-docker
run-flask-with-docker: ## Run flask with docker
	./scripts/run_locally_with_docker.sh

.PHONY: test
test:
	ruff check .
	black --check .
	source $(HOME)/.nvm/nvm.sh && npm test
	pytest

.PHONY: bootstrap
bootstrap: generate-version-file
	pip3 install -r requirements_for_test.txt
	source $(HOME)/.nvm/nvm.sh && nvm install && npm ci --no-audit && npm rebuild node-sass && npm run build

.PHONY: npm-audit
npm-audit:
	source $(HOME)/.nvm/nvm.sh && npm run audit

.PHONY: bootstrap-with-docker
bootstrap-with-docker: generate-version-file
	docker build -f docker/Dockerfile -t document-download-frontend .

.PHONY: freeze-requirements
freeze-requirements: ## create static requirements.txt
	pip install --upgrade pip-tools
	pip-compile requirements.in

## DEPLOYMENT

.PHONY: preview
preview:
	$(eval export CF_SPACE=preview)
	$(eval export DNS_NAME=documents.notify.works)
	cf target -s ${CF_SPACE}

.PHONY: staging
staging:
	$(eval export CF_SPACE=staging)
	$(eval export DNS_NAME=documents.staging-notify.works)
	cf target -s ${CF_SPACE}

.PHONY: production
production:
	$(eval export CF_SPACE=production)
	$(eval export DNS_NAME=documents.service.gov.uk)
	cf target -s ${CF_SPACE}

.PHONY: generate-manifest
generate-manifest:
	$(if ${CF_SPACE},,$(error Must specify CF_SPACE))

	$(if $(shell which gpg2), $(eval export GPG=gpg2), $(eval export GPG=gpg))
	$(if ${GPG_PASSPHRASE_TXT}, $(eval export DECRYPT_CMD=echo -n $$$${GPG_PASSPHRASE_TXT} | ${GPG} --quiet --batch --passphrase-fd 0 --pinentry-mode loopback -d), $(eval export DECRYPT_CMD=${GPG} --quiet --batch -d))

	@jinja2 --strict manifest.yml.j2 \
	    -D environment=${CF_SPACE} --format=yaml \
	    <(${DECRYPT_CMD} ${NOTIFY_CREDENTIALS}/credentials/${CF_SPACE}/paas/environment-variables.gpg) 2>&1

.PHONY: cf-login
cf-login: ## Log in to Cloud Foundry
	$(if ${CF_USERNAME},,$(error Must specify CF_USERNAME))
	$(if ${CF_PASSWORD},,$(error Must specify CF_PASSWORD))
	$(if ${CF_SPACE},,$(error Must specify CF_SPACE))
	@echo "Logging in to Cloud Foundry on ${CF_API}"
	@cf login -a "${CF_API}" -u ${CF_USERNAME} -p "${CF_PASSWORD}" -o "${CF_ORG}" -s "${CF_SPACE}"

.PHONY: cf-deploy
cf-deploy: ## Deploys the app to Cloud Foundry
	$(if ${CF_SPACE},,$(error Must specify CF_SPACE))
	@cf app --guid ${CF_APP} || exit 1

	# cancel any existing deploys to ensure we can apply manifest (if a deploy is in progress you'll see ScaleDisabledDuringDeployment)
	cf cancel-deployment ${CF_APP} || true
	# generate manifest (including secrets) and write it to CF_MANIFEST_PATH (in /tmp/)
	make -s CF_APP=${CF_APP} generate-manifest > ${CF_MANIFEST_PATH}
	# reads manifest from CF_MANIFEST_PATH
	cf push ${CF_APP} --strategy=rolling -f ${CF_MANIFEST_PATH}
	# delete old manifest file
	rm ${CF_MANIFEST_PATH}

.PHONY: cf-rollback
cf-rollback: ## Rollbacks the app to the previous release
	cf cancel-deployment ${CF_APP}
	rm -f ${CF_MANIFEST_PATH}

.PHONY: cf-create-cdn-route
cf-create-cdn-route:
	$(if ${CF_SPACE},,$(error Must specify CF_SPACE))
	$(if ${DNS_NAME},,$(error Must specify DNS_NAME))
	cf create-service cdn-route cdn-route document-download-cdn-route -c '{"domain": "${DNS_NAME}"}'

.PHONY: generate-version-file
generate-version-file: ## Generates the app version file
	@echo -e "__git_commit__ = \"${GIT_COMMIT}\"\n__time__ = \"${DATE}\"" > ${APP_VERSION_FILE}
