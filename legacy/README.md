# Legacy code: reference only

This folder holds the first version of PolluxKart.
It was generated with Emergent, an AI app builder, in early 2026.

**Nothing in this folder is built, tested, or deployed.**
Do not fix bugs here and do not copy code from here without reading why it was replaced.

## What is inside

- `backend/`: a FastAPI (a Python web framework) server using MongoDB (a document database).
- `frontend/`: a React app built with Create React App (a now-deprecated React starter kit), Tailwind and shadcn/ui.

## Why it was replaced

An audit in September 2026 found problems that could not be fixed by patching.
Examples: anyone could reset anyone's password, stock could be sold twice, and the checkout used hardcoded fake addresses.
The full list, with the rule the rebuild follows for each one, is in [`docs/legacy/audit-2026-09.md`](../docs/legacy/audit-2026-09.md).

## How to use it

Use it as a feature checklist.
It shows what the store already tried to do, such as brands, promotions, and a stock movement log.
Use it as a list of mistakes to avoid.
Each mistake is written up in the audit document.

## When it goes away

This folder is deleted in the launch pull request.
That happens once every item in `docs/legacy/parity-checklist.md` is ticked.
Git history keeps the code after deletion, so nothing is lost.
