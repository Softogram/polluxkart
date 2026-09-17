# Board tools

Python on the standard library. Tests never call GitHub.
The rules are in `docs/platform/development-process.md`.

- `board.py` - stage names, which issue titles are tracked, and GitHub calls used by the checker and the sync.
- `sync.py` - move each card to the Status that matches its stage label. Never adds `stage: implementation-ready`.
- `check.py` - live `make board-check` lands with ticket #32.

Run the tests:

```
python3 -m unittest discover -s tools/board
```

The live sync is `.github/workflows/board-sync.yml`. It needs the GitHub App described in `docs/platform/runbook.md`.
