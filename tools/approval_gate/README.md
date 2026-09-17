# approval_gate

Enforces the owner's rule of 2026-09-13: **nothing is implemented without the owner's approval.**
The rules in plain words are in `docs/platform/development-process.md`.

## What it checks on every pull request

- The pull request links its ticket on its own line: `Plans #N` (documents only) or `Implements #N` (anything else).
- A planning pull request changes only Markdown files and does not close its ticket.
- An implementation pull request implements exactly one open ticket whose current stage is implementation-ready, in-progress or in-review, and whose latest approval-related stage label was `stage: implementation-ready` applied by the owner.
- An implementation pull request includes tests when it changes backend or frontend code, and closes no other ticket.
- Pull requests by Dependabot are exempt, except a Dependabot pull request into `main`.
- A pull request into `main` passes only when it comes from this repository's `development` branch (a release). Ticket lines on a release are ignored.

## How it runs

`.github/workflows/approval-gate.yml` runs `gate.py` on `pull_request_target`, from the base branch, so a pull request cannot change the check that judges it.
It only reads the GitHub API and never runs code from the pull request.
If the owner approves a ticket after its pull request was opened, re-run the check or edit the pull request description.

## Test it

```
python3 -m unittest discover -s tools/approval_gate -v
```

Standard library Python 3.10 or newer; nothing to install.
