# ProvaLab for Claude Code

Run, generate and triage ProvaLab tests, and get your changes reviewed by the
ProvaLab PR review bot before you commit, without leaving Claude Code.

This plugin contains **no business logic and defines no tools of its own**. It bundles
a connector to the ProvaLab remote MCP server and adds skills and slash commands that
teach Claude Code how to drive it — pick the tests, run them, read the results honestly.

## Install

```
/plugin marketplace add provalab-dev/claude-code-plugin
/plugin install provalab@provalab-marketplace
```

Restart Claude Code once so the MCP server loads, then sign in (next section).

**Use either this plugin or the claude.ai ProvaLab connector, not both.** Both point at
`https://mcp.provalab.io/mcp`, and Claude Code connects to one endpoint only once. A
plugin-provided server ranks above a claude.ai connector, so with the plugin enabled
`/mcp` lists the connector as `hidden — same URL as your server 'plugin:provalab:api'`.
That is expected: the plugin's server gives you the same tools. To go back to the
connector, disable the plugin's server in `/plugins` (or run
`/plugin disable provalab@provalab-marketplace`) and restart.

## Authentication

The plugin signs its MCP requests with a token from `provalab-auth`, a small CLI that
runs the OAuth device flow, so it also works on headless machines (SSH sessions, VPSes,
containers, CI). One-time setup:

```
# 1. Install the CLI (Python 3.9+; stdlib only, no other dependencies)
curl -fsSL https://plugins.provalab.io/install.sh | sh

# 2. Sign in (prints a URL and a short code; approve it in any browser)
provalab-auth login
```

You'll see something like:

```
  ┌────────────────────────────────────────────────┐
  │  Enter code:   BCDF-GHJK                       │
  └────────────────────────────────────────────────┘

  Open this URL in ANY browser (any device):
     https://auth.provalab.io/device?user_code=BCDF-GHJK

  Waiting for approval....
```

Approve it on your phone or laptop. The CLI stores the token at
`~/.config/provalab/auth.json`, and expired tokens refresh silently.

The plugin does not need `provalab-auth` on your `PATH`: its `.mcp.json` runs the copy
bundled with the plugin, `python3 "${CLAUDE_PLUGIN_ROOT}/bin/provalab_auth.py" mcp-header`,
which prints `{"Authorization": "Bearer <token>"}` as Claude Code's `headersHelper`
requires. It reads the same token file, so one `provalab-auth login` covers it. If you
would rather not install the CLI at all, run that bundled script with `login` instead.

To sign out: `provalab-auth logout`. To check state: `provalab-auth status`.

### Checking the connection

```
claude mcp list
```

should show `plugin:provalab:api: https://mcp.provalab.io/mcp (HTTP) - ✔ Connected`.

| You see | Meaning |
|---|---|
| `! Needs authentication` | The helper produced no token. Run `provalab-auth status`, then `provalab-auth login`, then `/mcp` → reconnect. |
| `✘ Failed to connect … (HTTP 401)` | The token was rejected or expired and could not refresh. Run `provalab-auth login`. |
| `✘ Failed to connect … (HTTP 403)` | Signed in, but `PROVALAB_ORG_ID` / `PROVALAB_PROJECT_ID` name an org you are not an active member of, or a project outside that org. Fix or unset them (see [Configuration](#configuration)). |

## Usage

Ask in plain language — the skills trigger on intent:

- *"Run the login tests for the checkout project"*
- *"Generate tests for https://staging.example.com/signup and run them"*
- *"Why did run 8412 fail?"*
- *"Did last night's run pass?"*
- *"Review my changes before I commit"*

Or use the slash commands:

| Command | Does |
|---|---|
| `/provalab-test <project> [target]` | Run the suite (or a target area) and report the result |
| `/provalab-status [test_run_id]` | Status of a recorded run, or the most recent one |
| `/provalab-results <test_run_id>` | Fetch and summarise results, grouped by cause |

## Reviewing changes before a commit

The plugin's second MCP server, `review` (`https://reviews.provalab.io/mcp`), is the
ProvaLab PR review bot. The `review-changes` skill sends your uncommitted or unpushed
changes to it, works through each finding (fix it, or answer with a reason; the bot
re-checks a disagreement), and rechecks until nothing is left unanswered. Nothing is
posted to GitHub.

It uses the same sign-in as the rest of the plugin: no key to paste. You can review a
repository when its GitHub installation of the Prova PR bot is linked to one of your
ProvaLab orgs (an org owner links it on reviews.provalab.io). For CI and scripts, use
an API key from that dashboard instead.

## How it behaves

Running a suite is **synchronous**: `execute_pytest` returns when the suite has
finished, with the full result. One call records one TMS run, so the skills always run a
suite in a single call. The skills also enforce a few honesty rules that matter more
than they sound:

- Never report a result that has not been fetched.
- Never describe a failure whose error text has not been read.
- Group failures by cause, not by test. Twenty reds from one broken selector is one
  problem.
- Flag skipped tests, because a suite that skips half its cases can look green while
  proving very little.

## Server contract

The plugin talks to the **QA Agent's MCP server** at `https://mcp.provalab.io/mcp`
(streamable-HTTP). The skills are written against the tools that server actually exposes:

| Tool | Shape |
|---|---|
| `execute_pytest(workspace_paths \| files, framework, base_url, timeout_s)` | **synchronous** — runs the suite and returns the full result |
| `get_execution_result(execution_id)` | full pytest JSON for a past execution |
| `tms_list_test_runs(status?, page_size?)` | recent TMS runs, newest first |
| `tms_get_test_run_results(test_run_id)` | per-test results recorded in TMS |
| `tms_get_test_run_failures(run_id)` | failed results with first console error + stack trace |
| `tms_get_similar_failures(result_id)` / `tms_classify_failure(result_id, category)` | triage helpers |
| `tms_list_projects(search?)` | projects in your organization |
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

Login proves *who* you are. The server then picks *which* org and project you act in:

- **Organization**: your first active membership. If you belong to more than one org,
  set `PROVALAB_ORG_ID` to the org's Identity UUID before starting Claude Code.
- **Project**: the org's only project, when it has exactly one. Otherwise set
  `PROVALAB_PROJECT_ID`, or pass `project_id` to the tools that take it.

The helper sends these as `X-Organization-Id` / `X-Project-Id` only when they are set
and non-empty. The server checks that you are an active member of the org, and that the
project belongs to it, before running anything, so a stale or wrong id fails with 403
instead of writing into the wrong project.

Tools that accept `organization_id` / `project_id` (`execute_pytest`,
`tms_list_test_runs`) should still be passed them explicitly. An invisible default is
the wrong thing to rely on when a wrong value writes results into someone else's
project.

### Tool namespacing

Plugin-bundled MCP tools are namespaced `mcp__plugin_<plugin>_<server>__<tool>`, so with
plugin `provalab` and server key `api` they surface as, for example:

```
mcp__plugin_provalab_api__execute_pytest
```

This matters for permission rules, `allowed-tools`, and hook matchers. A bare
`mcp__provalab__*` matcher will **not** fire for a plugin-bundled server; use
`mcp__plugin_provalab_api__*`.

## Layout

```
provalab-claude-plugin/
├── .claude-plugin/marketplace.json
└── plugins/provalab/
    ├── .claude-plugin/plugin.json
    ├── .mcp.json                     # remote MCP connector (plugin ROOT, not in .claude-plugin/)
    ├── bin/provalab_auth.py          # bundled auth CLI; .mcp.json's headersHelper runs it
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
- Remote transports, OAuth, `headersHelper`, duplicate servers vs connectors — https://code.claude.com/docs/en/mcp.md
- Marketplace schema and install flow — https://code.claude.com/docs/en/plugin-marketplaces.md
