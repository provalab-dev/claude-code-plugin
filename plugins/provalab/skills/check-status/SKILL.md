---
name: check-status
description: Use for quick ProvaLab lookups that do not start anything — "how's my run", "is it done yet", "what was the last run", "did the nightly pass", "list my recent runs", "what projects do I have". Read-only status checks.
---

# Checking ProvaLab status

Fast, read-only answers. This skill never starts a run — if the user actually
wants tests executed, use `run-tests` instead.

## Steps

1. **Work out which run they mean.**
   - An explicit `run_id` → use it.
   - "My run", "it", "the current one" → the run you started earlier in this
     conversation, if there is one.
   - "The last run", "the nightly" → `provalab_list_runs(project)`, take the most
     recent match.
   - No project context at all → `provalab_list_projects()` first.

2. **Call `provalab_get_run(run_id)`** and answer directly.

3. **Answer the question that was asked.** "Is it done?" wants "yes, passed" or
   "no, still running, about 4 minutes in" — not a full report. Offer the detail;
   do not lead with it.

## If the run is still going

Give the status and how long it has been running. Then ask whether to wait rather
than silently entering a poll loop — the user asked a question, not for a babysitter.

If they do want you to wait, switch to the `run-tests` polling discipline: poll
every 15–30 seconds, say what you are waiting on, and never report a result you
have not fetched.

## If it finished and failed

Say so, with the counts, and offer to triage. Do not start explaining failures
unprompted — that is `triage-failures`, and it costs another API call the user
may not want yet.
