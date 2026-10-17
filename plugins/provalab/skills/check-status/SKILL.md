---
name: check-status
description: Use for quick ProvaLab lookups that do not start anything — "how did my run go", "what was the last run", "did the nightly pass", "list my recent runs", "what projects do I have". Read-only status checks.
---

# Checking ProvaLab status

Fast, read-only answers. This skill never starts a run. If the user actually wants
tests executed, use `run-tests` instead.

## Steps

1. **Work out which run they mean.**
   - An explicit TMS test run id → use it.
   - "My run", "it" → the run recorded earlier in this conversation, if any.
   - "The last run", "the nightly" → `tms_list_test_runs(project_id)`, take the
     newest match.
   - No project context at all → `tms_list_projects` first.

2. **Call `tms_get_test_run_results(test_run_id)`** and answer directly.

3. **Answer the question that was asked.** "Did it pass?" wants "yes, 42 passed" or
   "no, 3 of 45 failed", not a full report. Offer the detail; do not lead with it.

## If the run is still going

Runs started through `execute_pytest` finish before the call returns, so they are
never "running". A run in `running` state was started elsewhere, for example from
CI. Give its status and ask whether to check again later. Do not enter a polling
loop on your own.

## If it finished and failed

Say so, with the counts, and offer to triage. Do not start explaining failures
unprompted. That is `triage-failures`, and it costs more tool calls the user may
not want yet.
