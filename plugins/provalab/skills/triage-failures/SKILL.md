---
name: triage-failures
description: Use when tests failed and the user wants to know why — "why did the run fail", "what broke", "triage these failures", "explain the errors", or when a completed run reported failures and the user asks what to do next.
---

# Triaging a failed ProvaLab run

The goal is to tell the user what actually broke and what to do about it. A list
of red test names is not triage.

## Steps

1. **Get the run.** If you have a `run_id`, use it. If the user said "the last
   run" or similar, call `provalab_list_runs(project)` and take the most recent.
   Confirm which run you are looking at before analysing it — triaging the wrong
   run is worse than asking.

2. **Fetch the real results.** Call `provalab_get_results(run_id)`. If the server
   offers `provalab_triage(run_id)`, call that too — it may already group
   failures by cause.

   **Read the actual errors.** Do not infer a cause from a test's name. A test
   called `test_login_redirects` failing tells you nothing about why.

3. **Group by cause, not by test.** Twenty tests failing on one broken selector
   is one problem, not twenty. Lead with the grouping — it is usually the single
   most useful thing you can say.

4. **Separate real failures from infrastructure noise.** These need different
   responses and conflating them sends the user down the wrong path:
   - **Assertion failures** — the app behaved differently than expected. Likely a
     real regression.
   - **Errors, timeouts, connection refused** — the test could not run. Often
     environment, not code.
   - **Skipped tests** — did not run at all. Worth flagging, because a suite that
     skips half its tests can look green while proving nothing.

5. **Say what to do next**, concretely. Point at the file or the change most
   likely responsible. If you genuinely cannot tell from the results, say that
   and name what would settle it — a log, a re-run, a screenshot.

## Honesty rules

- Quote real error text. Never paraphrase an error you have not read.
- If a failure's cause is ambiguous, say it is ambiguous. A confident wrong
  diagnosis costs more than an honest "I can't tell yet from this output",
  because the user acts on it.
- If the whole run errored rather than failed, lead with that. The suite did not
  find bugs; it did not get to look.
