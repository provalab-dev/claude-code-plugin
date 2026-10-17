---
description: Run a ProvaLab test suite for a project, optionally narrowed to a target area, and report the results.
argument-hint: <project> [target]
---

Run ProvaLab tests.

- Project: `$1`
- Target (optional — a feature area, folder or file): `$2`
- Full arguments as given: `$ARGUMENTS`

Do this:

1. Resolve the project. Call `tms_list_projects` (pass `search` with `$1` if given) and take the exact match. If `$1` is empty or several projects match, ask which one. Do not guess.
2. Find the tests. Call `list_workspace_files`, and `get_ui_test_inventory(domain)` for UI suites. Pick the files that match `$2`, or the whole suite if no target was given. Include `conftest.py` files the tests depend on.
3. Tell the user which files you will run and in which project, then call `execute_pytest` **once** with `workspace_paths`, `organization_id`, `project_id`, and a `timeout_s` sized for the whole suite. Execution is synchronous: the call returns when the suite has finished, and one call records one TMS run.
4. Report from the returned result: passed, failed, errored and skipped counts, and the TMS run it recorded. If anything failed, quote the actual error text from the result. Never describe a failure you have not read.

Do not split a suite across several calls, and do not use `test_filter` to batch tests. Each call creates a separate TMS run.
