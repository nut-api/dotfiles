---
name: fast-pr
description: Create a GitHub issue from the current repo's .github/ISSUE_TEMPLATE forms, then branch and open a linked PR following .github/pull_request_template.md. Use when the user asks to open an issue and PR, "fast pr", "create issue and link pr", or wants already-made code changes turned into a proper issue+PR pair.
---

# Fast PR

Turns a chunk of work (already done, or about to be done) into: one issue matching this repo's issue-form template, a branch, and a PR that closes the issue and follows this repo's PR template. Always drafts and confirms before touching GitHub or git state.

## Quick start

1. Read `.github/ISSUE_TEMPLATE/*.yaml` (or `.yml`) and `.github/pull_request_template.md` from the repo root. If either is missing, say so and stop — don't invent a template.
2. Figure out what kind of work this is (bug / feature / chore / refactor / perf / whatever templates exist) — ask the user if it's not obvious from context.
3. Draft everything, present it, wait for explicit go-ahead.
4. On confirmation: create issue → branch → push → create PR.

## Reading the templates

Each YAML issue form typically has:
- `title`: a prefix pattern, e.g. `"[ENH] App Name: Issue Title / Short Description"` — reuse the bracket tag, replace the rest.
- `type` / `labels`: apply these to the created issue.
- `body`: a list of fields (`textarea`/`input`, some `required`). Map each required field to a markdown `###` header in the issue body — never leave a required field blank or templated.

For the PR template, keep its section structure verbatim (e.g. `## Related issues`, checklists, `## What's changed`) and fill it from the actual diff/work — don't leave placeholder text like "No change" if there is one.

## Branch naming

Default convention (use unless the repo's actual git history clearly uses something else — check `git branch -a` / recent merge commits first):

`{issue_type}-{issue_number}/{description}`

- `issue_type`: `bug`, `enh` (enhancement), `doc` (documentation), or whatever type the matched issue template declares (e.g. `chore`, `refactor`) if it doesn't fit those three.
- `description`: short, snake_case (underscores, not hyphens).
- Epic feature work: prefix with the epic's slug and a slash: `{epic_feature}/{issue_type}-{issue_number}/{description}`.

Examples:
- `bug-1234/fix_typo_in_readme`
- `enh-5678/add_pagination_to_results`
- `doc-9123/update_readme_with_setup_instructions`
- `epic_feature/bug-1234/fix_typo_in_readme`

Ask the user whether this work belongs under an epic before drafting the branch name; if yes, apply the epic prefix. The issue number is only known after the issue is created, so draft the branch name with a placeholder and finalize it after step 1 of the workflow below.

## Workflow

1. **Draft, don't execute.** Compose:
   - Issue title, labels, and body (per the template mapping above), grounded in the real change (diff, conversation context) — no generic filler.
   - Branch name (placeholder for the issue number).
   - PR title and body, following the repo's PR template exactly, with the close-linking syntax it specifies (usually `close #<issue-number>`).
2. **Present the full draft as plain text** — issue body, branch name, PR body — and stop. Do not call `gh`/git yet.
3. Wait for explicit confirmation. If the user wants changes, revise and re-present; don't proceed on silence or an ambiguous reply.
4. On confirmation, in order:
   - Create the issue (prefer `gh-axi issue create`, fall back to `gh issue create`) with the drafted title/labels/body → capture the issue number from the returned URL.
   - Finalize the branch name with the real issue number; `git branch -m` if renaming the current branch, or `git checkout -b` if starting fresh.
   - `git push -u origin <branch>`.
   - Create the PR (prefer `gh-axi pr create`, fall back to `gh pr create`) with the finalized body.
5. Report both URLs. Stop there — this skill does not merge, request reviewers, or push further.

## Rules

- Never auto-commit uncommitted changes to make the diff "complete" — if the working tree is dirty, ask first.
- A template's `projects:` field (issue forms) only applies via the GitHub web UI — `gh issue create` won't add the issue to a project board. Mention this as a manual follow-up rather than trying to script around it.
- If the task type doesn't cleanly match any available issue template, ask the user which to use instead of picking the closest guess.
- If the repo has no PR template, still confirm before creating anything, but drop the template-matching step for the PR body.
