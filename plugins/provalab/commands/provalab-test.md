---
description: Start a ProvaLab test run for a project, optionally narrowed to a target suite or feature.
argument-hint: <project> [target]
---

Start a ProvaLab test run.

- Project: `$1`
- Target (optional — a suite, tag, file, or feature area): `$2`
- Full arguments as given: `$ARGUMENTS`

Do this:

1. If `$1` is empty, call `provalab_list_projects` and ask which project to use. Do not guess.
2. Call `provalab_run_tests` with that project, and with `$2` as the target if one was given. Omit the target to run everything.
3. Report the returned `run_id` immediately, so the user can come back to it later.
4. Poll `provalab_get_run(run_id)` every 15–30 seconds until it is no longer running. Say what you are waiting on between polls.
5. Summarise the outcome with real counts. If anything failed, call `provalab_get_results(run_id)` and quote the actual errors — never describe a failure you have not read.

Runs take minutes. Never block, and never report a result you have not fetched.
