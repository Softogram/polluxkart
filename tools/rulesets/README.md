# Branch rulesets

Files in `.github/rulesets/` are the source of truth.
They name people and apps, never numeric ids.

```
make rulesets-check                        # compare GitHub with the files
make rulesets-apply-dry-run                # print planned writes, change nothing
make rulesets-apply RULESETS=development   # first apply: development plus merge settings
make rulesets-apply RULESETS="main main-owner-merge"  # after the first release into main
make rulesets-apply                        # all three, only after main is ready
```

`validate` runs inside `make ci` and does not talk to GitHub.

Apply order matters.
Protect `development` first.
Do not apply `main` or `main-owner-merge` until the first release has merged into `main`, so the approval gate exists there.
Named apply still updates the four repository merge settings.

`check` compares rules, required checks, merge methods, branch targets and bypass actors.
If a field is missing because this login cannot see it, that is reported as "not visible with this login", not as a match and not as drift.
The daily `rulesets-drift` job cannot see hidden bypass lists; run `make rulesets-check` with an admin login for that part.

Changing a rule: pull request, merge, then apply the named rulesets, then `make rulesets-check`.
