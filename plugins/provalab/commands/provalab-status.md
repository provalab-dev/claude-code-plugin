---
description: Show the status of a recorded ProvaLab test run — a specific TMS run id, or the most recent run if none is given.
argument-hint: "[test_run_id]"
---

Check ProvaLab run status.

- TMS test run id (optional): `$1`

Do this:

1. If `$1` was given, call `tms_get_test_run_results(test_run_id=$1)`.
2. If not, use the run recorded earlier in this conversation if there is one. Otherwise call `tms_list_test_runs` for the project (call `tms_list_projects` first if you have no project context) and take the newest run.
3. Say which run you are reporting on, then answer directly: its status, and passed / failed / skipped counts.

Runs started from this plugin are synchronous, so there is nothing to poll for them. A run in `running` state was started elsewhere, for example from CI. Report it as running and ask whether to check again later rather than polling.

Do not start a new run. This command only reads.
