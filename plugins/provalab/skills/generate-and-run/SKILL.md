---
name: generate-and-run
description: Use when the user wants tests created from something rather than run from an existing suite — a URL, a user story, a ticket, a feature description, or "write tests for this page". Covers generating tests in ProvaLab and then executing them.
---

# Generating tests, then running them

Two phases: generation, then a normal run. Generation is the part users are least
able to check by eye, so surface what was generated before it runs.

## Steps

1. **Resolve the project** the tests belong to. Call `provalab_list_projects` if
   the user did not name one. Generated tests have to live somewhere, so this is
   not optional.

2. **Call `provalab_generate_tests(url_or_story, project)`.**
   - Pass the URL verbatim if the user gave one.
   - Pass the user story or feature description as written. Do not rewrite it
     into what you think it should say — the generator's output quality depends
     on the user's actual wording, and silently editing it makes a bad result
     impossible to diagnose.

3. **Show the user what came back before running anything.** Generated tests are
   a draft, not a fact. List what was generated in a sentence or two so the user
   can spot a misunderstanding cheaply, now, rather than after a five-minute run
   against the wrong flow.

   If the response contains a `run_id`, generation and execution were combined
   server-side — skip to step 5.

4. **Run them.** Call `provalab_run_tests(project, target)` with the target
   scoped to what was just generated.

5. **Poll `provalab_get_run(run_id)`** until it finishes, then summarise. The
   `run-tests` skill covers the polling and reporting discipline; it applies
   unchanged here.

## Reading the first run of generated tests

A failure on the first run of freshly generated tests is ambiguous in a way an
established suite's failure is not. It means one of three things, and they need
different responses:

- **The test is wrong** — the generator misread the page or the story. Say so and
  offer to regenerate with a clearer description.
- **The app is genuinely broken** — the test found a real bug. This is the
  valuable case.
- **The test is flaky or environment-dependent** — a timing or setup problem.

Call `provalab_get_results(run_id)` and read the actual error before deciding
which. Guessing here is worse than saying you cannot tell yet, because a user who
is told "we found a bug" and finds a broken test will stop trusting generated
tests entirely.
