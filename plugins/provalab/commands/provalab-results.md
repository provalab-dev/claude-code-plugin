---
description: Fetch and summarise the results of a completed ProvaLab run, grouping failures by cause.
argument-hint: <run_id>
---

Fetch and summarise ProvaLab results.

- Run ID: `$1`

Do this:

1. If `$1` is empty, ask for a run ID or offer the most recent run from `provalab_list_runs`. Do not guess — summarising the wrong run is worse than asking.
2. Call `provalab_get_results($1)`. If `provalab_triage` is available, call it too — it may already group failures by cause.
3. Lead with the outcome and real counts: passed, failed, errored, skipped.
4. If anything failed, group failures **by cause, not by test** — twenty tests failing on one broken selector is one problem, not twenty.
5. Separate genuine assertion failures from infrastructure errors (timeouts, connection refused). They mean different things and send the user in different directions.
6. Quote actual error text. Never paraphrase an error you have not read, and say so plainly if a cause is ambiguous.

Flag skipped tests explicitly — a suite that skips half its tests can look green while proving very little.
