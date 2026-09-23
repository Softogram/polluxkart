# Local checks

The Makefile is the front door. Python under `tools/checks/` does the work.

| Command | What it runs |
| --- | --- |
| `make doctor` | Is this machine missing anything the checks need? |
| `make ci` | Every check a pull request must pass. |
| `make ci-docs` | Docs checks only (the `docs` workflow). |
| `make ci-tooling` | Tooling checks only (the `tooling-tests` workflow). |

`make ci` keeps going after a failure and prints a summary. Ctrl+C stops the current check; later checks are listed as not run.

Python 3.10 or newer is required. Older versions print an error and exit 1 before any check runs. If Python is not installed at all, `make` itself prints `python3: command not found`; install Python 3.10 or newer first.

`actionlint` and ShellCheck are required for `make ci` (the `actionlint` check, and the end-to-end tests inside `checks-tests`). On GitHub's Linux machines, `tools/checks/install_linters.py` installs the pinned versions. Locally, install them with Homebrew or your package manager. `make doctor` fails if they are missing or older than the pin.

Pinned versions live in `tools/checks/linters.py`.

## Exit codes

| Code | Meaning |
| --- | --- |
| 0 | Every selected check passed |
| 1 | At least one check failed, or Python is older than 3.10 |
| 2 | Wrong usage, such as an unknown group name |
| 130 | Stopped with Ctrl+C; checks not reached are listed as not run |

## Adding a Dependabot entry when a new folder arrives

`.github/dependabot.yml` lists only GitHub Actions today, because Dependabot reports a configuration error for an ecosystem whose folder holds no dependency files.
The ticket that creates `api/`, `web/` or a Dockerfile adds its entry in the same pull request, copied from here:

```yaml
  - package-ecosystem: maven          # or npm for pnpm, or docker
    directory: /api                   # or /web, or the Dockerfile's folder
    target-branch: development
    schedule:
      interval: weekly
      day: monday
      time: "09:00"
      timezone: Asia/Kolkata
    groups:
      maven:
        patterns: ["*"]
        update-types: [minor, patch]
    ignore:
      - dependency-name: "*"
        update-types: ["version-update:semver-major"]
```

The `ignore` block keeps major versions out of Dependabot's weekly pull request, because a major version may break things and belongs in its own planned ticket (owner decision, 2026-09-14).
Security updates ignore that block, so a published vulnerability still gets a pull request even when the fix is a new major.
GitHub Actions is the exception: its majors are still proposed, so its entry has no `ignore` block.

`test_workflow_pins.py` fails if a Maven, npm or Docker entry leaves out its group or its major-version ignore, so a later ticket cannot forget them.

## Adding a CodeQL language when a new folder arrives

The same tickets add their language to the matrix in `.github/workflows/codeql.yml`: `java-kotlin` with `api/`, `javascript-typescript` with `web/`, both with `build-mode: none`.
A test fails if a folder exists without its language, or a language is listed without its folder.

## How to add a check

Add a row to `CHECKS` in `checks.py` with a group name.
If the group is new, add a `ci-<group>` target in the `Makefile` and one workflow job that runs `make ci-<group>` at release.
`test_coverage.py` fails until all three exist.
