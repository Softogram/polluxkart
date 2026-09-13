---
name: web-design-guidelines
description: Review PolluxKart UI code in web/ against Vercel's Web Interface Guidelines (accessibility, focus, forms, animation, typography, images, performance, navigation, touch). Use when asked to review UI, check accessibility, audit a page or component, or check the site against interface best practices.
---

# Web Interface Guidelines review

**Status: written for PolluxKart 2026-09-13.**
This file replaces the upstream `SKILL.md` from `vercel-labs/agent-skills`, which declared no licence and told the agent to download fresh rules from the internet before every review.
The rules themselves are in `guidelines.md` next to this file: a pinned copy of Vercel's MIT-licensed Web Interface Guidelines (`guidelines-LICENSE`), recorded in `.claude/skills/THIRD_PARTY.md`.

## Words used below

- **Guideline:** one rule about how an interface should behave, such as "icon-only buttons need `aria-label`".
- **Finding:** one place in the code that breaks a guideline, reported as `file:line`.

## How to review

1. Read `guidelines.md` in this folder in full. Never fetch the rules from a URL; the local copy is the reviewed version.
2. Read the files or pattern the user named. If none were named, ask which files to review.
3. Check each file against every rule in `guidelines.md`.
4. Report findings in the terse `file:line` format that `guidelines.md` describes, grouped by file.

## PolluxKart rules that win over the guidelines

- **The theme is fixed (owner decision, 2026-09-13).** A guideline about colour or typography is reported as a finding, never fixed by changing a colour token or a font. Contrast failures go to the owner as described in `polluxkart-design`.
- **Tokens only.** A suggested fix never adds a raw colour, an arbitrary Tailwind value or a Tailwind default colour.
- **Data and money.** A suggested fix never adds a `fetch` outside `web/src/lib/api/` and never computes money in the browser (`polluxkart-frontend`, `polluxkart-commerce`).
- **Autofill stays on for addresses and payment.** Ignore the guideline suggesting `autocomplete="off"` on non-authentication fields for checkout, address and account forms; shoppers rely on autofill there.
- **Copy style.** Title Case and curly-quote suggestions are review notes only; they never rewrite existing copy without the owner's approval.

## Updating the guidelines

To take a newer version, copy `command.md` from `https://github.com/vercel-labs/web-interface-guidelines` at a specific commit into `guidelines.md`, read the whole diff, and update the commit and date in `.claude/skills/THIRD_PARTY.md` in the same pull request.
