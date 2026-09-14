# E00-09 Complete the repository CLAUDE.md with commands and tooling

Parent: [low-level/](README.md) | Index: [docs/](../../README.md)

**Status: DRAFT (2026-09-14)**
Ticket: #39 (E00-09), part of epic #10.
Test plan: [../test/issue-39-claude-md-commands.md](../test/issue-39-claude-md-commands.md)
Depends on: #34 (the Makefile and `make ci`).

## Words used below

- **CLAUDE.md:** the instructions file at the repository root that AI agents read at the start of every task, and that contributors read first.
- **Make target:** a named recipe in the `Makefile`, run as `make <target>`.
- **`make help`:** the command that prints every target with a one-line description.
- **Help comment:** a `## description` written after a target's name in the Makefile, which `make help` prints.

## What was already decided before this document

- **Rule one, the Git rules and the writing rules in CLAUDE.md** (owner decisions, 2026-09-13, [decisions.md](../../platform/decisions.md)); this ticket does not change them.
- **`make ci` and `make doctor`, and their targets** (owner decision, 2026-09-14, "`make ci` and `make doctor`"). The #34 implementation already rewrites "Checks before a pull request" around them.
- **How CLAUDE.md lists commands** (owner decision, 2026-09-14, "Commands in CLAUDE.md", answered while planning this ticket):
  - only commands that exist today; each later ticket that adds a command adds it to CLAUDE.md itself;
  - CLAUDE.md keeps only everyday commands, and `make help` is the full list.

## The problem

- Once #34 lands, CLAUDE.md names a few commands, but nothing stops a later edit from naming a target that does not exist, and agents act on what CLAUDE.md says.
- The `make help` planned in #34 is a hand-written list, which can drift from the targets that really exist; the owner's answer makes it the full list, so it must be generated.
- docslint does not check CLAUDE.md at all today, so an em dash or broken link there goes unnoticed.

## The change

### A "Commands" section in CLAUDE.md

Placed after "Git", replacing nothing else.
At implementation time it holds only the commands that exist then:

```markdown
## Commands

- `make doctor`: check this machine has the tools; run once per machine and after installing tools.
- `make ci`: every check a pull request must pass; run before every pull request.
- `make help`: every other target, with what it does.
```

Later tickets add their own lines, for example #35 adds `git config core.hooksPath .githooks`, and E05-04 adds `make up`.
"Checks before a pull request" (rewritten by #34) stays a pointer to `make ci`.

### `make help` generated from the Makefile

Every target line in the Makefile gains a help comment, and `help` prints them:

```make
ci: ## run every check a pull request must pass
	@$(PYTHON) tools/checks/checks.py

help: ## list every target
	@$(PYTHON) tools/checks/make_help.py Makefile
```

`tools/checks/make_help.py` reads the Makefile, finds every `name: ## description` line, and prints them aligned, in file order.
It works with GNU Make 3.81 because Make only runs a Python script.

### The check (`tools/checks/test_claude_md.py`, run by `checks-tests`)

It fails, naming the problem, when:

1. CLAUDE.md contains `make <target>` (in inline code or a code block) and the Makefile does not define that target;
2. a target in the Makefile has no help comment, so `make help` would be incomplete;
3. a line of CLAUDE.md outside code blocks and tables holds two sentences (a full stop, question mark or exclamation mark followed by a space and a capital letter, ignoring common abbreviations such as "e.g.").

docslint gains `CLAUDE.md` in its list of extra files, so its links and em dashes are checked like the README's.

**Names in the code:** `make_targets(makefile_text)` returning target names with their help text, `claude_md_make_commands(text)`, `two_sentence_lines(text)`, and in `make_help.py`, `main(argv)`.

### Documents updated in the implementation pull request

- `CLAUDE.md`: the "Commands" section.
- `tools/checks/README.md`: every new target needs a help comment, and a new everyday command goes into CLAUDE.md in the same pull request.
- `tools/docslint/docslint.py` and its tests: `CLAUDE.md` added to the extra files.

## Edge cases and failure behaviour

| Situation | What happens |
|---|---|
| CLAUDE.md mentions `make up` before E05-04 adds it | The check fails, naming `up` |
| A target is renamed in the Makefile but not in CLAUDE.md | The check fails, naming the old name |
| A new target is added without a help comment | The check fails, naming the target |
| "make" appears in prose, such as "to make a change" | Not matched: only `make <target>` inside code formatting counts |
| A sentence with "e.g." or a version number like "3.81" | Not counted as two sentences |
| Rule one's wording | Not touched; the pull request diff is checked for it (test plan) |

## What is deliberately not covered

- **Planned commands:** the owner chose only existing ones.
- **A separate commands document:** `make help` is the full list.
- **Changes to rule one or the approval rules:** owned by E00-01 and reviewed by the owner.
- **One-sentence-per-line checks for the rest of the docs:** only CLAUDE.md is in this ticket's scope.

## Open questions for the owner

None open.
Both questions this ticket raised were answered on 2026-09-14 and are recorded in [decisions.md](../../platform/decisions.md), "Commands in CLAUDE.md".
