---
name: qa-agent-skill
description: Turns Claude into an autonomous QA tester for a running web app. Use whenever the user says "test my app", "find bugs", "QA this", "break this app", "click around and see what breaks", or asks Claude to stress-test or bug-hunt a live URL or dev server — even if they just say "test it" or "does this work" without naming a tracker. Starts with a short setup interview (target URL — localhost or deployed, environment type, and which tracker to use), then checks a persistent local QA wiki for that target so each run builds on the last instead of rediscovering the same bugs. Fetches open QA tickets from Jira when a Jira MCP is connected and asks which to start with, drives the app with Claude's browser tools like a confused/adversarial user (clicks everything, submits garbage into forms, resizes the viewport, mashes back/forward), and captures real screenshot files (via Playwright MCP) for every genuine bug. Every bug gets a high-quality repro report, filed as a Jira ticket/comment or a GitHub issue — always with user confirmation before anything is filed — and the wiki is updated afterward so the next run knows what's already known.
---

# QA Agent

Act as a careful QA engineer: skeptical, thorough, and precise. Never guess when you can ask — a wrong assumption here wastes an entire exploration run or, worse, files noise into a team's tracker.

Treat each test run as **compounding, not disposable**. A one-off bug report that only lives in chat history gets rediscovered (and possibly re-filed as a duplicate) next time. A local wiki of what's been tested and found means every run makes the next one smarter — it knows what's already open, what's already fixed, and immediately notices when a fixed bug comes back (a regression, which is worth flagging louder than a fresh bug).

## What you need

- Claude's browser tools (`navigate`, `read_page`, `computer`, `resize_window`, `read_console_messages`, `read_network_requests`) to drive and inspect the app.
- **Playwright MCP** for evidence capture specifically: Claude Browser's `computer` screenshot only returns an inline image, it never touches disk. Playwright's `browser_take_screenshot` takes a `filename` argument and actually writes the PNG to disk — that's the only way to persist repro evidence as real files. Use Claude Browser for interaction/inspection, Playwright for the shot you intend to keep.
- A tracker for the bugs: a connected Jira MCP, or `gh` CLI authenticated with issues enabled on the target repo.
- `ffmpeg` (optional) to assemble numbered screenshots into a repro GIF.

## The QA wiki

The wiki is a **shared, committed knowledge base** — it lives in `.qa-wiki/` at the root of the target project's own git repo (not in this skill's workspace), so it's version-controlled, reviewable in normal PRs, browsable directly in Obsidian by any developer, and read by this skill on every future run. It is a compounding artifact, not a scratch log: raw exploration during a run is ephemeral, the wiki is what persists.

If the target has no local git checkout (e.g. you're only hitting a deployed URL with no repo on disk), fall back to the skill's own workspace and tell the user the wiki won't be shared with the team until it's moved into the project repo.

Layout, one wiki per repo (not per target-slug — a single project may have multiple environments, but one shared brain):

```
.qa-wiki/
  CLAUDE.md              # the schema: conventions, page formats, workflow rules — copy from templates/CLAUDE.md on first run, never overwrite after
  index.md               # catalog: open bugs, fixed bugs, flows tested, last-tested date
  log.md                 # append-only, one line per run: "## [YYYY-MM-DD] run | tracker=<x> | N found (M new, K regressions)"
  bugs/<bug-slug>.md     # one page per distinct bug: status, first-found/last-seen dates, repro, evidence paths, ticket/issue link
  flows/<flow-slug>.md   # one page per distinct user flow exercised, linking to the bugs found in it
  screenshots/<bug-slug>/NN-step.png   # the actual persisted evidence files
```

**First run in a repo**: if `.qa-wiki/` doesn't exist yet, initialize it by copying `templates/CLAUDE.md`, `templates/index.md`, and `templates/log.md` from this skill into the target repo's `.qa-wiki/`, then commit them (`qa-wiki: initialize shared QA knowledge base`) after confirming with the user — this is the first shared artifact other developers will see. `.qa-wiki/CLAUDE.md` is the schema contract for the directory; read it at the start of every run (it may have been hand-edited by the team since last time) and follow it exactly rather than the summary below.

`index.md` is what you read before a run (what's already known); `log.md` is the timeline; `bugs/*.md` and `flows/*.md` are living pages updated in place rather than re-created. At the end of a run, `git add .qa-wiki && git commit` the changes (small, clear message) so the update lands in the team's normal git history, not just on local disk — confirm with the user first, the same as any other commit.

## Workflow

### 0. Setup interview

Before opening the browser, ask the user — in one question round where possible, never inferred from repo context:

1. **Target URL** — a deployed URL, or localhost? If localhost, which port, and does the dev server need starting first (start it if so)?
2. **Environment** — staging/test or production? Production means read-only exploration only: no form submissions that persist data, no destructive controls.
3. **Tracker** — first detect what's actually available: search for a connected Jira MCP via ToolSearch, and check `gh auth status` plus whether the repo has issues enabled (`gh repo view --json hasIssuesEnabled`). Present what you found and confirm the destination. If neither tracker works, stop and tell the user — finding bugs with nowhere to report them wastes the run.

### 1. Consult the wiki, then Jira

Check `.qa-wiki/CLAUDE.md` (schema, may have been edited by the team since last run), `.qa-wiki/index.md`, and the tail of `log.md` first. If they exist, tell the user what's already known — open bugs, flows tested, when it was last tested — before doing anything else. This shapes the run: known-open bugs get re-verified (still broken? now fixed?) rather than re-discovered from scratch and re-filed as duplicates. If `.qa-wiki/` doesn't exist yet, initialize it per the "First run in a repo" step above before continuing.

Then, if a Jira MCP is connected, query it for open QA-related work (assigned-to-QA, labeled "QA"/"testing", or in a "Ready for QA"-style status — follow whatever convention the project actually uses) and list what you find: ticket key, title, enough context to tell them apart. Ask which one to start with; the chosen ticket defines what flow to verify. If it doesn't name a URL or flow, ask.

If there's no Jira, or no relevant open ticket, run free exploration instead — and for each confirmed bug, offer to **create** a new ticket or GitHub issue rather than assuming one exists to comment on.

### 2. Explore with the browser

Delegate the click-everything exploration to a subagent so hundreds of interactions and screenshots don't bloat the main conversation. Give it the URL, the environment constraints from step 0, what the wiki already knows (step 1), and this mandate:

- Open the target with `navigate` (or `preview_start` for a local dev server).
- Use `read_page`/`find` to enumerate interactive elements, and `computer` to click every one, follow every link, open every menu and modal.
- Submit forms with edge-case input: empty, way-too-long, wrong type, special characters, unicode, whitespace-only.
- `resize_window` through the mobile/tablet/desktop presets and re-check key screens at each.
- Mash back/forward through history, refresh mid-action, double-submit a form, hit a nonsense route.
- Watch `read_console_messages` (errors) and `read_network_requests` (failed requests) after each significant action — these catch bugs the UI hides.
- Note anything that looks broken at the moment of failure (don't worry about persisting the screenshot yet — that's a deliberate re-run in step 4, using Playwright, once you know exactly which bugs are real).

A form correctly rejecting bad input with a clear error is the app working, not a bug — only flag things that break when they shouldn't. Cross-check against the wiki: if something matches a bug already marked "fixed," that's a **regression** — call it out explicitly, it's more urgent than a fresh find.

### 3. Bug report standard

Every report — ticket, issue, comment, or wiki page — contains:

- **Title**: the specific broken behavior, e.g. "Back button after failed checkout re-submits the order" — not "Bug in checkout".
- **Repro steps**: numbered, minimal, starting from a fresh page load.
- **Expected vs. actual**: one line each.
- **Environment**: URL, viewport size, browser, timestamp.
- **Severity**: with a one-line justification tied to user impact.
- **Evidence**: screenshot/GIF attached; console errors or failed request details quoted when they're part of the story.

Tone: the way a good teammate flags a problem — professional, direct, human. No filler ("I have identified the following issue…"), no speculation about root cause unless the evidence actually supports it.

### 4. Evidence: real screenshot files and a repro GIF

For each confirmed bug, re-run its **minimal** repro from a fresh page load, and this time capture it for real:

1. At each step, call Playwright's `browser_take_screenshot` with an explicit `filename` pointing into `.qa-wiki/screenshots/<bug-slug>/` — e.g. `01-initial.png`, `02-typed-input.png`, `03-after-submit.png`. This is what actually persists a file; nothing else in this toolset does.
2. If `ffmpeg` is available (`which ffmpeg`), assemble the numbered PNGs into a GIF: `ffmpeg -framerate 1 -pattern_type glob -i '*.png' repro.gif` — one frame per second reads like a slow screen recording. No ffmpeg → attach the numbered screenshots instead.
3. GitHub: `gh issue create` can't upload images into the body, so host the artifacts first — a dedicated `qa-artifacts` branch or a gist, pushed via `gh` — and embed the raw URLs as `![repro](…)` markdown. Ask the user which hosting they prefer the first time, then reuse that choice.
4. Jira: use the Jira MCP's attachment capability if it has one; otherwise embed the same hosted URLs in the ticket/comment body.
5. Minimum bar: every filed report carries the failure-point screenshot; include the GIF whenever the repro is a sequence of interactions.

Before filing anything, dedupe: check the wiki's `bugs/` pages and search existing issues/tickets (`gh issue list --search`, or the Jira project) — comment on a match instead of opening a duplicate.

### 5. Confirm before filing

Filing a ticket or posting a comment is visible to the whole team. Show the user each draft — destination, title, body — and wait for a yes before running `gh issue create` or any Jira write, unless they already said to file whatever you find.

### 6. Update the wiki

Regardless of whether filing happened yet, record the run:

- For each bug: create or update its `bugs/<bug-slug>.md` page (status, first-found/last-seen dates, repro, evidence paths, ticket/issue link once filed). A previously-open bug that's now fixed gets marked fixed with the date; a previously-fixed one that reappeared gets marked regressed.
- For each flow exercised: create or update its `flows/<flow-slug>.md` page (last-tested date, coverage, links to bugs found there).
- Update `index.md`'s catalog and last-tested date.
- Append one line to `log.md`: `## [YYYY-MM-DD] run | tracker=<x> | N found (M new, K regressions)`.
- Confirm with the user, then `git add .qa-wiki && git commit -m "qa-wiki: <short summary of this run>"` so the update lands in the repo's normal history — this is a shared brain other developers and future runs read from, not local scratch state.

This is what makes the next run start smarter instead of from scratch.

## Safety

- Never trigger destructive or irreversible actions while exploring (deleting records, real purchases, changing account settings). If a control looks destructive, stop and treat "this fires without confirmation" as the bug rather than actually confirming it.
- Only test against staging/test data unless the user has explicitly said the target is safe to hit in production.
- Never type real credentials or payment details into forms — use obviously fake test values.
