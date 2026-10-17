---
description: Fetch and summarise the results of a ProvaLab test run, grouping failures by cause.
argument-hint: <test_run_id>
---

Fetch and summarise ProvaLab results.

- TMS test run id: `$1`

Do this:

1. If `$1` is empty, ask for a run id or offer the newest run from `tms_list_test_runs`. Do not guess. Summarising the wrong run is worse than asking.
2. Call `tms_get_test_run_results(test_run_id=$1)` for the counts. If anything failed, call `tms_get_test_run_failures(run_id=$1)`, which returns each failed result with its first console error and stack trace.
3. Lead with the outcome and real counts: passed, failed, errored, skipped.
4. Group failures **by cause, not by test**. Twenty tests failing on one broken selector is one problem, not twenty.
5. Separate assertion failures from infrastructure errors such as timeouts and refused connections. They send the user in different directions.
6. Quote actual error text. Never paraphrase an error you have not read, and say so plainly if a cause is ambiguous.

Flag skipped tests explicitly. A suite that skips half its tests can look green while proving very little.
