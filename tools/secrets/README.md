# Secret scanning

This folder holds the secret scan that runs before a commit and inside `make ci`.

## Words used here

- **Secret:** a password, API key, token or private key that grants access to something.
- **gitleaks:** an open-source secret scanner. It reads files or git history and flags text shaped like a secret.
- **Finding:** one thing gitleaks flags. It may be a real secret or a false alarm.
- **False alarm:** text that looks like a secret but is not, such as an example value in a test.
- **Allow list:** the entries in `.gitleaks.toml` that tell gitleaks to stop flagging a known false alarm.
- **Redact:** hide the matched value in the output, so a log never repeats the secret it found.
- **Tracked file:** a file git records, as opposed to one git ignores such as a local `.env`.

## Why three layers

This repository is public.
Anything that reaches it is readable by anyone, forever, because forks and caches keep a copy even after a later commit removes it.
So the scan is repeated at three points, and each one catches what the one before it missed.

| Layer | Where | What it scans | What it stops |
|---|---|---|---|
| 1 | The pre-commit hook | The staged changes | The commit, before the secret enters any commit |
| 2 | The `secrets` check in `make ci` | The branch's own commits, then every tracked file as it is now | The push, through the pre-push hook |
| 3 | GitHub secret scanning and push protection | Every push, and the whole history | The push, unless the pusher bypasses with a reason |

Layer 2 does not re-run in GitHub Actions on a pull request into `development` (owner decision, 2026-09-16).
It runs on your machine, and again at release.

## The two commands

```
python3 tools/secrets/scan.py staged   what the pre-commit hook runs
python3 tools/secrets/scan.py ci       what the secrets check in make ci runs
```

Both run gitleaks with `--redact`, and this script prints only the rule name, the file, the line and the commit.
The matched value is never read out of the report, so no log can repeat a secret.

Exit code 0 means nothing was found. Exit code 1 means a finding or an allow-list problem.

## Which commits `scan.py ci` covers

- On your machine: from where the branch left `origin/development` up to `HEAD`.
- On GitHub: the workflow passes the pull request's base commit in `SCAN_BASE`, so the range is exactly the pull request's commits, including ones a later commit undid.
- After a merge, the range is empty and only the tracked files are scanned.
- If the starting point cannot be found on your machine, the scan fails with "fetch origin first" rather than silently scanning nothing.
- On GitHub a run with no starting point, such as a release push, has no commit range of its own. It scans the tracked files and says so in the log.

It scans tracked files only.
`gitleaks dir` would also read files git ignores, which would flag your own local `.env`, so the tracked files are copied into a temporary folder, scanned there, and the folder is deleted whatever happens.

## Allowing a false alarm

Add an entry to `.gitleaks.toml` in a pull request:

```toml
[[allowlists]]
description = "2026-09-20: example key copied from the Razorpay documentation"
paths = ['''^api/payment/src/test/resources/razorpay-docs-example\.json$''']
```

Three rules are checked, and each one fails the scan when broken:

1. The description must start with a real date in `YYYY-MM-DD` form, then a colon, then a reason.
2. An entry must not be narrowed by commit id. Squash merging gives every change a new commit id, so the entry would quietly stop matching.
3. An inline allow comment in source code is refused. Allow it in this file, where a reviewer can see it, or not at all.

## What to do when something is found

The table is in [the runbook](../../docs/platform/runbook.md), under "Handling secrets".
The short version: if it ever reached a commit, rotate it the same day.
If the pre-commit hook stopped it before any commit existed, removing it is enough.

## Keeping gitleaks current

The version is pinned in `tools/checks/linters.py` with its download address and checksum, installed on GitHub by `tools/checks/install_linters.py`, and checked on your machine by `make doctor` (`brew install gitleaks`).
Raising the pin is its own pull request, because a newer gitleaks may add rules that flag files already in the tree.

## See also (do not follow recursively)

- [../../docs/platform/security.md](../../docs/platform/security.md) - the rules for secrets and personal data
- [../../docs/platform/runbook.md](../../docs/platform/runbook.md) - what to do when a scan finds something
- [../githooks/README.md](../githooks/README.md) - the hooks that run this scan
