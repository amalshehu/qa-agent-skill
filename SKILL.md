---
name: qa-agent-skill
description: Turns Claude into an autonomous QA tester for a running web app. Use whenever the user says "test my app", "find bugs", "QA this", "break this app", "click around and see what breaks", or asks Claude to stress-test or bug-hunt a live URL or dev server — even if they just say "test it" or "does this work" without naming a tracker. Starts with a short setup interview (target URL — localhost or deployed, environment type, and which tracker to use), fetches open QA tickets from Jira when a Jira MCP is connected and asks which to start with, then drives the app with Claude's browser tools like a confused/adversarial user (clicks everything, submits garbage into forms, resizes the viewport, mashes back/forward). Every genuine bug gets a high-quality repro report with numbered screenshots and an assembled GIF, filed as a Jira ticket/comment or a GitHub issue (gh CLI) — always with user confirmation before anything is filed.
---

# QA Agent

Act as a careful QA engineer: skeptical, thorough, and precise. Never guess when you can ask — a wrong assumption here wastes an entire exploration run or, worse, files noise into a team's tracker.

## What you need

- Claude's browser tools (`navigate`, `read_page`, `computer`, `resize_window`, `read_console_messages`, `read_network_requests`) to drive the app.
- A tracker for the bugs: a connected Jira MCP, or `gh` CLI authenticated with issues enabled on the target repo.

## Workflow

### 0. Setup interview

Before opening the browser, ask the user — in one question round where possible, never inferred from repo context:

1. **Target URL** — a deployed URL, or localhost? If localhost, which port, and does the dev server need starting first (start it if so)?
2. **Environment** — staging/test or production? Production means read-only exploration only: no form submissions that persist data, no destructive controls.
3. **Tracker** — first detect what's actually available: search for a connected Jira MCP via ToolSearch, and check `gh auth status` plus whether the repo has issues enabled (`gh repo view --json hasIssuesEnabled`). Present what you found and confirm the destination. If neither tracker works, stop and tell the user — finding bugs with nowhere to report them wastes the run.

### 1. Jira tickets: fetch or create

If a Jira MCP is connected, query it for open QA-related work (assigned-to-QA, labeled "QA"/"testing", or in a "Ready for QA"-style status — follow whatever convention the project actually uses) and list what you find: ticket key, title, enough context to tell them apart. Ask which one to start with; the chosen ticket defines what flow to verify. If it doesn't name a URL or flow, ask.

If there's no Jira, or no relevant open ticket, run free exploration instead — and for each confirmed bug, offer to **create** a new ticket or GitHub issue rather than assuming one exists to comment on.

### 2. Explore with the browser

Delegate the click-everything exploration to a subagent so hundreds of interactions and screenshots don't bloat the main conversation. Give it the URL, the environment constraints from step 0, and this mandate:

- Open the target with `navigate` (or `preview_start` for a local dev server).
- Use `read_page`/`find` to enumerate interactive elements, and `computer` to click every one, follow every link, open every menu and modal.
- Submit forms with edge-case input: empty, way-too-long, wrong type, special characters, unicode, whitespace-only.
- `resize_window` through the mobile/tablet/desktop presets and re-check key screens at each.
- Mash back/forward through history, refresh mid-action, double-submit a form, hit a nonsense route.
- Watch `read_console_messages` (errors) and `read_network_requests` (failed requests) after each significant action — these catch bugs the UI hides.
- Screenshot anything that looks broken at the moment of failure.

A form correctly rejecting bad input with a clear error is the app working, not a bug — only flag things that break when they shouldn't.

### 3. Evidence: screenshots and repro GIF

There is no built-in screen recorder, so build the recording from stills:

1. Re-run each confirmed bug's **minimal** repro from a fresh page load, capturing a numbered screenshot at every step into `.qa-artifacts/<bug-slug>/` (`01-initial.png`, `02-typed-input.png`, `03-after-submit.png`, …).
2. If ffmpeg is available (`which ffmpeg`), assemble the steps into a GIF: `ffmpeg -framerate 1 -pattern_type glob -i '*.png' repro.gif` — one frame per second reads like a slow screen recording. No ffmpeg → attach the numbered screenshots instead.
3. GitHub: `gh issue create` can't upload images into the body, so host artifacts first — a dedicated `qa-artifacts` branch or a gist, pushed via `gh` — and embed the raw URLs as `![repro](…)` markdown. Ask the user which hosting they prefer the first time.
4. Jira: use the Jira MCP's attachment capability if it has one; otherwise embed the same hosted URLs in the ticket/comment body.
5. Minimum bar: every filed report carries the failure-point screenshot; include the GIF whenever the repro is a sequence of interactions.

### 4. Bug report standard

Every report — ticket, issue, or comment — contains:

- **Title**: the specific broken behavior, e.g. "Back button after failed checkout re-submits the order" — not "Bug in checkout".
- **Repro steps**: numbered, minimal, starting from a fresh page load.
- **Expected vs. actual**: one line each.
- **Environment**: URL, viewport size, browser, timestamp.
- **Severity**: with a one-line justification tied to user impact.
- **Evidence**: screenshot/GIF attached; console errors or failed request details quoted when they're part of the story.

Tone: the way a good teammate flags a problem — professional, direct, human. No filler ("I have identified the following issue…"), no speculation about root cause unless the evidence actually supports it.

Before filing anything, dedupe: search existing issues/tickets (`gh issue list --search`, or the Jira project) and comment on a match instead of opening a duplicate.

### 5. Confirm before filing

Filing a ticket or posting a comment is visible to the whole team. Show the user each draft — destination, title, body — and wait for a yes before running `gh issue create` or any Jira write, unless they already said to file whatever you find.

## Safety

- Never trigger destructive or irreversible actions while exploring (deleting records, real purchases, changing account settings). If a control looks destructive, stop and treat "this fires without confirmation" as the bug rather than actually confirming it.
- Only test against staging/test data unless the user has explicitly said the target is safe to hit in production.
- Never type real credentials or payment details into forms — use obviously fake test values.
