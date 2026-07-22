# qa-agent-skill

Turn Claude into an autonomous QA tester for your web app. Say "test my app" and Claude opens it in a browser, explores it like a confused/adversarial user — clicks everything, submits garbage into forms, resizes the viewport, mashes back/forward, tries invalid routes — and files real bugs it finds as GitHub issues or Jira tickets, each with a repro (numbered screenshots, assembled into a GIF) and a clear write-up.

## What it does

1. **Setup interview** — asks for the target URL (local dev server or deployed), the environment (staging/test vs. production — production is read-only), and which tracker to use (Jira and/or GitHub).
2. **Jira-first** — if a Jira MCP is connected, fetches open QA tickets and asks which one to start with. No ticket or no Jira? It explores freely and offers to create one for anything it finds.
3. **Exploration** — drives the app with Claude's browser tools, clicking every interactive element, submitting edge-case input (empty, oversized, wrong type, special characters, unicode), resizing across breakpoints, and mashing browser history — while watching the console and network tab for real failures.
4. **Evidence** — captures a numbered screenshot at each repro step and assembles them into a GIF (via `ffmpeg`) so every bug report comes with a visual repro, not just prose.
5. **Reports** — every filed bug follows a fixed standard: specific title, minimal numbered repro, expected vs. actual, environment, justified severity, and evidence. Written the way a teammate would flag it, not "I have identified the following issue."
6. **Confirms before filing** — shows you the draft (destination + title + body) and waits for a yes before creating anything, since filing is visible to your whole team.

It deliberately distinguishes real bugs (crashes, console exceptions, broken layouts, silent data loss, validation bypass) from expected behavior (a form correctly rejecting bad input is not a bug).

## Requirements

- [Claude Code](https://code.claude.com) with Claude's browser tools available
- `gh` CLI authenticated (`gh auth login`) if filing to GitHub issues
- A connected Jira MCP if filing to Jira — see [SETUP.md](SETUP.md) for the official Atlassian Rovo MCP server setup
- `ffmpeg` (optional) for assembling repro GIFs — falls back to individual screenshots if not installed

## Installation

```bash
git clone https://github.com/amalshehu/qa-agent-skill.git ~/Code/qa-agent-skill
ln -s ~/Code/qa-agent-skill ~/.claude/skills/qa-agent-skill
```

Restart Claude Code (or start a new session) so it picks up the skill. Then just say:

```
test my app at https://staging.example.com
```

See [SETUP.md](SETUP.md) for connecting Jira and enabling GitHub issues on your repo.

## Safety

- Never triggers destructive/irreversible actions while exploring — a control that looks destructive is treated as the bug, not confirmed.
- Only tests against staging/test data unless you've explicitly said production is safe to hit.
- Never types real credentials or payment details — uses obviously fake test values.

## License

MIT — see [LICENSE](LICENSE).
