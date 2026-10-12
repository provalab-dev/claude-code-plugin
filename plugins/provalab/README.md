# ProvaLab for Claude Code

Run, generate and triage ProvaLab tests without leaving Claude Code.

This plugin contains **no business logic and defines no tools of its own**. It bundles
a connector to the ProvaLab remote MCP server and adds skills and slash commands that
teach Claude Code how to drive it — start a run, poll it, read the results honestly.

## Install

```
/plugin marketplace add https://plugins.provalab.io/marketplace.json
/plugin install provalab@provalab-marketplace
```

Restart Claude Code once so the MCP server loads.

## Authentication

The plugin fetches its access token from `provalab-auth`, a small CLI
that runs the OAuth device flow — perfect for headless machines
(SSH sessions, VPSes, containers, CI). One-time setup:

```
# 1. Install the CLI (Python 3.9+ required; stdlib only, zero deps)
curl -fsSL https://plugins.provalab.io/install-auth | sh

# 2. Sign in (opens no browser — prints a URL + short code)
provalab-auth login
```

You'll see something like:

```
  ┌────────────────────────────────────────────────┐
  │  Enter code:   BCDF-GHJK                       │
  └────────────────────────────────────────────────┘

  Open this URL in ANY browser (any device):
     https://auth.provalab.io/device?user_code=BCDF-GHJK

  Or visit https://auth.provalab.io/device and enter the code above.

  Waiting for approval....
```

Open the URL on your phone, laptop, anywhere. Sign in, click Approve —
the CLI on the server sees the approval and stores your token at
`~/.config/provalab/auth.json`. Every future MCP call the plugin makes
uses that token; expired tokens refresh silently.

To sign out: `provalab-auth logout`. To check state: `provalab-auth status`.

**No API key, no localhost callback, no env vars to export**. The
plugin's `.mcp.json` shells out to `provalab-auth token` on each
connection.

## Usage

Ask in plain language — the skills trigger on intent:

- *"Run the login tests for the checkout project"*
- *"Generate tests for https://staging.example.com/signup and run them"*
- *"Why did run 8412 fail?"*
- *"Is my run done yet?"*

Or use the slash commands:

| Command | Does |
|---|---|
| `/provalab-test <project> [target]` | Start a run, then poll it to completion |
| `/provalab-status [run_id]` | Status of a run, or the most recent one |
| `/provalab-results <run_id>` | Fetch and summarise results, grouped by cause |

## How it behaves

Runs take minutes, so the whole design is **poll-based, never blocking**. Starting a run
returns a `run_id` immediately; a separate tool call polls for completion. The skills
enforce a few honesty rules that matter more than they sound:

- Never report a result that has not been fetched.
- Never describe a failure whose error text has not been read.
- Group failures by cause, not by test — twenty reds from one broken selector is one
  problem.
- Flag skipped tests, because a suite that skips half its cases can look green while
  proving very little.

## Server contract

The plugin talks to the **QA Agent's MCP server**, mounted at `/mcp/sse`. The skills
are written against the tools that server actually exposes:

| Tool | Shape |
|---|---|
| `execute_pytest(workspace_paths \| files, framework, base_url, timeout_s)` | **synchronous** — runs the suite and returns the full result |
| `get_execution_result(execution_id)` | full pytest JSON for a past execution |
| `tms_list_test_runs(status?, page_size?)` | recent TMS runs, newest first |
| `tms_get_test_run_results(test_run_id)` | per-test results recorded in TMS |
| `get_ui_test_inventory(domain)` | every UI test file for a domain + its test functions |
| `list_workspace_files` / `read_workspace_file` | anything not covered by the inventory |
| `analyze_page(url)` / `crawl_site(url)` | page structure, for writing tests |
| `get_session_artifacts` | screenshots, video and logs from a run |
| `get_project_context(project_id, organization_id, user_id)` | compiled project knowledge |

**Execution is synchronous.** There is no `run_id` to poll and no "running" state —
`execute_pytest` returns when the suite has finished. The earlier design assumed an
async start/poll lifecycle; the real server does not have one, and the skills were
rewritten around that rather than pretending otherwise. One call creates one TMS run,
which is why a suite is never split across calls.

Past runs are reachable two ways, and they are different handles on the same thing:
`get_execution_result(execution_id)` gives the full pytest report, while
`tms_list_test_runs` → `tms_get_test_run_results(test_run_id)` walks in from the TMS
side when no execution id is at hand. Prefer the execution report when you have the id.

### Configuration

`.mcp.json` defaults to the K3s NodePort. See [Authentication](#authentication) above
for `PROVALAB_MCP_URL` / `PROVALAB_AUTH_METADATA_URL` and the login flow itself — this
section is about the org/project selection that login does not cover.

Login proves *who* you are; `PROVALAB_ORG_ID` and `PROVALAB_PROJECT_ID` still say
*which* org/project you're acting in, and both are read from headers on every request.
**Set both before use.** Several tools take no id parameters at all
(`list_workspace_files`, `get_ui_test_inventory`) — they can only read them from here.
Left at the `0` default, those tools answer `"No project context available"`, which is
the intended failure: loud and specific. And unlike a bare header value, `0` is now also
checked server-side — the MCP server verifies you're an active member of that org (and,
if a project id is set, that the project actually belongs to that org) before running
anything, so a stale or wrong id fails with 403 rather than quietly writing into the
wrong project.

The defaults are `0` rather than empty for a reason worth keeping. An empty header value
— what an unset `${VAR:-}` expands to — made Claude Code reject **every** `tools/call`
with "Invalid request parameters" while `tools/list` still succeeded, so the plugin
looked connected and was not. Any non-empty value avoids that; `0` additionally fails
loudly instead of silently pointing at some real project that happens to exist (and, per
above, `0` is never a real org/project id you can be a member of, so the server-side
membership check rejects it too).

Tools that DO accept `organization_id` / `project_id` (`execute_pytest`,
`tms_list_test_runs`) should still be passed them explicitly. An invisible session
default is the wrong thing to rely on when a wrong value writes results into someone
else's project.

### Tool namespacing

Plugin-bundled MCP tools are namespaced `mcp__plugin_<plugin>_<server>__<tool>`, so with
plugin `provalab` and server key `api` they surface as:

```
mcp__plugin_provalab_api__provalab_run_tests
```

This matters for permission rules, `allowed-tools`, and hook matchers — a bare
`mcp__provalab__*` matcher will **not** fire for a plugin-bundled server.

Because the namespace already carries `provalab`, the `provalab_` prefix on each tool
name is redundant. Dropping it server-side would give the shorter
`mcp__plugin_provalab_api__run_tests`. Worth deciding before the tool names are public.

## Layout

```
provalab-claude-plugin/
├── .claude-plugin/marketplace.json
└── plugins/provalab/
    ├── .claude-plugin/plugin.json
    ├── .mcp.json                     # remote MCP connector (plugin ROOT, not in .claude-plugin/)
    ├── commands/
    ├── skills/
    └── README.md
```

Component directories live at the **plugin root**. Only `plugin.json` belongs inside
`.claude-plugin/` — putting `skills/` or `.mcp.json` there is a common failure mode.

## Schema sources

Verified against the current documentation:

- Plugin structure and `plugin.json` — https://code.claude.com/docs/en/plugins-reference.md
- Bundled MCP servers — https://code.claude.com/docs/en/plugins-reference.md#mcp-servers
- Remote transports, OAuth, `${VAR}` expansion — https://code.claude.com/docs/en/mcp.md
- Marketplace schema and install flow — https://code.claude.com/docs/en/plugin-marketplaces.md
