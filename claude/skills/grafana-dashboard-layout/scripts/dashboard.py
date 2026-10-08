#!/usr/bin/env python3
"""Grafana dashboard layout tooling: get / put / inspect / verify.

Works on plain dashboard JSON and on dashboards embedded in a Kubernetes
ConfigMap YAML (the grafana sidecar pattern). `get`/`put` round-trip the
embedded JSON without disturbing the surrounding YAML or its comments.

Usage:
  dashboard.py get     <dash.yaml|dash.json> [-o out.json]
  dashboard.py put     <dash.yaml|dash.json> <edited.json>
  dashboard.py inspect <dash.yaml|dash.json>
  dashboard.py verify  <before.yaml|json> <after.yaml|json> [--allow-dropped ID,ID]
"""
import argparse
import json
import re
import sys

BLOCK_RE = re.compile(r"^(?P<indent>[ \t]*)(?P<key>[\w.\-]+):[ \t]*\|-?[ \t]*$")
SCREEN_UNITS = 25  # roughly one 1080p viewport of Grafana grid rows


# ---------------------------------------------------------------- load / save


def _find_block(text):
    """Locate an embedded JSON block scalar in a ConfigMap YAML.

    Returns (start_line, end_line, body_indent) or None for plain JSON.
    """
    lines = text.split("\n")
    for i, line in enumerate(lines):
        m = BLOCK_RE.match(line)
        if not m:
            continue
        body_indent = None
        j, last = i + 1, i
        while j < len(lines):
            cur = lines[j]
            if cur.strip() == "":
                j += 1
                continue
            indent = len(cur) - len(cur.lstrip())
            if indent <= len(m.group("indent")):
                break
            if body_indent is None:
                body_indent = indent
                if cur.lstrip()[:1] != "{":
                    break  # block scalar, but not JSON
            last = j
            j += 1
        if body_indent is not None and lines[i + 1].lstrip()[:1] == "{":
            # end just past the last non-blank line, so a trailing newline or
            # blank line after the block survives the round-trip
            return i, last + 1, body_indent
    return None


def load(path):
    """Return (dashboard_dict, context) where context is used by save()."""
    text = open(path).read()
    stripped = text.lstrip()
    if stripped.startswith("{"):
        return json.loads(text), {"kind": "json", "path": path}
    blk = _find_block(text)
    if not blk:
        sys.exit(f"{path}: no dashboard JSON found (not JSON, no JSON block scalar)")
    start, end, indent = blk
    lines = text.split("\n")
    body = "\n".join(l[indent:] if len(l) >= indent else l for l in lines[start + 1:end])
    return json.loads(body), {
        "kind": "yaml", "path": path, "text": text,
        "start": start, "end": end, "indent": indent,
    }


def save(db, ctx, path=None):
    out = path or ctx["path"]
    body = json.dumps(db, indent=2, ensure_ascii=False)
    if ctx["kind"] == "json":
        open(out, "w").write(body + "\n")
        return
    pad = " " * ctx["indent"]
    block = [pad + l if l else "" for l in body.split("\n")]
    lines = ctx["text"].split("\n")
    new = lines[:ctx["start"] + 1] + block + lines[ctx["end"]:]
    open(out, "w").write("\n".join(new))


# ---------------------------------------------------------------- traversal


def walk(db):
    """Yield (panel, parent_row_or_None) for every panel in the dashboard."""
    for p in db.get("panels", []):
        yield p, None
        for c in p.get("panels", []) or []:
            yield c, p


def by_id(db):
    out = {}
    for p, _ in walk(db):
        pid = p.get("id")
        if pid in out:
            print(f"warning: duplicate panel id {pid}", file=sys.stderr)
        out[pid] = p
    return out


def groups(db):
    """Coordinate spaces that must each be overlap-free.

    Top-level = rows plus the children of expanded rows (siblings in one grid).
    Each collapsed row's nested children form their own space.
    """
    yield "top-level", [p for p in db.get("panels", [])]
    for p in db.get("panels", []):
        if p.get("type") == "row" and p.get("panels"):
            yield f"row {p.get('id')} ({p.get('title')})", p["panels"]


def overlaps(panels):
    cells, bad = {}, []
    for p in panels:
        g = p.get("gridPos", {})
        for y in range(g.get("y", 0), g.get("y", 0) + g.get("h", 0)):
            for x in range(g.get("x", 0), g.get("x", 0) + g.get("w", 0)):
                if (x, y) in cells:
                    bad.append((p.get("id"), cells[(x, y)], x, y))
                cells[(x, y)] = p.get("id")
    return bad


def schema_problems(db):
    """Collapsed rows must nest children; expanded rows must not."""
    out = []
    for p in db.get("panels", []):
        if p.get("type") != "row":
            continue
        n = len(p.get("panels") or [])
        if p.get("collapsed") and n == 0:
            out.append(f"row {p['id']} ({p.get('title')}) is collapsed but nests no panels "
                       f"- its children are stranded at top level and render as orphans")
        if not p.get("collapsed") and n > 0:
            out.append(f"row {p['id']} ({p.get('title')}) is expanded but nests {n} panels "
                       f"- they will be hidden")
    return out


# ---------------------------------------------------------------- commands


def cmd_get(args):
    db, ctx = load(args.file)
    body = json.dumps(db, indent=2, ensure_ascii=False)
    if args.out:
        open(args.out, "w").write(body + "\n")
        print(f"wrote {args.out}")
    else:
        print(body)


def cmd_put(args):
    _, ctx = load(args.file)
    db = json.load(open(args.json))
    save(db, ctx)
    print(f"updated {args.file}")


def cmd_inspect(args):
    db, _ = load(args.file)
    print(f"{db.get('title','<untitled>')}  (uid={db.get('uid')})\n")
    height = 0
    for p in db.get("panels", []):
        g = p.get("gridPos", {})
        height = max(height, g.get("y", 0) + g.get("h", 0))
        if p.get("type") == "row":
            state = "collapsed" if p.get("collapsed") else "expanded"
            print(f"ROW y={g.get('y'):>3} [{state:<9}] {p.get('title')}")
            for c in p.get("panels") or []:
                cg = c.get("gridPos", {})
                print(f"   . {c.get('type','?'):<11} y={cg.get('y'):>3} x={cg.get('x'):>2} "
                      f"w={cg.get('w'):>2} h={cg.get('h'):>2} id={c.get('id'):<3} {c.get('title')}")
        else:
            print(f"  {p.get('type','?'):<11} y={g.get('y'):>3} x={g.get('x'):>2} "
                  f"w={g.get('w'):>2} h={g.get('h'):>2} id={p.get('id'):<3} {p.get('title')}")

    print("\n-- layout notes --")
    rows = [p for p in db.get("panels", []) if p.get("type") == "row"]
    expanded = [r for r in rows if not r.get("collapsed")]
    print(f"rows: {len(rows)} ({len(expanded)} expanded), panels: {len(by_id(db))}, "
          f"visible height: {height} units (~{height / SCREEN_UNITS:.1f} screens)")
    if height > 4 * SCREEN_UNITS and len(expanded) == len(rows) and len(rows) > 3:
        print("! every row is expanded and the dashboard is long - collapse the "
              "drill-down rows so the top answers the first question without scrolling")
    ys = [r.get("gridPos", {}).get("y", 0) for r in rows]
    if ys != sorted(ys):
        print("! row y positions are not monotonic - row order will not match the JSON order")
    for problem in schema_problems(db):
        print(f"! {problem}")
    for label, panels in groups(db):
        bad = overlaps(panels)
        if bad:
            print(f"! overlapping panels in {label}: {bad[:5]}")


def cmd_verify(args):
    old, _ = load(args.before)
    new, _ = load(args.after)
    fo, fn = by_id(old), by_id(new)
    allowed = {int(x) for x in args.allow_dropped.split(",") if x.strip()} if args.allow_dropped else set()

    fail = []
    dropped, added = set(fo) - set(fn), set(fn) - set(fo)
    if dropped - allowed:
        fail.append(f"panels lost: {sorted(dropped - allowed)}")
    if dropped & allowed:
        print(f"ok: dropped as allowed: {sorted(dropped & allowed)}")
    if added:
        print(f"note: panels added: {sorted(added)}")

    if not args.allow_content:
        drift = []
        for pid in sorted(set(fo) & set(fn)):
            for field in ("title", "targets", "fieldConfig", "options", "transformations"):
                a = json.dumps(fo[pid].get(field), sort_keys=True)
                b = json.dumps(fn[pid].get(field), sort_keys=True)
                if a != b:
                    drift.append(f"panel {pid} ({fn[pid].get('title')}): {field}")
        if drift:
            fail.append("content changed in a layout-only edit:\n    " + "\n    ".join(drift))

    for label, panels in groups(new):
        bad = overlaps(panels)
        if bad:
            fail.append(f"overlapping panels in {label}: {bad[:5]}")

    fail += schema_problems(new)

    if fail:
        print("FAIL")
        for f in fail:
            print(f"  - {f}")
        sys.exit(1)
    print(f"PASS: {len(fn)} panels, no overlaps, schema consistent"
          + ("" if args.allow_content else ", no query/threshold drift"))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("get", help="extract dashboard JSON")
    g.add_argument("file")
    g.add_argument("-o", "--out")
    g.set_defaults(func=cmd_get)

    p = sub.add_parser("put", help="write JSON back, preserving surrounding YAML")
    p.add_argument("file")
    p.add_argument("json")
    p.set_defaults(func=cmd_put)

    i = sub.add_parser("inspect", help="print the row/panel tree and layout notes")
    i.add_argument("file")
    i.set_defaults(func=cmd_inspect)

    v = sub.add_parser("verify", help="compare before/after for a safe layout edit")
    v.add_argument("before")
    v.add_argument("after")
    v.add_argument("--allow-dropped", help="comma-separated panel ids intentionally removed")
    v.add_argument("--allow-content", action="store_true",
                   help="permit query/title/threshold changes (not a layout-only edit)")
    v.set_defaults(func=cmd_verify)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
