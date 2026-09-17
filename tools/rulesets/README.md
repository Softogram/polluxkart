# Branch rulesets

Files in `.github/rulesets/` are the source of truth.
They name people and apps, never numeric ids.

```
make rulesets-check   # compare GitHub with the files
make rulesets-apply   # create or update rulesets (admin login)
```

`make rulesets-apply --dry-run` is not a Make flag; run `python3 tools/rulesets/rulesets.py apply --dry-run`.

`validate` runs inside `make ci` and does not talk to GitHub.

Changing a rule: pull request, merge, then `make rulesets-apply`, then `make rulesets-check`.
