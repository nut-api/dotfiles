---
name: revert-before-retry-debug
description: Use when debugging misconfiguration, unexpected behavior, or system errors and about to try a different fix after one didn't work
---

# Revert Before Retry Debug

## Overview

Each debug attempt is a clean, isolated experiment. If a change doesn't solve the problem, revert it completely before trying the next approach. Never stack unverified changes.

## When to Use

Any time you're debugging and a change didn't fix the issue — configs, templates, environment settings, parameters, code.

**Do NOT skip this when:**
- The change "might still be useful later"
- The change is "harmless"
- You're "almost sure the next fix will work"

## Core Pattern

```
1. Apply ONE change
2. Test
3. If solved → done
4. If NOT solved → REVERT the change fully, restore previous state
5. Then try next approach
```

Never go to step 5 without completing step 4.

## Why

Accumulated failed changes:
- Pollute the codebase with noise (things that do nothing)
- Make root cause harder to isolate
- Create false impressions that something is doing work when it isn't
- Lead to shipping dead config that confuses future readers

**Real example:** During a Crunchy→CNPG migration debug, `hba_file: "pg_hba.conf"` was added to Patroni config (didn't work — Patroni resolves to absolute path anyway) and `pg_hba` entries were added to CNPG spec (redundant — CNPG adds defaults). Neither was reverted when they failed to solve the issue. Both ended up shipping as dead config until explicitly audited.

## Red Flags — Stop and Revert

- "This change might still be useful even if it didn't fix this"
- "It's harmless to keep it"
- "I'll clean it up later"
- "Let me just add one more thing on top"

All of these mean: **revert the failed change first.**

## Common Mistakes

| Mistake | Fix |
|---|---|
| Keeping failed change "for reference" | Delete it. Git history has it if needed. |
| Stacking changes until something works | Isolate — one change, test, revert if fail |
| "Harmless" leftover config | Dead config = noise. Remove it. |
| Fixing and moving on without checking for leftovers | After solving, audit for accumulated dead changes |
