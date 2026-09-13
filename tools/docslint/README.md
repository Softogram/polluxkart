# docslint

Checks that the documentation tree follows the rules in `docs/README.md`, so a person or an agent can always find an answer by following links.

## What it checks

1. Every relative link in `docs/`, the root `README.md`, `legacy/README.md`, `ops/` and `tools/` points at a file that exists.
2. Links under a "Read next" heading point only downward: into the same folder or below.
3. "Read next" links never form a loop.
4. Every document under `docs/` can be reached from `docs/README.md` by following "Read next" links.
5. No em dash character appears in those files.

Links and dashes inside code blocks are ignored for link checks, because they are examples.

## Run it

```
python3 tools/docslint/docslint.py
python3 -m unittest discover -s tools/docslint
```

It needs only Python 3.10 or newer, with no packages to install.
It runs on every pull request through `.github/workflows/docs.yml`, and will become part of `make ci`.

## When it fails

Each problem names the file and what is wrong.
A "not reachable" error usually means a new document was not added to its folder's README under "Read next".
A "must point downward" error means a sideways or upward link belongs under "See also (do not follow recursively)" instead.
