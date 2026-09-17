# One command for every check a pull request must pass.
# The logic is in tools/checks/; see tools/checks/README.md.

PYTHON ?= python3

.DEFAULT_GOAL := help
.PHONY: help ci ci-docs ci-tooling doctor board-check rulesets-check rulesets-apply rulesets-apply-dry-run

help:
	@echo "make doctor      check this machine has the tools the checks need"
	@echo "make ci          run every check a pull request must pass"
	@echo "make ci-docs     run only the docs checks (the docs workflow)"
	@echo "make ci-tooling  run only the tooling checks (the tooling-tests workflow)"
	@echo "make board-check      check the live PolluxKart project board against stage labels"
	@echo "make rulesets-check           compare live GitHub branch rules with the files"
	@echo "make rulesets-apply-dry-run   print planned ruleset writes (admin login still needed to read)"
	@echo "make rulesets-apply           create or update GitHub branch rules (admin login)"
	@echo "                             pass RULESETS='development' to apply named rulesets"

ci:
	@$(PYTHON) tools/checks/checks.py

ci-docs:
	@$(PYTHON) tools/checks/checks.py --group docs

ci-tooling:
	@$(PYTHON) tools/checks/checks.py --group tooling

doctor:
	@$(PYTHON) tools/checks/doctor.py

board-check:
	@$(PYTHON) tools/board/check.py

rulesets-check:
	@$(PYTHON) tools/rulesets/rulesets.py check

rulesets-apply:
	@$(PYTHON) tools/rulesets/rulesets.py apply $(RULESETS)

rulesets-apply-dry-run:
	@$(PYTHON) tools/rulesets/rulesets.py apply --dry-run $(RULESETS)
