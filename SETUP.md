# QA Agent Skill Setup

Complete these steps before using the skill for the first time. Pick a tracker — GitHub issues, Jira, or both. Neither is mandatory on its own; the skill detects what's actually connected/authenticated at the start of each run and asks you to confirm.

## Always needed

- `claude` CLI installed and authenticated, with Claude's browser tools available.
- **Playwright MCP** connected — this is what actually persists screenshot files to disk (see main [README](README.md)).
- `ffmpeg` recommended (not required): without it, evidence falls back to individual screenshots instead of an assembled repro GIF. `brew install ffmpeg` (macOS) or your package manager.

## Option A: GitHub Issues

Nothing Jira-related needed for this path.

### 1. Authenticate `gh`

```bash
gh auth login
```

### 2. Enable Issues on the target repo (if not already)

```bash
gh repo edit <owner>/<repo> --enable-issues
gh repo view <owner>/<repo> --json hasIssuesEnabled   # verify
```

### 3. Evidence hosting — no setup required

`gh issue create` can't attach images directly, so the skill hosts screenshots/GIFs itself on first run and embeds them as `![repro](<raw-url>)` markdown, which GitHub renders inline in the issue. Two ways it can do this — it'll ask which you prefer the first time, then reuse that choice:

- **Dedicated branch** (default): pushes to an orphan `qa-artifacts` branch in the target repo, referenced via `https://raw.githubusercontent.com/<owner>/<repo>/qa-artifacts/<path>`.
- **Gist**: `gh gist create`, referenced via the gist's own raw file URL.

Either way, nothing needs to be pre-created — the skill sets this up the first time it files a GitHub bug with evidence.

That's the whole setup for GitHub: `gh auth login` + issues enabled.

## Option B: Jira (optional — only if you actually track QA work there)

Skip this entirely if GitHub issues are enough for you.

### Connect the Jira MCP

For Jira Cloud:

```bash
claude mcp add --transport http atlassian https://mcp.atlassian.com/v1/mcp/authv2
```

This will:
1. Prompt you to authenticate with Atlassian OAuth 2.1
2. Grant Claude access to your Jira Cloud instance
3. Store the connection in your Claude config

### Verify Jira is connected

Start a new Claude session and run:

```
search for jira tickets in the current Jira project
```

If Claude can find and describe tickets, Jira MCP is working.

## Ready to Test

Trigger it with:

```
test my app at https://your-app.example.com
```

The skill will:
1. Ask for the target URL and environment (staging/test vs. production), then detect what's actually available for filing — connected Jira MCP, and/or `gh` auth + issues-enabled — and confirm the destination with you.
2. If Jira is connected, fetch open QA tickets and ask which to start with; otherwise explore freely.
3. Open the app, explore like a confused/adversarial user, submit edge-case input.
4. Independently re-verify anything that looks broken before treating it as a confirmed bug.
5. Draft the report and show it to you before filing anything.
6. File as a GitHub issue and/or Jira ticket with evidence attached, on your confirmation.

---

## Troubleshooting

**"GitHub issues aren't being filed"**
- Verify `gh auth status` shows you're logged in.
- Verify the target repo has issues enabled: `gh repo view --json hasIssuesEnabled`.
- Check that you have push access to the repo (needed for the `qa-artifacts` branch, if that's the hosting choice).

**"No Jira MCP connected"** (only relevant if you're using Jira)
- Did you run `claude mcp add atlassian ...` and complete the OAuth flow?
- Restart Claude after connecting.
- Check settings to ensure the atlassian connector is enabled.

**"Jira MCP found but can't query tickets"**
- Verify your Jira user has permission to view QA-labeled or "Ready for QA" tickets.
- Check that the Jira instance URL is correct in the MCP config.
