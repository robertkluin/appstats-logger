SHELL := /bin/bash
PYTHON := python
PIP := pip

BUILD_DIR := .build
TOOLS_DIR := .tools

clean:
	find . -name "*.py[co]" -delete

distclean: clean
	rm -rf $(BUILD_DIR)

run: deps
	dev_appserver.py . --use_sqlite

deps: py_deploy_deps py_dev_deps

py_deploy_deps: $(BUILD_DIR)/pip-deploy.log

py_dev_deps: $(BUILD_DIR)/pip-dev.log

$(BUILD_DIR)/pip-deploy.log: requirements.txt
	@mkdir -p .build
	$(PIP) install -Ur requirements.txt | tee $(BUILD_DIR)/pip-deploy.log
	$(PYTHON) $(TOOLS_DIR)/link_libs.py

$(BUILD_DIR)/pip-dev.log: requirements_dev.txt
	@mkdir -p .build
	$(PIP) install -Ur requirements_dev.txt | tee $(BUILD_DIR)/pip-dev.log

unit:
	nosetests

integrations:
	nosetests --logging-level=ERROR -a slow

test: clean integrations

