# E00-14 Stop the `legacy/` Dependabot alerts at the source

Parent: [low-level/](README.md) | Index: [docs/](../../README.md)

**Status: DRAFT (2026-10-01)**
Ticket: #247 (E00-14), part of epic #10.
Test plan: [../test/issue-247-legacy-dependabot-alerts.md](../test/issue-247-legacy-dependabot-alerts.md)
Depends on: nothing. One step needs the owner's own login, because GitHub offers no other way to do it.

## Words used below

- **Dependency:** a library the code uses but did not write, such as `urllib3` or React.
- **Dependency file:** the file that lists those libraries, such as `requirements.txt` for Python or `package.json` for npm. GitHub calls it a **manifest**.
- **Dependabot:** GitHub's own bot that watches those libraries.
- **Dependency graph:** GitHub's own reading of every dependency file in a repository. It is a GitHub service, not a file anyone checks in.
- **Dependabot alert:** a warning in the repository's Security tab saying a listed library has a known vulnerability. Alerts are produced from the dependency graph.
- **Version update pull request:** the scheduled pull request Dependabot opens to move a library to a newer version. Shaped by `.github/dependabot.yml`.
- **Security update pull request:** the pull request Dependabot opens because of an alert. Also opened by Dependabot, but triggered by the alert rather than by the schedule.
- **Auto-triage rule:** a rule in a repository's settings that closes or reopens matching alerts automatically, with no person involved.
- **Auto-dismissed:** the resolution GitHub records on an alert that a rule closed. It is a separate resolution from a dismissal by a person, and it is hidden from the default Open list.
- **`legacy/`:** the first version of the store, kept in this repository as reading material for the rebuild and never deployed.

## What was already decided before this document

- **Dependabot is configured so `legacy/` stops producing alerts and update pull requests**, instead of each alert being dismissed by hand (owner decision, 2026-10-01, [decisions.md](../../platform/decisions.md), "Dependabot alerts from `legacy/` are stopped at the source").
  Also offered then: keep dismissing them with a dated reason as they arrive, or delete `legacy/` now.
- **Deleting `legacy/` was not chosen now**, because the rebuild still reads from it (same entry). It stays available for when it no longer does.
- **That same entry says which GitHub setting does the job is not decided and must be confirmed on GitHub rather than assumed.** This document is that confirmation.
- **The first version is kept only as reference and is never deployed** (owner decision, 2026-09-13, "Rebuild from scratch, keep the first version as reference").
- **Dependabot security updates are switched on** (owner decision, 2026-09-14, "Dependabot and CodeQL").
- **Alerts from `legacy/` are dismissed with a dated reason, and future ones are auto-dismissed where GitHub allows** (owner decision, 2026-09-14, same entry, revised 2026-10-01). This document settles what "where GitHub allows" turns out to mean.
- **CodeQL skips `legacy/`** (owner decision, 2026-09-14, same entry).
- **An agent may merge a Dependabot pull request once every required check is green**, after running `make ci` on its branch by hand until #245 ships (owner decision, 2026-09-23, corrected 2026-09-29).

## The problem

On 2026-10-01 the repository had 13 open Dependabot alerts.
One critical, four high, eight medium.
Every one of them was in `legacy/backend/requirements.txt`, across three libraries: `pyjwt`, `urllib3` and `oauthlib`.

Forty nine alerts on the same file had already been closed by hand, each carrying a dated reason saying the code is never deployed.
Then thirteen more arrived.

Two security update pull requests were open at the same time, #243 and #244, and both touched only that one file.
They exist even though `.github/dependabot.yml` configures only `github-actions` for the root folder, because security update pull requests are triggered by an alert rather than by the configuration file.

So the work repeats itself every week, and none of it is about code that will ship.
The real cost is not the minutes. It is that a Security tab which always reads "13 open" is a Security tab nobody looks at, so the first alert that matters will be missed.

## What was confirmed on GitHub, and how

Everything below was checked on 2026-10-01 against this repository and GitHub's current documentation.
Each line names the check that produced it, so a later reader can run the same check rather than trusting this document.

### 1. No file in this repository can stop an alert being raised

Alerts come from the dependency graph, which reads the dependency files and compares them with GitHub's advisory database.
`.github/dependabot.yml` shapes pull requests only.
There is no path exclusion, no ignore list and no equivalent of CodeQL's `paths-ignore` for alerts.

This is the single most important finding, because it is the one most likely to be assumed the other way.
`.github/codeql/codeql-config.yml` already excludes `legacy/**` with exactly that kind of wildcard, which makes it natural to expect Dependabot to work the same way.
It does not.

### 2. An auto-triage rule is the only mechanism that reaches alerts by path

The rule form is live for this repository at Settings, Advanced Security, Dependabot rules, New rule.
Custom rules are available here because the repository is public.

The form has three parts: a name, a "Target alerts" box, and the actions.
The "Target alerts" box takes filter words rather than free text, and `manifest:` is one of them.
GitHub's documentation lists what a rule can match on: "CVE ID, CWE, Dependency scope (`devDependency` or `runtime`), Ecosystem, GHSA ID, Manifest path (for repository-level rules only), Package name, Patch availability, Severity, EPSS Score".

Manifest path is in that list, which is what makes this ticket possible.
Note the condition attached to it: repository-level rules only, not organisation-level ones.

### 3. The path must be written out in full. A wildcard does not match

This was tested directly, using the same filter vocabulary on the repository's own alerts page:

| Filter | Open | Closed |
|---|---|---|
| `is:open manifest:legacy/backend/requirements.txt` | 13 | 49 |
| `is:open manifest:legacy/*` | 0 | 0 |

The exact path matches every alert. The wildcard matches nothing at all.

This is the trap in the whole ticket.
A rule written as `manifest:legacy/*`, which is the obvious thing to write, would be accepted by the form, would look correct in the settings list, and would silently never fire.
Nobody would notice, because the symptom of a rule that does not fire is identical to having no rule: alerts keep arriving.

### 4. There is no API for creating a rule, so the owner creates it by hand

Four candidate REST endpoints were tried and all four returned 404:
`repos/{owner}/{repo}/dependabot/alert-rules`, `repos/{owner}/{repo}/dependabot/rules`, `repos/{owner}/{repo}/dependabot/auto-triage-rules` and `orgs/{org}/dependabot/rules`.

GitHub's GraphQL schema was then read directly.
It carries 1835 types, and none of them mentions triage or a Dependabot rule; the only Dependabot types are `DependabotUpdate` and `DependabotUpdateError`.
The `Mutation` type has no field mentioning Dependabot or triage at all.

So the rule cannot be written down in this repository, generated by a script, or applied by `make`.
It is a setting a person clicks, and the only person with the rights is the owner.
This is the same shape as the ruleset step in #245, and it carries the same risk: a setting nobody can see from the code is a setting that gets lost.
That is why this ticket writes the rule down in [security.md](../../platform/security.md) and gives the runbook a way to check it is still there.

### 5. A rule does not prevent an alert. It closes one

This matters for how the owner's decision is read, so it should be said plainly.

The alert is still raised. GitHub then applies the rule and closes it, recording the resolution `auto-dismissed`.
That resolution is excluded from the default Open view, and the alerts page offers `resolution:auto-dismissed` to find them.

The practical result is what the owner asked for: nobody touches an alert again, and the Open count stays at zero.
The literal result is not: alerts are still produced, they are just closed the moment they appear.
Open question 1 puts that difference to the owner rather than deciding it here.

The close is visible from the command line, which is what the test plan leans on.
A dismissal by a person and a dismissal by a rule look different in the alerts API.
Alert 102, dismissed by hand on 2026-09-27, reports `auto_dismissed_at: null` with a named person in `dismissed_by`.
An alert closed by a rule reports a timestamp in `auto_dismissed_at` instead.

### 6. Stopping the update pull requests is a separate change, in a separate place

An `ignore` entry in `.github/dependabot.yml` does affect security update pull requests, not only scheduled ones.
GitHub's options reference marks each option that carries over, with the legend: "All options marked with [the shield icon] also change how Dependabot creates pull requests for security updates, except where `target-branch` is used."
`ignore` carries that marker. So does `allow`. `open-pull-requests-limit`, `registries` and `target-branch` do not.

One detail inside `ignore` matters.
An ignore written with `update-types` affects scheduled updates only, which is why the existing major-version ignore in `tools/checks/README.md` correctly says security updates pass through it.
An ignore written with `dependency-name` and no `update-types` is the one that reaches security updates.

### 7. The catch: `target-branch` disables exactly that

GitHub's documentation on `target-branch` is explicit: "When you use this option, the settings for this package manager will no longer affect any pull requests raised for security updates."
Security update pull requests always target the default branch, so an entry that names a branch is treated as a scheduled-updates-only entry.

Every entry in this repository sets `target-branch: development`, and `tools/checks/test_workflow_pins.py` fails any entry that does not:

```
if entry.get("target-branch") != "development":
    problems.append("%s must target development" % where)
```

So the repository's own test, as written today, forbids the one entry shape that would work.
The rule was written for a good reason and should not be dropped casually.
Its purpose is that a Dependabot pull request never aims at `main`, and that purpose survives leaving `target-branch` out, because the default branch of this repository is `development` anyway, confirmed live.
What changes is only whether the key is written down.

Two further facts about the same test:

- `test_d2_1_the_real_file_passes` asserts the file holds exactly one entry, so adding any second entry fails it.
- The same check refuses `open-pull-requests-limit: 0`, which would not have helped regardless: GitHub's documentation says "Security update pull requests are not subject to this limit and do not count toward it."

Open question 2 puts the choice to the owner.

### 8. Deleting the files does clear the alerts, which is why the deletion option stays real

The alerts API still holds 44 alerts recorded against the path `backend/requirements.txt`, the location of that file before the rebuild moved it into `legacy/`.
All 44 are in state `fixed`.
Nobody fixed anything. The file moved, so the alerts resolved themselves.

This is recorded here as evidence for the option the owner kept on the table, not as a proposal to take it now.

### 9. Both dependency files in this repository are inside `legacy/`, and both are live in the dependency graph

The dependency graph currently holds 93 Python packages, 69 npm packages and 4 GitHub Actions.
The Python packages come from `legacy/backend/requirements.txt` and the npm packages from `legacy/frontend/package.json`.

`legacy/frontend/package.json` has produced no alert so far.
That is luck rather than design: 69 npm packages pinned with `^` ranges from the first version will eventually produce one.
So the rule names both files, or it solves half the problem and the other half arrives later looking like a new bug.

### 10. CodeQL needs nothing from this ticket

`.github/codeql/codeql-config.yml` already carries `paths-ignore: legacy/**`, so code scanning findings from the first version are never produced.
The handoff into this session listed "the same treatment for CodeQL" as a possible question for the owner.
It is not a question. It is already done, and the record answers it.

## The change

### Part 1: the auto-triage rule, created by the owner

One rule, in Settings, Advanced Security, Dependabot rules:

| Field | Value |
|---|---|
| Rule name | `legacy reference code` |
| State | Enabled |
| Target alerts | `manifest:legacy/backend/requirements.txt` and `manifest:legacy/frontend/package.json` |
| Rule | Dismiss alerts, **Indefinitely** |

"Indefinitely" rather than "Until patch is available".
"Until patch is available" reopens the alert as soon as a fix exists, which is precisely the weekly noise being removed, and a fix is irrelevant to code that is never deployed.

The "Open a pull request to resolve alerts" action is checked and greyed out in the form, with the note "Dependabot will always try to open a pull request to resolve open alerts when security updates are enabled".
That action therefore cannot be used while the 2026-09-14 decision to keep security updates switched on stands, and this ticket does not propose changing that decision.
Read the wording carefully, though: it says **open** alerts.
An auto-dismissed alert is not open, which is the reason open question 2 proposes watching before changing any file.

### Part 2: the update pull requests

Decided by open question 2. The two shapes are written out here so the owner is choosing between things they can see.

**Option (a), change the file.** A second entry in `.github/dependabot.yml`:

```yaml
  - package-ecosystem: pip
    directory: /legacy/backend
    # No target-branch on purpose. GitHub ignores the settings of any entry
    # that names one when it raises a security pull request, and this entry
    # exists only to stop those. The default branch is development anyway.
    schedule:
      interval: monthly
    groups:
      legacy:
        patterns: ["*"]
    ignore:
      - dependency-name: "*"
```

and the matching change in `tools/checks/test_workflow_pins.py`, letting an entry leave `target-branch` out while still refusing one that targets `main`.
An npm entry for `/legacy/frontend` follows the same shape if npm pull requests ever start.

**Option (b), watch first.** Create the rule, close #243 and #244, change no file, and look again after a fortnight.
If no new security pull request has appeared for `legacy/`, the rule was enough on its own and `.github/dependabot.yml` is never touched.
If one has appeared, do option (a) then.

Option (b) is recommended, because option (a) weakens a test rule permanently in order to solve a problem that may already be solved.

### Part 3: documents changed in the implementation pull request

- [security.md](../../platform/security.md), "Dependencies and scanning": what the rule matches, why, and the fact that the path must be exact.
- [runbook.md](../../platform/runbook.md): the read-only check that the rule is still working, and what a broken rule looks like.
- [tools/checks/README.md](../../../tools/checks/README.md): a note next to the Dependabot template saying a new dependency file inside `legacy/` must be added to the rule by hand, because a wildcard does not match.

### Part 4: the two open pull requests

#243 (`pyjwt`) and #244 (`urllib3`) are closed or merged according to open question 3, with a comment naming this ticket either way.

## Edge cases and failure behaviour

- **The rule is written with a wildcard.** It matches nothing and alerts keep arriving, looking exactly like no rule at all. Guarded by naming both exact paths in this document and in `security.md`, and by the runbook check reading the alerts back rather than reading the settings page.
- **A new dependency file appears inside `legacy/`.** It is not covered, because the rule names paths one by one. `legacy/` is frozen, so this is unlikely, but the note in `tools/checks/README.md` exists for it.
- **A dependency file appears outside `legacy/`,** which is what happens when `api/` or `web/` is built. It is correctly not covered, and that is the point. The first alert against `api/` or `web/` must appear in the Open list as normal. The test plan makes this a named check at that moment rather than an assumption.
- **The owner deletes or disables the rule by accident.** Alerts return to the Open list. The runbook check finds it. Nothing breaks.
- **GitHub changes or withdraws auto-triage rules.** Same symptom, same check, and the fallback is the position the repository is in today.
- **`legacy/` is deleted later.** Every alert becomes `fixed` on its own, as the 44 alerts at the old path already show, and the rule becomes dead weight to be removed in that ticket.
- **An alert arrives for a library used by both `legacy/` and future real code.** GitHub raises one alert per manifest, so the `api/` or `web/` alert is a separate alert at a separate path and is untouched by the rule.
- **The rule fires on an alert that should have been seen.** The alert is not gone. `resolution:auto-dismissed` lists everything the rule closed, and the runbook says to read that list when reviewing security, so the decision is reversible and auditable.

## What is deliberately not covered

- Deleting `legacy/` or anything inside it. The owner chose not to, on 2026-10-01.
- Reopening or re-dismissing the 49 alerts already closed by hand. They are closed and they carry their reason.
- Dismissing the 13 currently open alerts by hand. That is the activity being stopped; the rule closes them.
- Turning the repository-wide Dependabot security updates setting off. It would also cover `api/` and `web/` when those arrive, which is the opposite of what is wanted, and it would revise the 2026-09-14 decision.
- Organisation-level rules. Manifest path matching is repository-level only, and there is one repository.
- CodeQL, already handled by its own config file.
- Running `make ci` on a Dependabot pull request, which is #245.

## Open questions for the owner

1. **A rule closes alerts automatically. It cannot stop them appearing. Is that enough?**
   Nothing on GitHub prevents an alert being raised for a path. The rule lets the alert arrive and closes it within minutes, marked `auto-dismissed` and hidden from the Open list, with nobody touching it.
   Options: (a) accept auto-dismissal as what "stopped at the source" means here, which is what this design assumes; (b) bring the deletion of `legacy/` forward instead, which does end it completely, at the cost of the reference material the rebuild still reads; (c) keep dismissing by hand, which the 2026-10-01 decision already rejected.
   **Recommendation: (a).** It removes all the recurring work, and (b) stays available the moment the rebuild stops needing `legacy/`.

2. **Stopping the update pull requests needs an entry whose shape this repository's own test forbids. Relax the test, or wait and see?**
   Options: (a) relax `test_workflow_pins.py` so an entry may leave `target-branch` out, with a dated comment saying why; (b) create the rule first, close #243 and #244, and watch for a fortnight, doing (a) only if security pull requests keep arriving; (c) switch the repository-wide security updates setting off, which would also silence `api/` and `web/` later.
   **Recommendation: (b), then (a) if needed.** It costs a fortnight and replaces a guess with a measurement.

3. **Do #243 and #244 get closed, or merged first?**
   Both touch only `legacy/backend/requirements.txt`. Merging costs about seven minutes of `make ci` each and upgrades code that is never deployed. Closing costs nothing and keeps `legacy/` as a true snapshot of what the first version ran.
   **Recommendation: close both, with a comment naming this ticket.**
