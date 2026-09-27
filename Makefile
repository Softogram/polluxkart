# One command for every check a pull request must pass.
# The logic is in tools/checks/; see tools/checks/README.md.
#
# Every target describes itself with a "## " comment, and make help prints
# them. A target without one fails the checks, so the list cannot go stale.

PYTHON ?= python3

.DEFAULT_GOAL := help
.PHONY: help ci ci-docs ci-tooling doctor board-check rulesets-check rulesets-apply rulesets-apply-dry-run

help: ## list every target
	@$(PYTHON) tools/checks/make_help.py Makefile

doctor: ## check this machine has the tools the checks need
	@$(PYTHON) tools/checks/doctor.py

ci: ## run every check a pull request must pass
	@$(PYTHON) tools/checks/checks.py

ci-docs: ## run only the docs checks (the docs workflow)
	@$(PYTHON) tools/checks/checks.py --group docs

ci-tooling: ## run only the tooling checks (the tooling-tests workflow)
	@$(PYTHON) tools/checks/checks.py --group tooling

board-check: ## check the live PolluxKart project board against stage labels
	@$(PYTHON) tools/board/check.py

rulesets-check: ## compare live GitHub branch rules with the files
	@$(PYTHON) tools/rulesets/rulesets.py check

rulesets-apply: ## create or update GitHub branch rules (admin login)
## pass RULESETS='development' to apply only the rulesets named
	@$(PYTHON) tools/rulesets/rulesets.py apply $(RULESETS)

rulesets-apply-dry-run: ## print the planned ruleset writes and change nothing
	@$(PYTHON) tools/rulesets/rulesets.py apply --dry-run $(RULESETS)
