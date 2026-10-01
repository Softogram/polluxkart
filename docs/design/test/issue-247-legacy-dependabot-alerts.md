# Test plan: E00-14 Stop the `legacy/` Dependabot alerts at the source

Parent: [test/](README.md) | Index: [docs/](../../README.md)

**Status: DRAFT (2026-10-01)**
Ticket: #247 (E00-14), part of epic #10.
Design: [../low-level/issue-247-legacy-dependabot-alerts.md](../low-level/issue-247-legacy-dependabot-alerts.md)

## Words used below

The design document defines every term used here.
The three that matter most for the tests:

- **Alert:** a warning in the Security tab. Produced by GitHub, not by anything in this repository.
- **Auto-triage rule:** the setting that closes matching alerts automatically. Created by hand by the owner; there is no API for it.
- **Auto-dismissed:** the resolution GitHub records on an alert a rule closed, as opposed to one a person closed.

## How these tests run

This ticket is unusual, and the test plan has to be honest about why.

Most of what it changes is not code.
The main change is a setting inside GitHub that no file in this repository can describe and no command can create or read directly.
So the automated tests cover only the file that may change, `.github/dependabot.yml`, and everything else is a short list of read-only commands run against the live repository, in a stated order, with the expected output written down in advance.

That is weaker than a unit test and it should be treated as weaker.
It is made as strong as it can be in two ways.
Every live check reads the **result** (the alerts) rather than the **setting** (the rule), because a rule that exists and a rule that works are different things and only one of them matters.
And every check has a stated failing output as well as a passing one, so "I ran it and it looked fine" is not available as an answer.

The automated part runs inside `make ci`, through `python3 -m unittest discover -s tools/checks`.

## Flow 1: `.github/dependabot.yml` (unit tests, only if open question 2 is answered (a))

If the owner chooses to watch first, this flow does not exist and nothing in `tools/` changes.
It is planned here so the choice does not need re-planning later.

The rules in `tools/checks/test_workflow_pins.py::DependabotTest` change in one way only: an entry may leave `target-branch` out, because GitHub ignores the settings of any entry that names one when raising a security pull request.

**Happy path.** The real `.github/dependabot.yml`, with the `github-actions` entry unchanged and a `pip` entry for `/legacy/backend` that has no `target-branch`, an `ignore` of `dependency-name: "*"` and a group, produces no problems.

**Error paths that matter.** Each one is a test that must still fail after the rule is relaxed, because the risk of relaxing a rule is relaxing more than intended:

| What the test feeds in | What must still be reported | Why it matters |
|---|---|---|
| An entry with `target-branch: main` | `must target development` | The original purpose of the rule. Relaxing it must not let a pull request aim at the release branch. |
| An entry with no `groups` block | `must group its updates` | AC9. |
| An entry with `auto-merge` or `automerge` | `must not auto-merge` | Nothing merges itself. |
| An entry with `open-pull-requests-limit: 0` | `must not stop updates being proposed` | Unchanged, and it would not have worked anyway: security pull requests ignore that limit. |
| A `maven` entry with no major-version ignore | `must ignore major updates` | Unchanged for the ecosystems that ship real code. |
| A `github-actions` entry that ignores majors | `must still propose major updates` | Unchanged. |
| An entry whose `directory` does not exist | `points at ..., which does not exist` | Catches `/legacy/backend` being written as `/legacy/backend/` or misspelled. |

**The test that is easy to forget.** `test_d2_1_the_real_file_passes` asserts the file holds exactly one entry.
Adding a second entry fails it, and the fix is to assert the real shape of both entries rather than to delete the assertion.
A test that stops counting entries stops noticing an entry nobody meant to add.

**Fixtures.** None. The existing tests build configuration dictionaries in memory; the new ones follow that.

## Flow 2: the rule works (live, read-only, in rollout order)

Run in this order, because each step's expected output depends on the one before.

**Step 0, before the rule exists.** Record the starting point:

```
gh api repos/Softogram/polluxkart/dependabot/alerts --paginate \
  --jq '[.[] | select(.state=="open")] | length'
```

Expected: `13` on 2026-10-01. If it is not 13, record what it is and carry that number forward.

**Step 1, the owner creates the rule.** Both manifest paths, dismiss indefinitely.

**Step 2, the existing alerts close by themselves.** Within minutes, re-run step 0's command.

Expected: `0`.
Failing output: still `13`, which almost always means the rule was written with a wildcard. Check it against the exact paths in the design.

**Step 3, they closed the right way.** A rule closing an alert and a person closing one look different, and only the first proves the rule fired:

```
gh api repos/Softogram/polluxkart/dependabot/alerts --paginate \
  --jq '[.[] | select(.auto_dismissed_at != null)] | length'
```

Expected: `13`, rising over time.
Failing output: `0` with 0 open alerts, which would mean somebody closed them by hand, which is the thing this ticket exists to stop.

**Step 4, the 49 earlier dismissals are untouched.** AC5:

```
gh api repos/Softogram/polluxkart/dependabot/alerts --paginate \
  --jq '[.[] | select(.state=="dismissed" and .auto_dismissed_at == null)] | length'
```

Expected: `49`, unchanged before and after.

**Step 5, a new alert is handled with nobody present.** This cannot be forced; it is waited for.
The next advisory against any of the 162 libraries in `legacy/` produces an alert, and the check is that it never appears in the Open list.
Re-run steps 2 and 3 after a fortnight: open stays `0`, the auto-dismissed count has gone up.
This is AC1, and it is the acceptance criterion that actually matters, because it is the only one that proves the weekly work is gone rather than paused.

## Flow 3: the update pull requests stop (live, a measurement rather than a test)

This flow is the evidence that decides open question 2, so it is run whichever option the owner picks.

**The measurement.** For a fortnight after the rule exists, list Dependabot's open pull requests:

```
gh pr list --repo Softogram/polluxkart --author app/dependabot \
  --json number,title,files --jq '.[] | "\(.number) \(.title)"'
```

Expected if the rule is enough on its own: no new pull request touching anything under `legacy/`.
Expected if it is not: at least one, and open question 2 is then answered (a) and Flow 1 is built.

**Why this is worth a fortnight.** GitHub's rule form says Dependabot opens pull requests "to resolve open alerts", and an auto-dismissed alert is not open.
That strongly suggests the pull requests stop by themselves, but it is a reading of one sentence of interface text, not a documented guarantee.
Watching costs a fortnight. Guessing costs a permanent weakening of a test rule that may never have been needed.

**The failing case that is not a failure.** A `github-actions` pull request appearing during the fortnight is expected and correct. Only `legacy/` paths count.

## Flow 4: nothing outside `legacy/` is affected (deferred, and the most important one)

This is the check that stops the ticket quietly doing harm, and it cannot be run today because every dependency file in the repository is currently inside `legacy/`.

**When it runs.** The first time `api/` or `web/` gains a dependency file, which is E03-02 (#56) and E04-01.

**What it checks.** When the first alert is raised against `api/` or `web/`, it appears in the Open list and stays there:

```
gh api repos/Softogram/polluxkart/dependabot/alerts --paginate \
  --jq '.[] | select(.state=="open") | "\(.dependency.manifest_path)"' | sort -u
```

Expected: paths outside `legacy/` appear; paths inside it do not.
Failing output: a path outside `legacy/` missing from the open list while present in the auto-dismissed list, which would mean the rule matches more than it should.

**Why it is deferred rather than dropped.** A rule that silences real code is a far worse outcome than the problem being fixed, and it would be invisible: the symptom is an alert that never arrives.
The exact-path matching confirmed in the design makes it unlikely, which is a reason to check it once rather than a reason to skip it.
This step is written into the acceptance criteria as AC3 and into [runbook.md](../../platform/runbook.md), so the ticket that creates the first real dependency file inherits it.

## Flow 5: the setting is still there, months later (the runbook check)

A setting nobody can see from the code is a setting that disappears without anyone noticing.

The runbook gets one read-only command, the same one as Flow 2 step 2, and one sentence saying what a non-zero answer means: either a real alert that needs reading, or a rule that has been deleted, disabled or outlived a GitHub change.
Both are things the owner wants to know, which is why the check reads the alerts rather than the settings page.

Reviewing security also means reading what was hidden, so the runbook names the filter for it: `resolution:auto-dismissed` on the alerts page.

## Acceptance criteria and the tests that prove them

| Criterion | Proved by |
|---|---|
| AC1: a new `legacy/` alert closes itself, with `auto_dismissed_at` set | Flow 2, steps 3 and 5 |
| AC2: 0 open alerts, closed by the rule rather than by hand | Flow 2, steps 2 and 3 |
| AC3: an alert outside `legacy/` is not affected | Flow 4, deferred to the first `api/` or `web/` dependency file |
| AC4: no new update pull request for `legacy/` over a fortnight | Flow 3 |
| AC5: the 49 hand-dismissed alerts are untouched | Flow 2, step 4 |
| AC6: `make ci` green, including `test_workflow_pins.py` | Flow 1, run by `make ci` |
| AC7: the rule is written down in `security.md` | Read in review of the implementation pull request |
| AC8: the runbook says how to confirm it still works | Flow 5 |
| AC9: the relaxed test still refuses a dropped group, auto-merge or `main` | Flow 1, the error-path table |

## What the owner gets when a dependency fails

The dependency here is GitHub itself, and the failures are quiet rather than loud.

- **The rule stops matching,** because GitHub changed how matching works or the feature was withdrawn. Alerts return to the Open list. Nothing is lost, nothing breaks, and the position is the one the repository is in today. Found by Flow 5.
- **The alerts API is unreachable** when a check is run. `gh` prints the HTTP error and the check is re-run later. No state depends on it.
- **GitHub stops producing alerts for `legacy/` for its own reasons,** for example because the advisory database changed. Indistinguishable from the rule working, and harmless either way, because the only thing at stake is reference code.
- **The owner's login loses the rights to edit the setting.** The rule keeps working; only changing it is blocked. Noticed when a change is next needed.

## Reachability check

There is one write in this ticket, and it is not a database row: the rule itself.

- **The real action that causes it:** the owner creating it in Settings, Advanced Security, Dependabot rules.
- **The read-back:** Flow 2, steps 2 and 3, which read the alerts rather than the settings page, because the settings page proves only that something was typed.

If open question 2 is answered (a), the second write is the new entry in `.github/dependabot.yml`, read back by Flow 1 parsing the real file rather than a fixture, which `test_d2_1_the_real_file_passes` already does.

## What is deliberately not covered, and why

- **Creating a rule in a test to see what it matches.** There is no API, so a test cannot create one, and creating one by hand to test it would change the live repository's security settings. The wildcard question was answered instead by querying the alerts page with both filters and comparing the counts, which needed no write at all.
- **Proving that an auto-dismissed alert never produces a security pull request.** It is undocumented, so it is measured over a fortnight in Flow 3 rather than asserted.
- **Testing GitHub's dependency graph.** Not ours to test.
- **Load, performance and concurrency.** No request path, no money, no stock, no counters.
- **The 13 currently open alerts individually.** They are counted, not read one by one. Their contents are already recorded in the ticket, and they are in code that is never deployed.
- **Any automated check that the rule still exists.** There is no API to ask. Flow 5 infers it from the alerts, which is the best available and is also the thing actually worth knowing.
