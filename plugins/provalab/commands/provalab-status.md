---
description: Check the status of a ProvaLab run — a specific run_id, or the most recent run if none is given.
argument-hint: "[run_id]"
---

Check ProvaLab run status.

- Run ID (optional): `$1`

Do this:

1. If `$1` was given, call `provalab_get_run($1)`.
2. If not, find the most recent run: use the run you started earlier in this conversation if there is one, otherwise call `provalab_list_runs` (calling `provalab_list_projects` first if you have no project context) and take the latest.
3. Say which run you are reporting on, then answer directly: still running (with elapsed time), passed, or failed with counts.

Keep it short. If it is still running, ask whether to wait rather than silently polling. If it finished with failures, offer to triage rather than launching into an explanation.

Do not start a new run — this command only reads.
