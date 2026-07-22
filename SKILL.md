---
name: qa-agent-skill
description: Turns Claude into an autonomous QA tester for a running web app. Use whenever the user says "test my app", "find bugs", "QA this", "break this app", "click around and see what breaks", or asks Claude to stress-test or bug-hunt a live URL or dev server — even if they just say "test it" or "does this work" without naming GitHub or Jira. Claude drives the app in a real browser via Playwright MCP, acts like a confused/adversarial user (clicks everything, submits garbage into forms, resizes the viewport, mashes back/forward), and for every genuine bug found writes a professional, human-sounding repro with a screenshot or recording attached, then files it as a GitHub issue (gh CLI) or a comment on the matching Jira ticket (Jira MCP) — whichever the project actually uses.
---

# QA Agent

## What you need

- A running app to point the browser at (a URL, or a local dev server — start it first if it isn't running).
- Playwright MCP browser tools (or whatever browser automation MCP is connected) to drive the app.
- Either `gh` CLI authenticated to the target repo, or a Jira/Atlassian MCP connected. Check which is actually available (`gh repo view`, and search for a Jira MCP via ToolSearch) — don't assume one over the other.

## Workflow

### 1. Confirm target and tracker

Ask which app/URL to test if it isn't obvious from context. Then figure out where bugs should go: check whether the current repo has GitHub issues enabled, and check whether a Jira MCP is connected. If both are available, ask the user which one to use rather than guessing. If neither is available, say so before doing any exploration — there's no point finding bugs with nowhere to report them.

### 2. Explore via a subagent

Delegate the actual click-everything exploration to a subagent so hundreds of clicks and screenshots don't bloat the main conversation. Give it the URL, the viewport breakpoints to try (mobile/tablet/desktop), and the mandate:

- Click every interactive element, follow every link, open every menu/modal.
- Submit forms with edge-case input: empty, way-too-long, wrong type, special characters, unicode, whitespace-only.
- Mash back/forward through browser history, refresh mid-action, try double-submitting a form, hit a nonsense route/URL.
- For anything that looks broken, record: exact repro steps, what was observed (console error, failed network request, visual break, crash, stuck loading state, silent data loss, validation bypass), and a screenshot at the point of failure. If a GIF-capable browser tool is connected, use it to record the repro sequence; otherwise a short set of before/during/after screenshots is the fallback artifact.

A form correctly rejecting bad input with a clear error is the app working, not a bug — only flag things that break when they shouldn't.

### 3. Filter and dedupe

Before filing anything, check whether an existing issue or ticket already covers it (`gh issue list --search`, or search the Jira project). If one exists, comment on it instead of opening a duplicate.

### 4. Write it up like a person, not a bot

- Title: short and specific, e.g. "Back button after failed checkout re-submits the order."
- Body: numbered repro steps, expected vs. actual, environment (URL, viewport, browser), severity, screenshot/recording attached.
- Write it the way a teammate would flag it, not "I have identified the following issue."

### 5. Confirm before filing

Filing an issue or posting a comment is visible to the whole team — tell the user what you're about to file or comment (title + destination) and wait for a yes before running `gh issue create` or posting to Jira, unless they already said to file whatever you find.

## Safety

- Never trigger destructive or irreversible actions while exploring (deleting records, real purchases, changing account settings). If a control looks destructive, stop and treat "this fires without confirmation" as the bug rather than actually confirming it.
- Only test against staging/test data unless the user has explicitly said the target is safe to hit in production.
- Never type real credentials or payment details into forms — use obviously fake test values.
