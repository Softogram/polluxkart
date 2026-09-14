# Test plan: E00-03 Keep the project board in sync with stage labels

Parent: [test/](README.md) | Index: [docs/](../../README.md)

**Status: DRAFT (2026-09-14)**
Ticket: #33 (E00-03).
Design: [../low-level/issue-33-board-label-sync.md](../low-level/issue-33-board-label-sync.md)

This ticket has no web requests.
Its flows are an issue event running the sync, the nightly reconcile, and the race with the approval label guard.
Terms such as GitHub App, installation token, valid stage label and reconcile are explained at the top of the design.

## Words used below

- **Label history:** the list of label events a test builds for a fake ticket, each with a label, "added" or "removed", and who did it.
- **Fake `gh`:** a small Python object standing in for GitHub in unit tests, holding fake issues and a fake board, and recording every change.
- **Throwaway ticket:** a real issue created only for the live test, titled `E99-01 Board sync test`, closed as not planned afterwards and removed from the board.
- **Passing partner:** the matching test that passes, proving a failing test fails for the intended reason.

## How these tests run

- Unit tests are standard library `unittest` files in `tools/board/`, run by `board-tests` in `make ci` and the `tooling-tests` workflow. They never call GitHub.
- `decide` is tested directly with label histories; `apply` and `reconcile` with the fake `gh`.
- The live walk-through runs once on GitHub after the App is installed, with results linked on #33.

## Flow 1: `decide` for one ticket (unit tests)

The owner is `CosmicSaaurabh`; another person is `helper`.

| Id | Ticket state and label history | Expected action | Proves |
|---|---|---|---|
| S1.1 | Open; `stage: planning` added by `helper` | Set Status to Planning | One label moves the card (AC1) |
| S1.2 | Open; planning, then awaiting-approval added and planning removed | Set Status to Awaiting approval | Label changes move the card |
| S1.3 | Open; awaiting-approval, then approval added by the owner and awaiting removed | Set Status to Implementation ready | The owner's approval is valid |
| S1.4 | Open; awaiting-approval kept, approval added by `helper` | Set Status to Awaiting approval; no label change | A non-owner approval is never treated as valid. Partner: S1.3 (AC2) |
| S1.5 | Open; awaiting-approval removed and approval added by `helper`, then approval removed by the guard | Add `stage: awaiting-approval`; set Status to Awaiting approval | Restore the last valid stage (AC2) |
| S1.6 | Same as S1.5, but the history before was planning, then in-progress (after an owner approval), then the wrong approval | Restore `stage: in-progress` | "Last valid" is the most recent one, not the first |
| S1.7 | Open; owner approval, then approval removed by `helper` and re-added by `helper`, then removed by the guard; nothing else | No label added; fail naming the ticket and "re-apply the approval by hand" | The sync never adds the approval label |
| S1.8 | Open; no stage labels and no guard history | Fail: "no stage label" | Missing labels are reported, not guessed |
| S1.9 | Open; `stage: planning` and `stage: in-review` | Fail naming both labels; no Status change | Two labels (AC6) |
| S1.10 | Closed as completed with `stage: in-review` | Remove in-review, add `stage: done`, set Status to Done | Completed close sets done |
| S1.11 | Closed as completed with `stage: implementation-ready` from the owner | Remove it, add `stage: done`, set Status to Done | Done replaces any stage |
| S1.12 | Closed as not planned with `stage: planning` | Set Status to Planning; no label change | Not planned changes nothing. Partner: S1.10 |
| S1.13 | Closed as completed, already `stage: done` | Set Status to Done; no label change | No needless edits |
| S1.14 | Title `Bug: checkout broken` with `stage: planning` | Nothing | Untracked issues are ignored |
| S1.15 | Title `E03-02 Maven skeleton`, not on the board | Add to the board, then set Status | New tickets appear (AC3) |
| S1.16 | Reopened after closed as completed, still `stage: done` | Set Status to Done; no label change | The sync does not guess a reopened ticket's stage |

## Flow 2: the guard race (unit tests)

Each case feeds the same final label history to `decide` at two points: as seen by the run for the "labeled" event, and as seen by the run for the guard's "unlabeled" event.

| Id | Case | Expected |
|---|---|---|
| R2.1 | `helper` adds the approval label while awaiting-approval is kept; the sync runs before the guard, then after | Both runs end with Status Awaiting approval and no label change (AC2) |
| R2.2 | `helper` replaces awaiting-approval with the approval label; the guard runs before the sync | Both sync runs restore `stage: awaiting-approval`; the second finds it already present and changes nothing |
| R2.3 | Same as R2.2, sync first, then guard | The first run sees only the wrong approval label, restores `stage: awaiting-approval` and sets Status to Awaiting approval; after the guard removes the approval label, the second run finds exactly one valid label and changes nothing |
| R2.4 | In every order above | At no point does any run set Status to Implementation ready |

## Flow 3: `apply` and `reconcile` (unit tests with a fake `gh`)

| Id | Case | Expected |
|---|---|---|
| A3.1 | An action with a label to add and a Status to set | Exactly one add-label call and one Status update |
| A3.2 | Reconcile over five tracked tickets: one card dragged by hand, one missing from the board, one with two labels | The dragged card is put back; the missing one is added; the two-label ticket is reported; the run exits 1 listing it |
| A3.3 | Reconcile over tickets that are all correct | No write calls; exit 0 |
| A3.4 | Reconcile passes and the #32 checker finds a view problem | Exit 1 naming the view problem |
| A3.5 | The fake `gh` fails on the Status update | Exit 1 naming the ticket; no later label change for that ticket |
| A3.6 | Every recorded call | None adds `stage: implementation-ready`, across all tests in the file (a check run after the whole test class) |
| A3.7 | `main` with `GH_TOKEN` in the environment | The token's value never appears in the output |

## Flow 4: the workflow file (unit tests on its text)

| Id | Check | Expected |
|---|---|---|
| W4.1 | Triggers | `issues` with opened, edited, labeled, unlabeled, closed, reopened; a nightly schedule; manual dispatch |
| W4.2 | Permissions | Top-level `contents: read` only; nothing writable from the workflow token |
| W4.3 | No `${{ github.event.issue.title }}` or `body` anywhere in the file | Passes; a copy with the title inside a `run:` line fails. Partner (AC5) |
| W4.4 | Concurrency | Grouped per issue with `cancel-in-progress: false` |
| W4.5 | Pins | Covered by the `workflow-pins` check from #38, or by actionlint and review until #38 lands (AC5) |

## Flow 5: live walk-through on GitHub (once, after the App is installed)

| Id | Action on the throwaway ticket | Expected within a minute | Acceptance criterion |
|---|---|---|---|
| L5.1 | Create `E99-01 Board sync test` from the ticket template | On the board, in Planning | AC3 |
| L5.2 | Move the label to awaiting-approval | Card in Awaiting approval | AC1 |
| L5.3 | Owner applies the approval label by hand, removing awaiting-approval | Card in Implementation ready | AC1 |
| L5.4 | Move through in-progress and in-review | Card follows each | AC1 |
| L5.5 | Drag the card to Planning by hand, then run the workflow by hand | Card back in In review | One way |
| L5.6 | Add `stage: planning` as well, so it has two stage labels | Run fails naming the ticket and both labels; card unchanged; remove the extra label afterwards | AC6 |
| L5.7 | Close as completed | Label becomes `stage: done`; card in Done | Completed close |
| L5.8 | A second throwaway ticket at awaiting-approval: a collaborator account other than the owner applies the approval label, if one exists | The guard removes it; the card never shows Implementation ready; the ticket ends at awaiting-approval | AC2 |
| L5.9 | The run logs | No token or key value appears | AC4 |
| L5.10 | Afterwards | Throwaway tickets closed as not planned and removed from the board; `make board-check` exits 0 | Clean up |

If no second account with write access exists, L5.8 is recorded as not run, and S1.4, S1.5 and R2.1 to R2.4 carry that criterion until a contributor joins.

## Acceptance criteria and the tests that prove them

| Acceptance criterion (from #33, plus the owner's 2026-09-14 answers) | Tests |
|---|---|
| AC1: changing a ticket's stage label moves its card | S1.1 to S1.3, L5.2 to L5.4 |
| AC2: a non-owner's approval label never leaves the card in the approved column | S1.4, S1.5, R2.1 to R2.4, L5.8 |
| AC3: a new ticket appears in Planning | S1.15, L5.1 |
| AC4: the key exists only as an encrypted secret, with the App's approved permissions | Runbook steps; L5.9; the App settings checked by hand against the design's table |
| AC5: actions pinned, minimal permissions | W4.2, W4.3, W4.5 |
| AC6: two stage labels make the run fail, naming the ticket | S1.9, A3.2, L5.6 |
| One way only | A3.2, L5.5 |
| Completed close sets `stage: done`; not planned changes nothing | S1.10 to S1.13, L5.7 |
| Restore the last valid stage after the guard | S1.5 to S1.7, R2.2, R2.3 |

## What the owner gets when a dependency fails

| Dependency | Failure | What happens | Test |
|---|---|---|---|
| GitHub App | Key missing, wrong or App uninstalled | The token step fails; red run; nothing changes | Stated in the design; seen live if it happens |
| GitHub API | Error or rate limit | Red run naming the ticket; the nightly reconcile repairs it | A3.5, A3.2 |
| Guard workflow | Runs before or after the sync | Same end state | R2.1 to R2.4 |

## Reachability check

No database rows are written.
The equivalent risk is automation that exists but never fires on real events: L5.1 to L5.7 drive it through real label changes on GitHub, not by calling the script directly.

## What is deliberately not covered, and why

- **Board to label direction:** not part of the decided design.
- **A second account's approval attempt, when no such account exists:** see L5.8.
- **GitHub's own event delivery delays:** the nightly reconcile is the safety net, tested in A3.2.
