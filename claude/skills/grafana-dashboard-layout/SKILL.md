---
name: grafana-dashboard-layout
description: Audit and rearrange Grafana dashboards against established design conventions (most-important-first, RED/USE, collapsed drill-down rows), and edit them safely without losing panels or silently changing queries. Use when asked to reorganize, reorder, restructure, clean up, review, or improve the layout of a Grafana dashboard, when adding panels to an existing dashboard, or when working with dashboard JSON embedded in a Kubernetes ConfigMap for the Grafana sidecar.
---

# Grafana dashboard layout

Two jobs: decide the **right order**, then make the change **without breaking anything**.
Layout edits are dangerous because a dashboard is one big JSON blob — a careless edit
silently drops panels or rewrites a query, and nothing errors.

## Quick start

`scripts/dashboard.py` (stdlib only, no PyYAML) handles the deterministic parts.
It reads plain dashboard JSON *and* JSON embedded in a ConfigMap YAML.

```bash
S=scripts/dashboard.py
cp dash.yaml /tmp/dash.bak.yaml          # always keep a before-copy

python3 $S inspect dash.yaml             # row/panel tree + layout smells
python3 $S get dash.yaml -o dash.json    # extract JSON to edit
# ... rearrange dash.json with a script (see Workflow) ...
python3 $S put dash.yaml dash.json       # write back, YAML comments preserved
python3 $S verify /tmp/dash.bak.yaml dash.yaml   # must PASS before applying
```

`verify` fails on: panels lost, grid overlaps, collapsed/expanded row-nesting bugs, and
any drift in `title`/`targets`/`fieldConfig`/`options`/`transformations`. Flags:
`--allow-dropped 71,72` for intentional removals, `--allow-content` when the edit is not
layout-only.

## Workflow

1. **Back up**, then `inspect` to see the current tree and smells.
2. **Decide the order** using [REFERENCE.md](REFERENCE.md) — the ordering rules and the
   per-row internal ordering (RED for services, USE for infra).
3. **Rearrange with a script, never by hand.** Dashboards run to thousands of lines;
   hand-editing `gridPos` reliably produces overlaps. Write a throwaway Python script
   that loads the JSON, sets each panel's `gridPos` from an explicit layout, and asserts
   every original panel id was placed. Compute `y` per row; do not eyeball it.
4. **`put`, then `verify`** against the backup. Do not skip — this is the step that
   catches a dropped panel or a mangled query.
5. **Apply** (`kubectl apply -f` for the sidecar pattern) and say what moved and why.

## Non-negotiables

- **Never change a query while rearranging.** Layout and content are separate commits.
  A clean `verify` (no `--allow-content`) is the proof.
- **Collapsed rows nest their children; expanded rows do not.** In the Grafana schema a
  `collapsed: true` row carries its panels in its own `"panels"` array; an expanded row
  leaves them as siblings after it in the top-level array. Get it backwards and the
  children render as always-visible orphans, or vanish. `verify` checks this.
- **Preserve comments** in ConfigMap-wrapped dashboards — `get`/`put` round-trips
  byte-identically; a naive YAML load-and-dump destroys them.
- **Record the ordering rationale** in a comment at the top of the file, so the next
  edit does not undo it.

## Advanced

See [REFERENCE.md](REFERENCE.md) for the design rules and their sources, the
row-internal ordering patterns (RED / USE), grid mechanics, and a worked example.
