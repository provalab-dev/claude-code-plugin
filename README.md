# ProvaLab — Coding-Agent Plugin

ProvaLab integration for AI coding agents (Claude Code, Cursor, Codex,
Antigravity, Windsurf). Lets your agent **run, generate, and triage
ProvaLab tests** directly from the editor via the ProvaLab MCP server
at `https://mcp.provalab.io/mcp` (streamable-HTTP transport).

Under the hood it's an MCP server plus a tiny auth helper
(`provalab-auth`). Each agent speaks MCP the same way; only the config
file where you tell it about the server differs.

---

## Prerequisites

Install the `provalab-auth` CLI once per machine so your agent can mint
short-lived OAuth tokens.

**macOS / Linux:**

```bash
curl -sSf https://plugins.provalab.io/install.sh | sh
provalab-auth login
```

**Windows (PowerShell):**

```powershell
irm https://plugins.provalab.io/install.ps1 | iex
provalab-auth login
```

`login` opens a browser (or prints a URL + code on headless machines)
and caches a refresh token at `~/.config/provalab/auth.json`. The CLI
is Python 3.9+ with no external deps.

---

## Install per agent

### Claude Code (full marketplace, with skills + slash commands)

```
/plugin marketplace add provalab-dev/claude-code-plugin
/plugin install provalab@provalab-marketplace
```

Restart Claude Code and run `/mcp` — the `provalab` server should show
as connected. The plugin adds `/provalab-test`, `/provalab-status`,
`/provalab-results` commands plus run/triage skills.

### Cursor

Edit `~/.cursor/mcp.json` (global) or `.cursor/mcp.json` (project) and
merge in:

```json
{
  "mcpServers": {
    "provalab": {
      "type": "http",
      "url": "https://mcp.provalab.io/mcp",
      "headersHelper": "provalab-auth mcp-header"
    }
  }
}
```

Restart Cursor.

### OpenAI Codex CLI

Add to `~/.codex/config.toml`:

```toml
[mcp_servers.provalab]
type = "http"
url = "https://mcp.provalab.io/mcp"
headers_cmd = ["provalab-auth", "mcp-header"]
```

### Google Antigravity

Edit the Antigravity MCP config (same JSON shape as Cursor):

```json
{
  "mcpServers": {
    "provalab": {
      "type": "http",
      "url": "https://mcp.provalab.io/mcp",
      "headersHelper": "provalab-auth mcp-header"
    }
  }
}
```

### Codeium Windsurf

Edit `~/.codeium/windsurf/mcp_config.json`:

```json
{
  "mcpServers": {
    "provalab": {
      "type": "http",
      "url": "https://mcp.provalab.io/mcp",
      "headersHelper": "provalab-auth mcp-header"
    }
  }
}
```

---

## Why `"type": "http"`, not `"sse"`?

ProvaLab's MCP endpoint speaks the **streamable-HTTP** transport at
`/mcp`. The legacy SSE endpoint at `/mcp/sse` is deprecated and
connections time out after 30s — don't use it.

---

## Verifying it works

With any agent, ask it:

```
List my ProvaLab test runs from the last 24h.
```

The agent should call `tms_list_test_runs` (or similar) via MCP and
return a list. If you see "MCP server not reachable" or auth errors,
run `provalab-auth status` to confirm the token is still valid, then
`provalab-auth login` to refresh.

---

## What's in the Claude Code plugin specifically

Only Claude Code supports packaged skills + slash commands — the other
agents just talk to the MCP server directly.

| Item | Trigger | Purpose |
|---|---|---|
| `/provalab-test` | slash command | Kick off a ProvaLab run from the agent |
| `/provalab-status` | slash command | Poll an in-flight run |
| `/provalab-results` | slash command | Pull failures + diffs for triage |
| `run-tests` | skill | Agent uses this when you ask it to run tests |
| `generate-and-run` | skill | Generates missing tests, then runs them |
| `check-status` | skill | Polls run status with sensible timeouts |
| `triage-failures` | skill | Pulls failure info and proposes fixes |

For Cursor / Codex / Antigravity / Windsurf, those capabilities are
still available — just invoke them through natural language and the
agent will choose the right MCP tool.

---

## License

MIT.
