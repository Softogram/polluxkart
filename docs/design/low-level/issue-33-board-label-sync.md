# E00-03 Keep the project board in sync with stage labels

Parent: [low-level/](README.md) | Index: [docs/](../../README.md)

**Status: DRAFT (2026-09-14)**
Ticket: #33 (E00-03), part of epic #10.
Test plan: [../test/issue-33-board-label-sync.md](../test/issue-33-board-label-sync.md)
Depends on: #32 (the configured board and `tools/board/board.py`) and #34 (`make ci`, pinned actions checks).

## Words used below

- **Sync:** the automation that moves a ticket's card to the column matching its stage label.
- **GitHub App:** a bot identity registered to the Softogram organisation and installed on this repository. It has only the permissions it is given, and is not tied to any person's account.
- **Installation token:** a short-lived key (it expires within an hour) that the App gets for each run, so no long-lived key is used to change anything.
- **Private key:** the App's secret, used only to ask GitHub for an installation token. It is stored as an encrypted GitHub Actions secret.
- **Label event:** GitHub's record that a label was added or removed, with who did it and when.
- **Valid stage label:** a stage label that follows the owner rule. `stage: implementation-ready` counts as valid only if the owner applied it.
- **Reconcile:** a full pass over every ticket that fixes anything the event-driven runs missed.

## What was already decided before this document

- **Six stages as labels, exactly one per ticket; only the owner applies `stage: implementation-ready`, by hand; a guard removes it when anyone else applies it** (owner decision, 2026-09-13, [decisions.md](../../platform/decisions.md), "Nothing is implemented without the owner's approval").
- **The board: public, named PolluxKart, epics in a separate view, only the owner edits it** (owner decision, 2026-09-14, "Project board").
- **How the sync works** (owner decision, 2026-09-14, "Board sync", answered while planning this ticket):
  - it uses a GitHub App, not a personal token;
  - it goes one way: labels move cards, and a card moved by hand goes back at the next sync;
  - a ticket closed as completed gets `stage: done` automatically; closing as "not planned" changes nothing;
  - after the guard removes an approval label someone else applied, the ticket goes back to its last valid stage label.

## The problem

Nothing moves cards today.
On 2026-09-14 six cards had to be updated by hand after their labels changed, and a board that drifts from the labels stops being trustworthy.
GitHub's built-in workflow token cannot change an organisation's project, so a separate identity is needed.

## The change

### The GitHub App (set up once by the owner)

| Setting | Value |
|---|---|
| Name | `polluxkart-board-sync` |
| Owner | the Softogram organisation |
| Repository permissions | Issues: read and write (to restore or set stage labels); Metadata: read |
| Organisation permissions | Projects: read and write |
| Webhooks | off (the workflow runs it, not GitHub events sent to a server) |
| Installed on | only `Softogram/polluxkart` |
| Stored in GitHub | the App's id as the Actions variable `BOARD_SYNC_APP_ID`; its private key as the Actions secret `BOARD_SYNC_PRIVATE_KEY` |

The steps are written in `docs/platform/runbook.md`.
The App's id and when its key was created are recorded in the private operations reference, never in the repository.

### The workflow (`.github/workflows/board-sync.yml`)

```yaml
name: board-sync

on:
  issues:
    types: [opened, edited, labeled, unlabeled, closed, reopened]
  schedule:
    - cron: "15 21 * * *"   # nightly reconcile, 02:45 in India
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: board-sync-${{ github.event.issue.number || 'reconcile' }}
  cancel-in-progress: false   # queue runs for the same ticket, never drop one

jobs:
  sync:
    runs-on: ubuntu-24.04
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@<commit> # v7.0.1
        with:
          persist-credentials: false
      - uses: actions/create-github-app-token@<commit> # vX.Y.Z
        id: app
        with:
          app-id: ${{ vars.BOARD_SYNC_APP_ID }}
          private-key: ${{ secrets.BOARD_SYNC_PRIVATE_KEY }}
          owner: Softogram
      - run: python3 tools/board/sync.py
        env:
          GH_TOKEN: ${{ steps.app.outputs.token }}
          ISSUE_NUMBER: ${{ github.event.issue.number }}
          APPROVER: CosmicSaaurabh
```

- The job checks out only the default branch and runs no code from any issue or pull request.
- **Issue titles and bodies are never placed inside a `run:` command**, only read by the script through the API, so a crafted issue title cannot run commands.
- Anyone can open an issue in a public repository, so these runs can be started by strangers; they can only cause the script to read that issue and apply the rules below.
- The token is masked by GitHub in logs, and the script never prints it.

### The script (`tools/board/sync.py`)

It uses `tools/board/board.py` from #32 for the stage table and GitHub calls.

**For one ticket** (an `issues` event):

1. Read the issue: title, state and state reason, labels, and every label event with its actor.
2. If the title is not `EXX-NN ...` or `Epic EXX: ...`, stop: it is not tracked.
3. Add it to the board if it is not there.
4. **Closed as completed:** if its stage label is not `stage: done`, remove the other stage labels and add `stage: done`, then continue with `stage: done`.
5. Work out the **valid stage labels** it carries: every stage label, except `stage: implementation-ready` when its most recent "added" event was by anyone other than the owner.
6. Decide:

| Valid stage labels | What the sync does |
|---|---|
| exactly one | Set the card's Status to that stage |
| none, and the ticket carries an approval label someone else applied, or the guard has already removed one | **Restore the last valid stage:** find the most recent stage label that was added before that wrong approval label and is not itself the approval label; add it back; set the card to it |
| none, otherwise | Leave the card; fail the run naming the ticket and "no stage label" |
| two or more | Leave the card; fail the run naming the ticket and the labels |

**The nightly reconcile** (no issue number) runs steps 2 to 6 for every tracked issue, then runs the #32 checker, and fails listing every problem it could not fix.
It also puts back any card moved by hand, which is what makes the sync one way.

**What the sync never does:**

- It never adds `stage: implementation-ready`, not even when restoring. If the last valid stage before a wrong approval was the owner's own approval, it restores nothing and fails the run, naming the ticket, so the owner re-applies the approval by hand. (Anything else would make the App the label's latest actor, and the approval gate would stop accepting it anyway.)
- It never changes a closed-as-not-planned ticket's labels.
- It never changes board settings or views.

**Names in the code:** `valid_stage_labels(labels, events, approver)`, `stage_to_restore(events, approver)`, `decide(issue, approver)` returning an `Action` (set status, add label, remove labels, fail with reason), `apply(action, gh)`, `reconcile(gh)`, `main(env)`.
`decide` is pure, so every rule is tested without GitHub.

### How it fits with the guard

The guard (`approval-label-guard.yml`) and the sync both react to the same label events, in either order:

| Order | Result |
|---|---|
| The sync runs on the wrong label first | Step 5 ignores the approval label (wrong actor); if the ticket still has its old stage label, the card stays there; the guard's later removal triggers another sync run that finds the same single valid label |
| The guard removes the label first | The sync run for the "labeled" event and the one for "unlabeled" both read the current state: no valid stage label, so the last valid stage is restored |

Both orders end with the ticket carrying one valid stage label and its card in that column.
Runs for the same ticket queue behind each other, so two runs never edit it at once.

### Wiring and documents

- `CHECKS` gains nothing new: `board-tests` from #32 runs `tools/board/` tests, which now include the sync's.
- `docs/platform/development-process.md`: "The six stages" says cards follow labels automatically, `stage: done` is set automatically when a ticket closes as completed, and the approval label restores itself to the last valid stage after the guard; the "Who moves it here" column for `stage: done` is updated.
- `docs/platform/runbook.md`: creating the App, storing its id and key, rotating the key, and what a red `board-sync` run means.
- The `polluxkart-workflow` skill: `stage: done` is set automatically on a completed close.

## Edge cases and failure behaviour

| Situation | What happens |
|---|---|
| A new ticket created from the ticket template | Added to the board in Planning |
| An issue retitled into the `EXX-NN` format | The `edited` event adds it to the board |
| A stranger opens an issue titled like a ticket | It is added to the public board; the owner closes it, and the nightly reconcile keeps closed not-planned items where they are |
| A ticket reopened after being closed as completed | It keeps `stage: done` until a person sets its real stage; the run does not guess |
| A card dragged by hand | Put back at the next event for that ticket, or at the nightly reconcile |
| The App's private key is missing or wrong | The token step fails; the run is red; nothing changes |
| The App was uninstalled | Same as above |
| GitHub API errors or rate limits | The run fails; the nightly reconcile repairs anything missed |
| Two label changes in quick succession | Runs queue; each reads the current state, so the last one wins correctly |
| A secret scanning concern | The only secret is the App key, stored as an encrypted secret and rotated by the runbook steps; installation tokens expire within an hour |

## What is deliberately not covered

- **Board to label sync:** the owner chose one way.
- **Pull requests on the board:** only issues are tracked.
- **Changing the guard or the approval gate:** unchanged.
- **Assigning people or setting other fields:** only Status is synced.

## Open questions for the owner

None open.
The ticket's five questions were answered on 2026-09-14 (the token-renewal question no longer applies, because the App's tokens renew themselves) and are recorded in [decisions.md](../../platform/decisions.md), "Board sync".
