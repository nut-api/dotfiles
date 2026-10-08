---
name: weekly-summary
description: Use when user asks for a weekly work summary or wants to summarize what they did this week. Reads the weekly work-log from ~/.claude/work-log/ and compiles into boss-ready weekly update email.
---

# Weekly Summary Skill

## Purpose

Compile a weekly work summary for Nut to send to his boss every week. Source of truth is the weekly log file — not git log.

## Work-log format

One file per week: `~/.claude/work-log/YYYY-Www.md` (e.g. `2026-W18.md`).

Each session that involved real work adds an entry:

```markdown
## YYYY-MM-DD | <project/repo name>
- <bullet: what was built/fixed/changed — key technical detail>
- <bullet: status — merged / in-progress / hotfixed>
```

Keep each bullet under 20 words. Edit existing entries if a later session updates earlier work — don't duplicate.

## Auto-save after real work

At the end of any session where real work happened, append or update `~/.claude/work-log/YYYY-Www.md` without being asked.

**Real work** = feature built, migration done, bug fixed, infra changed, PR merged, config updated.
**Not real work** = questions answered, code explained, lookups, reading files only, version bumps, chart releases, renaming files, minor housekeeping with no functional impact.

If nothing was built or changed — do not write to the log.

**Filter before logging:** Only log work that would be worth mentioning to a manager. Skip anything that is purely mechanical, administrative, or a side-effect of other work (e.g. bumping chart version to trigger release, renaming a file, removing stale config).

## Writing the weekly summary

When user asks for weekly summary:

1. Read `~/.claude/work-log/YYYY-Www.md` for the current week
2. Split entries into: completed work vs. still-in-progress work
3. Write in this exact format:

```
Subject: [infra] weekly update | YYYY-MM-DD

Infrastructure — Weekly Progress

*Context: <1–2 sentences, plain language: what the project is and what this week's work was about>*

**What We Accomplished**
- **<short plain-language label>:** <what the problem was / what changed, and why it matters>. <one proof point: number, test result>.
- **<short plain-language label>:** <what the problem was / what changed, and why it matters>. <one proof point: number, test result>.

**In Progress**
- **<short plain-language label>:** <what it is and why, current status, what remains>.
- **<short plain-language label>:** <what it is and why, current status, what remains>.
```

Rules:
- Write for a reader with **no background** on the project. Boss is engineering-savvy in general but has not followed the details of this work.
- Always include the italic Context line so bullets make sense without prior knowledge. Skip it only if the same project ran the previous weeks and boss already has the context.
- Each bullet leads with a bold plain-language label (what it is), then problem → change → why it matters. Say what was wrong before saying what was fixed.
- Avoid internal jargon, tool names, and code identifiers (e.g. describe "compaction" as "the routine that merges old backup files", "SIGTERM" as "the shutdown request"). If a term is unavoidable, explain it in a few words inline.
- Keep the technical proof, but as a plain result ("0 lost writes across 4 tests", "30s → 1–3s"), not as implementation detail.
- Each bullet 1–3 short sentences max, no padding
- Group related sub-items under one bullet (don't list every sub-task)
- Date in subject = today's date
