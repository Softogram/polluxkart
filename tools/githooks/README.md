# Git hooks

Enable once per clone:

```
git config core.hooksPath .githooks
```

`make doctor` reports whether that setting is in place. It never changes the setting.

| Hook | When | What it does |
| --- | --- | --- |
| `.githooks/pre-commit` | every `git commit` | Checks the **staged** docs tree with `docslint`. `SKIP_LOCAL_CI` does not skip this. |
| `.githooks/pre-push` | every `git push` | Refuses a push that updates `development` or `main`. If the branch has an open pull request, refuses a dirty folder and then runs `make ci`. |

If `gh` is missing or GitHub cannot be reached, the pre-push hook warns and lets the push go ahead without `make ci`.
`SKIP_LOCAL_CI=1 git push` skips `make ci` only. Say so in the pull request. It never allows a direct push to `development` or `main`.

The wrappers call `tools/githooks/pre_commit.py` and `tools/githooks/pre_push.py`.
