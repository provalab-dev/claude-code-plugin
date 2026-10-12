---
name: run-tests
description: Use when the user asks to run tests, kick off a test run, execute a suite, or verify a feature works in ProvaLab — including phrasings like "run the login tests", "test the checkout flow", "run the regression suite for X". Covers starting a run and following it to completion.
---

# Running a ProvaLab test suite

Test runs take minutes. The server is async by design: starting a run returns
immediately with a `run_id`, and you poll for completion. **Never block waiting
for a run to finish, and never claim a result you have not fetched.**

## Steps

1. **Resolve the project.** If the user named one, use it. If they did not, call
   `provalab_list_projects` and pick the match. If two or more plausibly match,
   ask rather than guessing — running the wrong suite wastes minutes and can hit
   real environments.

2. **Start the run.** Call `provalab_run_tests(project, target, options)`.
   - `target` narrows what runs — a suite name, a tag, a file, or a feature area
     like `login`. Omit it to run everything for the project.
   - Pass `options` only when the user asked for something specific (browser,
     environment, parallelism). Do not invent options.
   - Expect `{ run_id, status: "running" }` back. Tell the user the run started
     and give them the `run_id`.

3. **Poll `provalab_get_run(run_id)` until it is no longer running.** Space the
   polls out — every 15–30 seconds is plenty. Between polls, say what you are
   waiting on rather than going silent.

4. **Summarise honestly when it finishes.**
   - Lead with the outcome: passed, failed, or errored, with counts.
   - If anything failed, name the failing tests. Do not paraphrase a failure you
     have not read — call `provalab_get_results(run_id)` and quote the real error.
   - Include the run link if the server returned one.

## Handling long or stuck runs

If a run is still `running` after several polls, say so plainly with the elapsed
time and let the user decide whether to keep waiting. Do not silently keep
polling forever, and do not report a partial result as if it were final.

If a poll fails or the run enters an error state, report that — an infrastructure
failure is not a test failure, and conflating them sends the user debugging the
wrong thing.

## What not to do

- Do not summarise results from the `provalab_run_tests` response. It only tells
  you the run started.
- Do not describe a run as passing because it has not failed yet.
- Do not re-run a suite to "check" a result you could fetch with
  `provalab_get_results`.
