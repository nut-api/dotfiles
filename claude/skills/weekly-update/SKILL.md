---
name: weekly-update
description: Use when user calls /weekly-update. Reads this week's git commits from the current project and appends or updates the weekly work-log file.
---

# Weekly Update Skill

## Purpose

Pull real work from git history for the current project this week and write it into the weekly work-log at `~/.claude/work-log/YYYY-Www.md`. Also capture unstaged/uncommitted work as in-progress.

## Steps

1. **Get current week bounds**
   - Today's date → ISO week number → `YYYY-Www`
   - Week start = Monday of this week, week end = Sunday

2. **Read git log for this week**
   ```bash
   git log --since="YYYY-MM-DD 00:00" --until="YYYY-MM-DD 23:59" --oneline --all
   ```
   Use actual Monday and Sunday dates.

3. **For each commit, inspect the diff**
   ```bash
   git show --stat <sha>
   git show <sha> -- <key files>
   ```
   Understand what changed and why. Group related commits into one logical entry.

4. **Filter — only log real work**
   Real work = feature built, bug fixed, infra changed, behavior changed, PR created/merged.
   Skip: bot commits (`apiplus-bot`), auto-sync commits, trivial renames with no functional impact, pure version bumps with no logic change.

5. **Determine worklog file**
   File: `~/.claude/work-log/YYYY-Www.md`
   - If file exists: check if date section for today/this-week already present → update it, do not duplicate
   - If file does not exist: create with header `# Work log — YYYY-Www (Mon DD – Sun DD)`

6. **Write commit entries in this format**
   ```markdown
   ## YYYY-MM-DD | <repo/project name>

   ### <short title of what was done>
   - bullet: key technical detail (what changed, why, how)
   - bullet: status or impact
   ```
   Group commits by date. Keep bullets under 20 words. Use the repo directory name as the project name.

7. **Check for in-progress work (unstaged/staged changes)**

   ```bash
   git status --short
   ```

   If dirty files exist (skip noise: `.DS_Store`, lock files, build artifacts, `.env*`):

   **On re-run — check if previously in-progress items are done:**
   - Read existing `## In Progress` section, find this project's subsection
   - For each file listed there: check `git status --short` — if file is now clean, check `git log` this week
     - Committed → already in commit section → **remove** from in-progress
     - Discarded → **remove** silently
     - Still dirty → **keep** existing entry as-is (preserve manual edits)

   **Write in-progress summary** using current session context (you know what the work is about):
   ```markdown
   ## In Progress

   ### <repo/project name>
   - <summary of what is being worked on — inferred from session context and dirty file list>
   ```

   - Section lives at end of work-log file, organized by project subsection
   - Each run only modifies this project's subsection; other projects left untouched
   - Remove this project's subsection if no dirty files remain after reconciliation

8. **Confirm** — tell user what was logged, what was skipped (and why), and what is marked in-progress.

## Rules

- Do not log the same commit entry twice — check existing file content before appending.
- Merge related commits into one logical entry rather than one entry per commit.
- Use technical specifics: tool names, file paths (short), behavior change, pattern used.
- Only include work worth mentioning to a manager.
- In-progress entries persist across runs — preserve user edits on still-dirty files.
- In-progress entries are removed automatically when underlying files are committed or discarded.
