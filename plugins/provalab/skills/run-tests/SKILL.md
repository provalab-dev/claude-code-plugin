---
name: run-tests
description: Use when the user asks to run tests, kick off a test run, execute a suite, or verify a feature works in ProvaLab — including phrasings like "run the login tests", "test the checkout flow", "run the regression suite for X". Covers choosing the tests, running them, and reporting the result.
---

# Running a ProvaLab test suite

`execute_pytest` is **synchronous**. It runs the suite and returns the full result
when the suite has finished. There is no `run_id` to poll and no "running" state to
wait on. One call records one TMS test run, so a suite is always run in one call.
**Never claim a result that is not in the response you got back.**

## Steps

1. **Resolve the project.** If the user named one, call `tms_list_projects` with
   `search` and take the exact match. If they did not, list projects and pick the
   match. If two or more plausibly match, ask rather than guess. Running the wrong
   suite wastes minutes and can hit real environments.

2. **Choose the tests.** Call `list_workspace_files`, and for UI suites
   `get_ui_test_inventory(domain)`. Select the files that match what the user asked
   for, plus the `conftest.py` files they depend on. Tell the user what you are
   about to run before you run it.

3. **Run them once.** Call `execute_pytest` with:
   - `workspace_paths`: the files you selected (or `files` with content for tests
     that are not in the workspace yet).
   - `organization_id` and `project_id`, so results are recorded in TMS. Pass them
     explicitly; do not rely on a session default.
   - `timeout_s` sized for the whole suite (roughly 120 s per UI test).
   - `base_url` only if the user gave one, and `test_plan_id` only if they named a
     plan. Do not invent other options.

4. **Summarise honestly from the response.**
   - Lead with the outcome: passed, failed or errored, with counts.
   - Name the failing tests and quote their real error text from the result.
   - Give the TMS run the call recorded, so the user can find it later.

## When something goes wrong

- If the call itself errors or times out, report that. An infrastructure failure is
  not a test failure, and conflating them sends the user debugging the wrong thing.
- If the user wants the detail of an earlier run, use `get_execution_result
  (execution_id)` when you have the execution id, or `tms_get_test_run_results
  (test_run_id)` from the TMS side.

## What not to do

- Do not split one suite into several `execute_pytest` calls, and do not use
  `test_filter` to batch tests. Each call creates a separate TMS run. `test_filter`
  is only for re-running a single failing test while debugging.
- Do not re-run a suite to "check" a result you can fetch.
