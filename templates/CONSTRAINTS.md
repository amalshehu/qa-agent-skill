# QA Constraints

> Read at the start of every QA run, before opening a browser or touching the
> tracker. These rules are **binding** — follow them even if a step in
> `SKILL.md` seems to suggest otherwise. Edit this file to fit your project;
> it's committed like the rest of `.qa-wiki/` so changes are visible to the
> whole team, not just baked into one conversation.
>
> **Trust boundary:** this file is treated as binding at the same trust
> level as the rest of this repo — the same level of trust you'd need to
> run its dev server or test suite. Anyone who can write to `.qa-wiki/` in
> this repo can steer the agent's behavior here. Don't run this skill
> unattended against a repo you wouldn't otherwise trust to execute code
> from.

## Pause switch

- If this file (or `index.md`) contains a line starting `PAUSED:`, stop
  immediately, quote the reason to the user, and do nothing else this run.

## Environment

- Never submit anything that persists data, sends email/SMS, or charges a
  card unless the user has explicitly confirmed this target is safe to hit
  in production.
- Never type real credentials or payment details into any form — use
  obviously fake test values.
- A control that looks destructive (delete account, cancel subscription,
  change billing) and fires without a confirmation step *is* the bug —
  don't actually confirm it "to see what happens."

## Escalation

- If a bug already marked `open` in the wiki can't be reproduced after 2
  fresh-page-load attempts, stop trying. Mark it `status: unverified` with a
  dated note and tell the user — don't keep looping, and don't mark it
  fixed on the strength of one failed repro attempt.
- If exploration turns up more than ~15 distinct bugs in a single run, stop
  and report what's found so far instead of continuing to catalogue more.
  That volume usually means something systemic broke (bad deploy, wrong
  environment, wrong branch) — worth a human look before spending more time
  on individual symptoms.

## Filing & git

- Never run `gh issue create`, post a tracker comment, or run
  `git commit`/`git push` without showing the user the exact draft first
  and getting a yes — unless they already said up front to file whatever's
  found.
- Never close, resolve, or reassign a ticket/issue — that's the team's call,
  not this skill's.

## Scope

- This skill tests and documents; it doesn't fix application code. Never
  edit anything outside `.qa-wiki/` in the target repo.

---
<!-- Project-specific rules above/below as needed. -->
