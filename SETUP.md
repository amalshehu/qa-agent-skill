# QA Agent Skill Setup

Complete these steps before using the skill for the first time.

## Prerequisites

- `claude` CLI installed and authenticated
- `gh` CLI authenticated to GitHub with repo access
- A Jira Cloud instance (or self-hosted Jira Server/Data Center)

## 1. Enable GitHub Issues on Target Repo (if needed)

If bugs should file to GitHub, ensure the repo has issues enabled:

```bash
gh repo edit <owner>/<repo> --enable-issues
```

Example:
```bash
gh repo edit your-org/your-repo --enable-issues
```

Verify:
```bash
gh repo view your-org/your-repo --json hasIssuesEnabled
```

## 2. Connect Jira MCP (Required)

The skill fetches open QA tickets from Jira, so you need the official Atlassian Rovo MCP server connected.

### For Jira Cloud (recommended):

Run this command in a terminal:

```bash
claude mcp add --transport http atlassian https://mcp.atlassian.com/v1/mcp/authv2
```

This will:
1. Prompt you to authenticate with Atlassian OAuth 2.1
2. Grant Claude access to your Jira Cloud instance
3. Store the connection in your Claude config

### For Jira Server / Data Center (self-hosted):

Use the community `sooperset/mcp-atlassian` instead:

```bash
git clone https://github.com/sooperset/mcp-atlassian.git /path/to/mcp-atlassian
cd /path/to/mcp-atlassian
npm install
# Then configure in your Claude settings pointing to the local server
```

### Verify Jira is Connected:

After connecting, start a new Claude session and run:

```
search for jira tickets in the current Jira project
```

If Claude can find and describe tickets, Jira MCP is working.

## 3. (Optional) Create `.qa-artifacts` directory in repo

The skill saves screenshots and GIFs to `.qa-artifacts/<bug-slug>/` in the target repo for hosting:

```bash
mkdir -p .qa-artifacts
git add .qa-artifacts/.gitkeep  # placeholder
git commit -m "Add .qa-artifacts directory for QA evidence"
```

## Ready to Test

Once Jira is connected, the skill is ready. Trigger it with:

```
test my app at https://staging.app.rubix.world
```

The skill will:
1. Fetch open QA tickets from Jira and ask which to start with
2. Open the app in Claude's browser
3. Explore like a confused user, click everything, submit garbage input
4. File bugs as Jira tickets/comments or GitHub issues with evidence attached

---

## Troubleshooting

**"No Jira MCP connected"**
- Did you run `claude mcp add atlassian ...` and complete the OAuth flow?
- Restart Claude after connecting.
- Check settings to ensure the atlassian connector is enabled.

**"Jira MCP found but can't query tickets"**
- Verify your Jira user has permission to view QA-labeled or "Ready for QA" tickets.
- Check that the Jira instance URL is correct in the MCP config.

**"GitHub issues aren't being filed"**
- Verify `gh auth status` shows you're logged in.
- Verify the target repo has issues enabled: `gh repo view --json hasIssuesEnabled`
- Check that you have push/write access to the repo.
