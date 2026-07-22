# QA Wiki — schema for this directory

This directory (`.qa-wiki/`) is a persistent, compounding knowledge base for
QA on this project — not a scratch log. It is committed to git so every
developer and every future QA run shares the same brain. Treat it the way you'd
treat a shared team wiki: read before you write, update in place rather than
duplicating, and keep cross-references honest.

Anyone can browse it directly in Obsidian (open this directory as an Obsidian
vault) or hand it to the QA agent skill, which reads and maintains it
automatically. Both are first-class consumers — don't write anything here that
only makes sense inside one conversation.

## Layers

- **Raw evidence** (`screenshots/<bug-slug>/`) — immutable. Screenshots and
  GIFs captured during a run. Never edited after capture, only added to.
- **The wiki** (`index.md`, `flows/`, `bugs/`, `log.md`) — everything else.
  Owned entirely by whoever/whatever is running QA. Created, updated,
  cross-linked, and kept consistent on every run.
- **This schema** (`CLAUDE.md`) — the conventions below. Co-evolve it as the
  project's QA needs change; don't silently diverge from it instead.

## Folder layout

```
.qa-wiki/
  CLAUDE.md              # this file
  index.md               # catalog: open bugs, fixed bugs, flows tested, last-tested date
  log.md                 # append-only run history
  bugs/<bug-slug>.md      # one page per distinct bug
  flows/<flow-slug>.md    # one page per user flow that's been exercised
  screenshots/<bug-slug>/NN-step.png   # persisted repro evidence
```

`<bug-slug>` and `<flow-slug>` are kebab-case, stable identifiers derived from
the bug title / flow name — once assigned, never renamed, so links and
history stay valid (e.g. `checkout-back-button-resubmit`, `signup-flow`).

## Page conventions

### `bugs/<bug-slug>.md`

Every bug page carries YAML frontmatter so status can be queried (e.g. with
Obsidian Dataview) without opening every file:

```markdown
---
status: open   # open | fixed | regressed
severity: high # low | medium | high | critical
first_found: 2026-07-22
last_seen: 2026-07-22
ticket: PROJ-123   # or GitHub issue URL, once filed
flow: [[signup-flow]]
---

# Back button after failed checkout re-submits the order

## Repro
1. ...
2. ...

## Expected vs. actual
- Expected: ...
- Actual: ...

## Environment
URL, viewport, browser, timestamp.

## Evidence
![step 1](screenshots/checkout-back-button-resubmit/01-initial.png)
```

Update this page in place across runs — don't create a second page for the
same bug. When a bug that was `fixed` reappears, flip `status: regressed` and
add a dated note; that's more urgent than a fresh find and should be called
out as such wherever it's reported.

### `flows/<flow-slug>.md`

One page per distinct user flow (signup, checkout, password reset, ...).
Tracks what's been exercised and links out to bugs found along the way —
this is what turns a pile of bug reports into an actual map of the app's
tested surface:

```markdown
---
last_tested: 2026-07-22
coverage: [desktop, mobile, tablet]
---

# Signup flow

Brief description of the flow and its entry points.

## Known-good paths
- ...

## Bugs found here
- [[signup-email-validation-bypass]] (open)
- [[signup-duplicate-account-toast]] (fixed 2026-06-01)
```

### `index.md`

Content-oriented catalog, read *first* on every run before anything else:

```markdown
# QA Wiki index

Last tested: 2026-07-22

## Open bugs
- [[checkout-back-button-resubmit]] — high — checkout
- ...

## Fixed bugs (recent)
- [[signup-duplicate-account-toast]] — fixed 2026-06-01

## Flows tested
- [[signup-flow]] — last tested 2026-07-22
- [[checkout-flow]] — last tested 2026-06-30
```

### `log.md`

Append-only, chronological, one line per run, consistent prefix so it stays
`grep`-able (`grep '^## \[' log.md | tail -5`):

```markdown
## [2026-07-22] run | tracker=jira | 3 found (2 new, 1 regression)
```

## Workflow expectations (for the QA agent, or any agent operating here)

1. **Read `index.md` and the tail of `log.md` first.** Never explore blind —
   known-open bugs get re-verified, not re-discovered and re-filed as dupes.
2. **Update pages in place.** A bug or flow page is a living document, not a
   new file per run.
3. **Commit changes** to this directory as part of the run (small, clear
   commit message, e.g. `qa-wiki: signup flow re-tested, 1 regression`) so
   the rest of the team sees the wiki update in normal git history — don't
   let it live only in an agent's local disk.
4. **Never delete evidence** for an open bug. Screenshots only get pruned
   once the corresponding bug page is marked `fixed` and enough time has
   passed that the evidence is no longer useful for regression comparison.
5. **Flag contradictions.** If a new run's findings conflict with an existing
   page (e.g. a flow marked stable actually breaks), fix the page and say so
   explicitly rather than silently overwriting.
