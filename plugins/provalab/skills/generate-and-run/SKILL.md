---
name: generate-and-run
description: Use when the user wants tests created from something rather than run from an existing suite — a URL, a user story, a ticket, a feature description, or "write tests for this page". Covers generating tests for ProvaLab and then executing them.
---

# Generating tests, then running them

Two phases: write the tests, then a normal run. Generated tests are the part users
are least able to check by eye, so show what you wrote before it runs.

## Steps

1. **Resolve the project** the tests belong to with `tms_list_projects`. Results
   have to be recorded somewhere, so this is not optional.

2. **Check what already exists.** Call `get_ui_test_inventory(domain)` and
   `list_workspace_files` before writing anything, so you extend the existing suite
   instead of writing a parallel copy of it.

3. **Understand the target.** For a URL, provision a browser with
   `provision_browser`, then use `crawl_site(session_id, start_url)` and
   `analyze_page(page_url)` on the pages that matter. For a user story or ticket,
   work from the user's wording as written. Do not rewrite it into what you think it
   should say.

4. **Write the tests and show them.** Generate pytest files, save them with
   `save_test_artifacts(files)`, and tell the user in a sentence or two what each
   test checks. A misunderstanding is cheap to catch now and expensive after a
   five-minute run against the wrong flow.

5. **Run them once** with `execute_pytest(files=..., organization_id, project_id,
   base_url, timeout_s)`, reusing the browser `session_id` if you provisioned one.
   The call is synchronous and returns the full result. The `run-tests` skill's
   reporting rules apply unchanged.

## Reading the first run of generated tests

A failure on the first run of freshly generated tests is ambiguous in a way an
established suite's failure is not. It means one of three things:

- **The test is wrong**: it misread the page or the story. Say so and offer to fix
  the test.
- **The app is genuinely broken**: the test found a real bug. This is the valuable
  case.
- **The test is flaky or environment-dependent**: a timing or setup problem.

Read the actual error in the result before deciding which. Saying you cannot tell
yet is better than guessing, because a user told "we found a bug" who then finds a
broken test will stop trusting generated tests.
