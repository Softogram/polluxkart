# One command for every check a pull request must pass.
# The logic is in tools/checks/; see tools/checks/README.md.

PYTHON ?= python3

.DEFAULT_GOAL := help
.PHONY: help ci ci-docs ci-tooling doctor

help:
	@echo "make doctor      check this machine has the tools the checks need"
	@echo "make ci          run every check a pull request must pass"
	@echo "make ci-docs     run only the docs checks (the docs workflow)"
	@echo "make ci-tooling  run only the tooling checks (the tooling-tests workflow)"

ci:
	@$(PYTHON) tools/checks/checks.py

ci-docs:
	@$(PYTHON) tools/checks/checks.py --group docs

ci-tooling:
	@$(PYTHON) tools/checks/checks.py --group tooling

doctor:
	@$(PYTHON) tools/checks/doctor.py
