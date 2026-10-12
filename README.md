# ProvaLab — Coding-Agent Plugin

ProvaLab integration for AI coding agents (Claude Code, Cursor, Codex,
Antigravity, Windsurf). Lets your agent **run, generate, and triage
ProvaLab tests** directly from the editor via the ProvaLab MCP server
at `https://mcp.provalab.io/mcp/sse`.

Under the hood it's an MCP server plus a tiny auth helper
(`provalab-auth`). Each agent speaks MCP the same way; only the config
file where you tell it about the server differs.

---

## Prerequisites

Install the `provalab-auth` CLI once per machine so the agent can mint
short-lived OAuth tokens for ProvaLab:

```bash
pip install provalab-auth    # or: pipx install provalab-auth
provalab-auth login          # opens a browser, caches a refresh token
```

---

## Install per agent

### Claude Code (full marketplace, with skills + slash commands)

```
/plugin marketplace add provalab-dev/claude-code-plugin
/plugin install provalab@provalab-marketplace
```

That's it — the plugin adds `/provalab-test`, `/provalab-status`,
`/provalab-results` commands plus run/triage skills.

### Cursor

Edit `~/.cursor/mcp.json` (global) or `.cursor/mcp.json` (project)
and merge in:

```json
{
  "mcpServers": {
    "provalab": {
      "type": "sse",
      "url": "https://mcp.provalab.io/mcp/sse",
      "headersHelper": "sh -c 'token=$(provalab-auth token); printf \"Authorization: Bearer %s\\r\\n\" \"$token\"'"
    }
  }
}
```

Restart Cursor.

### OpenAI Codex CLI

Add to `~/.codex/config.toml`:

```toml
[mcp_servers.provalab]
type = "sse"
url = "https://mcp.provalab.io/mcp/sse"
headers_cmd = ["sh", "-c", "token=$(provalab-auth token); printf 'Authorization: Bearer %s\\r\\n' \"$token\""]
```

### Google Antigravity

Edit the Antigravity MCP config (same JSON shape as Cursor):

```json
{
  "mcpServers": {
    "provalab": {
      "type": "sse",
      "url": "https://mcp.provalab.io/mcp/sse",
      "headersHelper": "sh -c 'token=$(provalab-auth token); printf \"Authorization: Bearer %s\\r\\n\" \"$token\"'"
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
      "type": "sse",
      "url": "https://mcp.provalab.io/mcp/sse",
      "headersHelper": "sh -c 'token=$(provalab-auth token); printf \"Authorization: Bearer %s\\r\\n\" \"$token\"'"
    }
  }
}
```

---

## Verifying it works

With any agent, ask it:
```
List my ProvaLab test runs from the last 24h.
```

The agent should call `provalab:api.list_runs` (or similar) via MCP
and return a list. If you see "MCP server not reachable" or auth
errors, run `provalab-auth login` again.

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
