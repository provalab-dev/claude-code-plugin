---
name: triage-failures
description: Use when tests failed and the user wants to know why — "why did the run fail", "what broke", "triage these failures", "explain the errors", or when a completed run reported failures and the user asks what to do next.
---

# Triaging a failed ProvaLab run

The goal is to tell the user what actually broke and what to do about it. A list of
red test names is not triage.

## Steps

1. **Get the run.** Use the TMS test run id if you have one. For "the last run",
   call `tms_list_test_runs(project_id)` and take the newest. Confirm which run you
   are looking at before analysing it. Triaging the wrong run is worse than asking.

2. **Fetch the real failures.** Call `tms_get_test_run_failures(run_id)`. It returns
   every failed result with its first console error and stack trace. If you have the
   execution id from `execute_pytest`, `get_execution_result(execution_id)` gives the
   full pytest report including stdout and stderr. For UI tests,
   `get_session_artifacts(session_id)` gives screenshots, video and console logs.

   **Read the actual errors.** Do not infer a cause from a test's name.

3. **Group by cause, not by test.** Twenty tests failing on one broken selector is
   one problem, not twenty. `tms_get_similar_failures(result_id)` shows where the
   same error signature appears elsewhere. Lead with the grouping.

4. **Separate real failures from infrastructure noise.**
   - **Assertion failures**: the app behaved differently than expected. Likely a
     real regression.
   - **Errors, timeouts, connection refused**: the test could not run. Often
     environment, not code.
   - **Skipped tests**: did not run at all. Worth flagging, because a suite that
     skips half its tests can look green while proving nothing.

5. **Record what you concluded**, if the user agrees, with
   `tms_classify_failure(result_id, category)` (`env`, `flaky`, `product-bug`,
   `test-bug`, `data` or `unknown`), so the conclusion survives this chat.

6. **Say what to do next**, concretely. Point at the file or change most likely
   responsible. If you cannot tell from the results, say so and name what would
   settle it: a log, a re-run, a screenshot.

## Honesty rules

- Quote real error text. Never paraphrase an error you have not read.
- If a cause is ambiguous, say it is ambiguous. A confident wrong diagnosis costs
  more than an honest "I can't tell yet", because the user acts on it.
- If the whole run errored rather than failed, lead with that. The suite did not
  find bugs; it did not get to look.
