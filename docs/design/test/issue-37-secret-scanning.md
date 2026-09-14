# Test plan: E00-07 Secret scanning in pre-commit, CI and GitHub push protection

Parent: [test/](README.md) | Index: [docs/](../../README.md)

**Status: DRAFT (2026-09-14)**
Ticket: #37 (E00-07).
Design: [../low-level/issue-37-secret-scanning.md](../low-level/issue-37-secret-scanning.md)

This ticket has no web requests.
Its flows are a commit, `make ci` on a laptop and on GitHub, and GitHub's own push protection.
Terms such as gitleaks, finding, allow list, redact and push protection are explained at the top of the design.

## Words used below

- **Generated fake secret:** a value built fresh by the test at run time in a well-known secret shape, for example `ghp_` followed by 36 random letters and digits (the shape of a GitHub token). It grants access to nothing, and it is never written into a committed file.
- **Sandbox repository:** a temporary git repository made by a test, with the real `.gitleaks.toml`, `tools/secrets/`, the hooks, and the hooks enabled.
- **Passing partner:** the matching test that passes, proving a failing test fails for the intended reason.

## How these tests run

- All automated tests are standard library `unittest` files in `tools/secrets/`, run by the `secrets` and `githooks-tests` checks in `make ci` and the `tooling-tests` workflow. They use the real, pinned `gitleaks`.
- **No secret-shaped value is ever committed to this repository**, not even in test code: tests build the value at run time from a prefix and random characters, so the repository's own scans stay clean.
- **Every test that produces scanner output asserts the generated value does not appear anywhere in it**, proving redaction.
- No test reaches GitHub; the one push protection check is done by hand, once.

## Flow 1: `git commit` (the pre-commit scan)

| Id | Kind | Case | Expected | Proves |
|---|---|---|---|---|
| S1.1 | End-to-end | Stage a file with ordinary text and commit | Commit created | Partner for S1.2 |
| S1.2 | End-to-end | Stage a file containing a generated fake secret and commit | Refused; the output names the rule and file; no new commit exists; the generated value is not in the output | AC1, redaction |
| S1.3 | End-to-end | Generated fake secret in a file on disk that is not staged; commit something else | Commit created, because only staged content is scanned | The scan covers what is committed |
| S1.4 | End-to-end | Generated fake secret in `.env`, which is git-ignored, and a normal commit | Commit created | A local `.env` never blocks work |
| S1.5 | End-to-end | `git add -f .env` with a generated fake secret, then commit | Refused. Partner: S1.4 | Force-adding a secret is still caught |
| S1.6 | End-to-end | Staged fake secret and a staged em dash in a doc | Refused; both docslint's and gitleaks' problems are printed, because both checks run | Neither check hides the other |
| S1.7 | End-to-end | `SKIP_LOCAL_CI=1` with a staged fake secret | Still refused | The escape hatch never skips the secret scan |
| S1.8 | End-to-end | The file with the fake secret gains an inline `gitleaks:allow` comment | Refused by the allow-list rule, naming file and line. Partner: S1.2 shows gitleaks alone would pass it | Inline allows are refused |

## Flow 2: `make ci` and the `secrets` check

| Id | Kind | Case | Expected | Proves |
|---|---|---|---|---|
| S2.1 | End-to-end | Sandbox branch with two clean commits after `origin/development` | `scan.py ci` exits 0: "No secrets found" | Partner |
| S2.2 | End-to-end | Branch commit 1 adds a generated fake secret, commit 2 deletes it; the tracked files are now clean | Exit 1; the finding names commit 1; the value is not in the output. Partner: S2.1 | AC2: every commit in the range is scanned |
| S2.3 | End-to-end | A generated fake secret in a commit that is already on `origin/development` (before the range) | Exit 0 | Only the branch's commits are scanned, as decided |
| S2.4 | End-to-end | `SCAN_BASE` set to a commit id, as on GitHub | The range starts there, not at `origin/development` | The CI range is the pull request's range |
| S2.5 | End-to-end | `SCAN_BASE` empty and `HEAD` equal to `origin/development` (a push after merge) | No commits scanned; the tracked-files scan still runs and passes | Merged results are still scanned |
| S2.6 | End-to-end | The working tree has a tracked file with a generated fake secret, uncommitted | Exit 1 from the tracked-files scan | The current files are scanned, not only commits |
| S2.7 | End-to-end | A local `.env` with a generated fake secret, otherwise clean | Exit 0. Partner: S2.6 | Ignored files are not scanned |
| S2.8 | End-to-end | `origin/development` missing in the sandbox and no `SCAN_BASE` | Exit 1: "fetch origin first" | Never scans nothing silently |
| S2.9 | End-to-end | The temporary folder for the tracked-files scan | Gone after both a passing and a failing run | No copies of files are left behind |
| S2.10 | End-to-end | `make ci` in a repository copy with S2.2's branch | The `secrets` check fails and the other checks still run and pass | The check is really wired into `make ci` |

## Flow 3: the allow list (unit tests)

| Id | Case | Expected |
|---|---|---|
| A3.1 | The real `.gitleaks.toml` | Passes |
| A3.2 | An entry with `description = "2026-09-20: example key in a test"` | Passes |
| A3.3 | An entry with no description | Fails, naming the entry. Partner: A3.2 |
| A3.4 | `description = "example key"` (no date) | Fails |
| A3.5 | `description = "2026-02-30: reason"` (not a real date) | Fails |
| A3.6 | `description = "2026-09-20:"` (no reason) | Fails |
| A3.7 | An entry using `commits = [...]` | Fails: commit ids change on squash merge |
| A3.8 | End-to-end: a false alarm allow-listed by path with a dated reason, then the same file scanned | gitleaks passes it. Partner: S1.2 | 
| A3.9 | A tracked Python file containing `# gitleaks:allow` | Fails, naming file and line |
| A3.10 | A Markdown file mentioning the marker inside backticks | Passes. Partner: A3.9 |
| A3.11 | A Markdown file with the marker outside backticks | Fails |

## Flow 4: `make doctor`, pins and settings

| Id | Kind | Case | Expected |
|---|---|---|---|
| D4.1 | Unit | `gitleaks` missing | `missing` with `brew install gitleaks`; exit 1 |
| D4.2 | Unit | `gitleaks` below the pin, then exactly the pin | `too old`, exit 1; then `ok` |
| D4.3 | Unit | `linters.py` pin for gitleaks | Has a version, a GitHub release address and a 64-character checksum; doctor's minimum equals it |
| D4.4 | Unit (#36's `validate`) | `.github/rulesets/repository.json` | Contains secret scanning, push protection, non-provider patterns and validity checks, all on |
| D4.5 | Unit | `.gitignore` via `git check-ignore` | `.env` and `.env.local` are ignored; `.env.example` is not (AC4) |
| D4.6 | Unit | `.github/CODEOWNERS` | Covers `.gitleaks.toml` and `tools/secrets/` |

## Flow 5: GitHub (by hand, once, recorded on #37)

| Id | Action | Expected | Acceptance criterion |
|---|---|---|---|
| G5.1 | After `make rulesets-apply`: `make rulesets-check` with the owner's login | Exit 0, including the four secret scanning settings | AC3 |
| G5.2 | The owner creates a GitHub fine-grained token with **no permissions and a one-day expiry**, commits it on a throwaway branch in a throwaway clone with the hooks off, and pushes | GitHub refuses the push, naming the secret type. Record the message, then revoke the token and delete the branch locally | Push protection blocks a real provider secret |
| G5.3 | The owner's email and the Security tab after G5.2 | No bypass happened, so no bypass alert; if GitHub records a blocked-push event, note it | Alerts go only to the owner |
| G5.4 | The implementation pull request's `tooling-tests` run | Shows `install_linters.py` installing gitleaks, `make doctor`, and the `secrets` check passing, with no values in the log | AC2 on GitHub |

G5.2 uses a real token because push protection may ignore invented values that fail a provider's own format checks, such as the checksum built into GitHub tokens, so an invented value could not prove the block works.
The token can do nothing, expires in a day, and is revoked straight after; if push protection unexpectedly let it through, it would still be harmless, and the owner deletes the branch.

## Acceptance criteria and the tests that prove them

| Acceptance criterion (from #37, plus the owner's 2026-09-14 answers) | Tests |
|---|---|
| AC1: with hooks enabled, staging a generated fake secret makes `git commit` fail | S1.2, S1.5, S1.7 |
| AC2: the same content in a pull request fails the CI scan, and the log does not show the value | S2.2, S2.4, S2.10, G5.4 |
| AC3: GitHub secret scanning and push protection are on | D4.4, G5.1, G5.2 |
| AC4: `.env` files are ignored by git, and `.env.example` is not | D4.5, S1.4, S2.7 |
| AC5: allow-list and bypass rules match the owner's answers | A3.1 to A3.11, S1.8 |
| Only pull request commits are scanned in CI | S2.2, S2.3, S2.4 |
| Scanner output never shows a matched value | Every S and A test with a finding |

## What the contributor gets when a dependency fails

| Dependency | Failure | What happens | Test |
|---|---|---|---|
| gitleaks | Not installed | The hook and the `secrets` check fail with "not installed; run make doctor" | D4.1, and the missing-program path from #34 |
| gitleaks | Too old | `make doctor` reports it | D4.2 |
| git history | Base commit not available | "fetch origin first"; exit 1 | S2.8 |
| GitHub | Settings changed by hand | The owner's `make rulesets-check` reports it | G5.1, and #36's drift tests |

## Reachability check

No database rows are written.
The equivalent risk is a scan that exists but never runs on real work: S1.2 goes through the real hook via `git commit`, S2.10 through the real `make ci`, and G5.4 through the real GitHub workflow.

## Concurrency and replay

Running the scan twice gives the same result.
Each test uses its own sandbox, so tests and a real `make ci` can run at the same time.

## What is deliberately not covered, and why

- **Whole-history scanning:** not part of the decided design; GitHub's secret scanning covers the history privately.
- **A bypass of push protection in the live test:** a bypass would push a real token into a public repository on purpose; G5.2 stops at the block.
- **Detection quality of gitleaks' built-in rules:** that is gitleaks' own test suite; these tests prove the wiring, the range, redaction and the allow-list rules.
- **Secrets in issues, pull request text and comments:** handled by GitHub's secret scanning, outside gitleaks.
