# E00-07 Secret scanning in pre-commit, CI and GitHub push protection

Parent: [low-level/](README.md) | Index: [docs/](../../README.md)

**Status: DRAFT (2026-09-14)**
Ticket: #37 (E00-07), part of epic #10.
Test plan: [../test/issue-37-secret-scanning.md](../test/issue-37-secret-scanning.md)
Depends on: #34 (`make ci`, `make doctor`, pinned linters), #35 (the pre-commit hook), and #36 (the repository settings file and its drift check).

## Words used below

- **Secret:** a password, API key, token or private key that grants access to something.
- **gitleaks:** an open-source secret scanner. It looks through files or git history for text shaped like a secret.
- **Finding:** one thing gitleaks flags. It may be a real secret or a false alarm.
- **False alarm (false positive):** text that looks like a secret but is not one, such as an example value in a test.
- **Allow list:** the one file listing false alarms gitleaks should not flag again.
- **Redact:** hide the matched value in the scanner's output, so a log never repeats the secret it found.
- **GitHub secret scanning:** GitHub's own scanner. It checks the repository's whole history and alerts the owner privately.
- **Push protection:** a GitHub feature that refuses a push containing a recognised secret before it reaches the repository.
- **Bypass (push protection):** the pusher overriding a push protection block by choosing a reason.
- **Rotate:** replace a key with a new one and switch the old one off, so a leaked copy stops working.
- **Tracked file:** a file git records, as opposed to an ignored one such as a local `.env`.

## What was already decided before this document

- **Razorpay keys live only locally and, on servers, in a secrets store; never in git, documents or chat** (owner decision, 2026-09-13, [decisions.md](../../platform/decisions.md), "Payments: Razorpay").
- **The pre-commit and pre-push hooks, `make ci`, `make doctor`, and the pinned, checksum-verified linters on GitHub** (owner decisions, 2026-09-14, "`make ci` and `make doctor`" and "Git hooks").
- **The repository settings are saved in `.github/rulesets/repository.json`, applied by script, and checked for drift** (owner decision, 2026-09-14, "Branch rules for `development` and `main`").
- **How secrets are scanned** (owner decision, 2026-09-14, "Secret scanning", answered while planning this ticket):
  - the CI scan checks every commit in a pull request, not the whole history; GitHub's own secret scanning watches the whole history privately;
  - a false alarm is allowed by an entry in one allow-list file, added by anyone through a pull request, each with a dated reason that a check enforces; inline allow comments are refused;
  - the person pushing may bypass a push protection block by giving a reason, and GitHub alerts the owner;
  - only the owner receives secret scanning alerts;
  - a secret must be rotated the same day once it is in any commit (pushed or not), a pushed branch, a document, a chat or a log; a key the pre-commit hook blocked before any commit existed does not need rotating, only removing.

## The problem

The repository is public, so anything that reaches it is readable by anyone, forever: forks and caches keep it even after a later commit removes it.
Today GitHub's push protection is the only barrier, and it recognises only secret formats from known providers.
There is no check on the contributor's machine and none in `make ci`.

## The change: three layers

| Layer | Where | Scans | Stops |
|---|---|---|---|
| 1. Pre-commit | `.githooks/pre-commit` (#35) | The staged changes | The commit, before the secret enters any commit |
| 2. `make ci` and GitHub CI | The `secrets` check in the `tooling` group | The commits on the branch, plus every tracked file as it is now | The push (through the pre-push hook) and the merge (through the `tooling-tests` required check) |
| 3. GitHub | Repository settings | Every push, and the whole history | The push, unless the pusher bypasses with a reason; alerts the owner either way |

Every gitleaks run uses `--redact`, so no terminal output, log or CI summary ever prints a matched value.

### Files

```
.gitleaks.toml                       new: gitleaks settings and the allow list
tools/secrets/scan.py                new: runs gitleaks for the hook and for make ci, and checks the allow list
tools/secrets/test_scan.py           new
tools/secrets/README.md              new: what each layer does and what to do on a finding
tools/githooks/pre_commit.py         changed: runs the staged scan after docslint
tools/checks/checks.py               changed: adds the secrets check to the tooling group
tools/checks/linters.py              changed: pins gitleaks with its checksum
tools/checks/doctor.py               changed: gitleaks becomes a needed-now tool
.github/workflows/tooling-tests.yml  changed: full history checkout, and the pull request's base commit passed to the scan
.github/rulesets/repository.json     changed: the secret scanning settings
.github/CODEOWNERS                   changed: .gitleaks.toml and tools/secrets/ request the owner's review
```

### `.gitleaks.toml` and the allow list

```toml
# gitleaks settings for PolluxKart. See tools/secrets/README.md.
# Every [[allowlists]] entry needs a description starting with the date it
# was added and the reason, for example "2026-09-20: example key in a test".

[extend]
useDefault = true

# [[allowlists]]
# description = "YYYY-MM-DD: why this is not a secret"
# paths = ['''^api/payment/src/test/resources/razorpay-docs-example\.json$''']
```

- gitleaks' built-in rules stay on (`useDefault`).
- The file starts with no allow-list entries.
- An entry narrows by path, by pattern, or by rule, never by commit id, because squash merging gives every change a new commit id and the entry would stop matching.

### `tools/secrets/scan.py`

Standard library Python; it runs the pinned `gitleaks`.

| Command | Used by | What it does |
|---|---|---|
| `scan.py staged` | the pre-commit hook | `gitleaks git --pre-commit --staged --redact --config .gitleaks.toml`, then the allow-list rules below |
| `scan.py ci` | the `secrets` check in `make ci` | the allow-list rules, then the branch's commits, then the tracked files |

**The allow-list rules**, checked before scanning:

1. Every `[[allowlists]]` entry in `.gitleaks.toml` has a `description` starting with a real date in `YYYY-MM-DD` form, then a colon and a reason.
2. No tracked file contains an inline `gitleaks:allow` marker, which gitleaks would otherwise obey silently.
   Markdown files may mention the marker inside backticks, so documents like this one can explain the rule.

**Which commits `scan.py ci` scans:**

- On GitHub, for a pull request: the workflow passes the pull request's base commit as `SCAN_BASE`, and the scan covers `SCAN_BASE..HEAD`, which is every commit in the pull request, including ones a later commit undid.
- On a laptop: from the point where the branch left `origin/development` up to `HEAD`.
- On GitHub after a merge into `development` or `main`: the range is empty, and the tracked-files scan covers the merged result.
- If the starting point cannot be found (for example `origin/development` was never fetched), the scan fails with "fetch origin first", never scanning nothing silently.

**Tracked files only.**
`gitleaks dir` also reads files git ignores, which would flag a contributor's own local `.env`.
So `scan.py ci` copies the files `git ls-files` lists into a temporary folder, scans that folder, and deletes it.

**Output.**
For each finding: the rule name, file and line, and for commits the commit id, with the value redacted.
Then one line: "No secrets found" or "2 possible secrets found".
It exits 0 when clean, 1 on any finding or allow-list problem.

**Names in the code:** `check_allowlist(config_text)`, `find_inline_allows(files)`, `scan_range(base, head, run)`, `scan_tracked_files(root, run)`, `format_findings(report)`, and `main(argv, env)`.

### Wiring into the other tickets' tooling

- **Pre-commit (#35):** `pre_commit.py` runs docslint on the staged copy, then `scan.py staged`. Both always run, and the hook fails if either fails. `SKIP_LOCAL_CI` does not affect it.
- **`make ci` (#34):** `CHECKS` gains `secrets` in the `tooling` group, needing `gitleaks` and `git`.
- **`make doctor` (#34):** `gitleaks` becomes a needed-now tool, minimum the pinned version, install hint `brew install gitleaks`.
- **GitHub (#34):** `linters.py` pins gitleaks' Linux release and checksum; `install_linters.py` installs it.
- **`tooling-tests.yml`:** the checkout step gains `fetch-depth: 0` (all history, so the commit range exists; the repository is small), and the `make ci-tooling` step gains `SCAN_BASE: ${{ github.event.pull_request.base.sha }}`, which is empty on pushes.

### GitHub settings (layer 3)

Added to `.github/rulesets/repository.json`, applied by `make rulesets-apply` and checked by `make rulesets-check` (#36):

| Setting | Value |
|---|---|
| Secret scanning | on |
| Push protection | on |
| Scanning for non-provider patterns (such as private keys) | on |
| Validity checks (GitHub asks the provider whether a found key still works) | on |

GitHub shows these settings only to an admin login, so only the owner's `make rulesets-check` compares them; the daily drift run reports them as "not visible with this login", as #36 designed.

**Bypass and alerts need no settings.**
Without GitHub's paid Secret Protection add-on, the person pushing can bypass a block by choosing "used in tests", "false positive" or "I'll fix it later".
GitHub then records an alert and emails the organisation owner and repository admins, which today is only the owner.

### What happens on a finding

Written into `tools/secrets/README.md` and `docs/platform/runbook.md`, "Handling secrets":

| Where it was caught | Real secret | False alarm |
|---|---|---|
| Pre-commit hook | Remove it from the file and unstage it. No commit exists, so no rotation (owner decision, 2026-09-14) | Add an allow-list entry with a dated reason, in the same pull request |
| `make ci` or the pull request's CI | It is in a commit: **rotate it the same day**, record the rotation in the private operations reference, remove it in a new commit | Allow-list entry with a dated reason |
| GitHub push protection | Do not bypass; remove it. If it was bypassed, it reached GitHub: rotate the same day | Bypass with "false positive", then add an allow-list entry so gitleaks agrees |
| GitHub secret scanning alert (owner's email) | Rotate the same day; close the alert as revoked | Close the alert as a false positive, with the reason |

Removing a secret in a later commit does not undo the leak: the earlier commit stays readable on GitHub.
Rewriting history to hide it is forbidden here and would not help, because forks and caches keep it.

### Documents updated in the implementation pull request

- `docs/platform/security.md`, "Secrets": the three layers, the allow-list rule, bypass and alerts, and the rotation rule as clarified on 2026-09-14.
- `docs/platform/runbook.md`, "Handling secrets": the table above.
- The `polluxkart-security-checklist` skill, "Secrets": the command becomes `gitleaks git --pre-commit --staged` (the older `gitleaks protect` form is deprecated), and the rotation clarification.
- `tools/secrets/README.md`: new.

## Edge cases and failure behaviour

| Situation | What happens |
|---|---|
| A secret is committed, then deleted in the next commit on the same branch | The CI range includes both commits, so the first one is still flagged |
| A real key in a local `.env` | Ignored by git, so never staged, never a tracked file, never scanned: no failure |
| Someone force-adds `.env` with `git add -f` | It is staged, so the pre-commit scan flags any secret in it |
| An inline `gitleaks:allow` comment in code | The allow-list rule fails the check, naming file and line |
| An allow-list entry without a dated reason | The check fails, naming the entry |
| An allow-list entry narrowed by commit id | Refused by the allow-list rules, because squash merges change commit ids |
| gitleaks not installed | The `secrets` check fails as "not installed; run make doctor"; the pre-commit hook fails with the same message |
| gitleaks older than the pin | `make doctor` reports `too old` |
| A new gitleaks release adds a rule that flags existing files | Only when the pin is raised, in its own pull request, which fixes or allow-lists the new findings |
| `origin/development` not fetched on a laptop | `scan.py ci` fails with "fetch origin first" |
| Anything already in the history from before this ticket | Outside every pull request's range, so it never fails CI; GitHub's secret scanning covers the whole history privately, and retiring the first version's credentials is ticket #44 (E01-05) |
| A secret pasted into an issue, pull request description or comment | gitleaks never sees it; GitHub's secret scanning checks those texts for provider secrets in public repositories, and the rotation rule applies |
| A scanner log on GitHub (public for a public repository) | Values are redacted; a test proves a generated value never appears in the output |

## What is deliberately not covered

- **Scanning the whole history in CI:** the owner chose pull request commits only (2026-09-14).
- **Only the owner approving push protection bypasses:** it needs GitHub's paid Secret Protection add-on (2026-09-14).
- **Retiring the first version's credentials:** ticket #44 (E01-05).
- **Dependency vulnerability scanning:** #38 and the backend and frontend CI tickets.
- **Secrets in AWS, SSM Parameter Store and server environments:** the infrastructure tickets in E06.

## Open questions for the owner

None open.
All five questions this ticket raised were answered on 2026-09-14 and are recorded in [decisions.md](../../platform/decisions.md), "Secret scanning".
