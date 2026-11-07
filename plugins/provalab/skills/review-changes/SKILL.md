---
name: review-changes
description: Get a code review of your local changes from the ProvaLab PR review bot before you commit or open a pull request, then fix or answer each finding and recheck. Use when the user asks to review changes, before a commit or PR in a repository where the Prova PR bot GitHub App is installed, or when they say "review my changes" / "prova review" / "review before commit".
---

# Review changes before commit

The ProvaLab PR review bot reviews your uncommitted or unpushed changes over MCP (the
plugin's `review` server) with the same engine, code graph and team rules it uses on
pull requests. Nothing is posted to GitHub.

## Before you start

- The tools are `review_changes`, `get_review`, `respond_to_finding` and `recheck`
  from the `review` server. Sign-in is the plugin's ProvaLab sign-in: if the server is
  not connected, tell the user to run `provalab-auth login` (or `/provalab-status`)
  and restart Claude Code, and stop.
- The repository must be installed in the Prova PR bot GitHub App, and that GitHub
  installation linked to one of the user's ProvaLab orgs. If `review_changes` says
  it is not, show its message and stop.

## 1. Send the changes

1. `REPO`: `owner/name` from `git remote get-url origin`.
2. `BASE`: `git merge-base HEAD origin/main` (use the PR's target branch if not main).
   It must exist on GitHub; if `git branch -r --contains BASE` is empty, run
   `git fetch origin` and retry. Never send a commit that is only local.
3. New files are invisible to `git diff` until git knows them: `git add -N <path>`
   for each untracked file that belongs to the change (not build output or secrets).
4. `DIFF`: `git diff -M BASE` (working tree against the base; includes commits made
   since the base).
5. `FILES`: for every path in the diff that is not deleted, its full current content.
   Skip binary files. Never send `.env`, keys or other secrets: if the diff contains
   one, stop and tell the user.
6. Call `review_changes(repo, base_sha=BASE, diff=DIFF, files=FILES, intent=...)`;
   `intent` is one line on what the change is for.
7. Call `get_review(review_id, wait_s=50)` until `state` is `done` or `failed`
   (about a minute; a large change takes longer). On `failed`, show the error.

## 2. Work through the findings

For each item in `findings` (most severe first):

- Read the code at `file:start_line` yourself. Do not trust or dismiss it unread.
- **Right** → fix it (use `suggested_patch` if it fits), then
  `respond_to_finding(id, "fixed")`.
- **Wrong** → `respond_to_finding(id, "disagree", reason)` with the concrete reason:
  the line, caller or requirement that makes it wrong. The bot re-checks and answers
  in `get_review` under `recheck` (`agree` or `still_a_bug` with its reason). If it
  says `still_a_bug` with a reason you cannot refute, fix it.
- **Right but out of scope** (the user decided, or it is pre-existing code) →
  `respond_to_finding(id, "wont_fix", reason)`.
- `verified: false` findings are questions the reviewer could not confirm: check them,
  but a quick look is enough.
- `hints` are analyzer leads the bot did not post; fix only ones that are clearly real.

Never answer `fixed` without changing the code, and never `disagree` with a critical
or security finding on a guess: ask the user.

## 3. Recheck

After fixing, rebuild `DIFF` and `FILES` (same base) and call
`recheck(review_id, diff, files)`, then `get_review` on the new id. It lists
`resolved` findings from the previous round and marks each finding `still_open` or
`new`; your earlier `wont_fix` / dispute answers stay on still-open ones.

Repeat until no unanswered findings remain, at most 3 rechecks (each review costs
the team's budget; 30 reviews an hour per person). Then report to the user: what was
fixed, what you disputed and the bot's verdicts, what was left as won't-fix and why.
Commit or open the PR only if the user asked for that.
