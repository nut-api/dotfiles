# Reference: dashboard layout rules and grid mechanics

## The ordering rules

| Rule | Why |
|---|---|
| Most important top-left | Users scan in a Z-pattern, left→right, top→bottom |
| General → specific, large → small | Grafana's own guidance: "create a logical progression of data" |
| Summary visible **without scrolling** | The top of the dashboard must answer the first question alone |
| Rows group related panels; row order reflects importance or data flow | Rows are functional containers, not arbitrary dividers |
| Collapse drill-down rows | Cuts cognitive load and scroll depth; the overview stays the default view |
| Bigger panel = more important | Size is read as emphasis, so size deliberately |
| RED for services, USE for infrastructure | Different question per layer — see below |

Sources: [Grafana best practices](https://grafana.com/docs/grafana/latest/dashboards/build-dashboards/best-practices/),
[Grafana Labs blog](https://grafana.com/blog/getting-started-with-grafana-best-practices-to-design-your-first-dashboard/),
[Sysdig golden signals](https://www.sysdig.com/blog/golden-signals-kubernetes).

## Choosing the row order

Order rows by *what someone opens the dashboard to find out*, most urgent first:

1. **Is the system healthy right now?** — summary stats, then live state
2. **Is work succeeding, and how fast?** — RED for the request/job pipeline
3. **Is the infrastructure saturated?** — USE for nodes and disks
4. **Are the dependencies healthy?** — caches, databases
5. **Backing stores and supporting services** — collapsed drill-down

A useful tiebreak: if a row's known failure mode has ever caused an incident, promote it.
Put the panel that would have caught the last incident where it cannot be missed.

## Ordering *inside* a row

**RED** — for request-driven services (APIs, job pipelines, gateways):

```
[ rate stat ] [ error stat ] [ success % ] [ latency p95 ]
[ throughput over time      ] [ duration over time       ]
[ errors breakdown          ] [ slowest breakdown        ]
```

Errors before latency before volume. A failure matters more than a slow success, which
matters more than a count.

**USE** — for resources (nodes, disks, CPU, memory):

```
[ utilization gauges ] [ saturation stats ] [ error/restart counts ]
[ saturation over time (queue depth, wait, pressure) ]
[ per-workload utilization ]
```

Lead with **saturation**, not utilization. Utilization looks fine right up until it
doesn't; saturation (queue depth, `w_await`, PSI, run-queue) is what actually degrades.
CPU graphs commonly look calm during an IO-bound incident.

## Grid mechanics

- The grid is **24 units wide**. Full width `w: 24`, half `w: 12`, sixth `w: 4`.
- `h` is in grid rows; roughly **25 units ≈ one 1080p viewport**. Over ~4 screens of
  expanded content, start collapsing rows.
- A row panel itself is always `h: 1, w: 24, x: 0`.
- `y` must be computed cumulatively. After a run of `h: 4` stats at `y=1`, the next band
  starts at `y=5`. Let a script do this arithmetic.
- A **collapsed** row occupies only its own 1 unit in the top-level flow — the next row
  sits at `y+1` regardless of how much it nests.
- Panel ids must be unique across the whole dashboard, nested ones included.

### The collapsed-row trap

This is the single most common way to corrupt a dashboard:

```jsonc
// collapsed: children NESTED inside the row
{ "type": "row", "collapsed": true,  "panels": [ {...}, {...} ] }

// expanded: children are SIBLINGS after the row, row's own array empty
{ "type": "row", "collapsed": false, "panels": [] },
{ "type": "timeseries", ... },
```

Mixing them up either strands children as always-visible orphans (collapsed row with an
empty array, children left at top level) or hides them entirely (expanded row that
nests). `dashboard.py verify` checks both directions.

## Worked example

A dashboard for a CI runner fleet that had grown to 7 expanded rows / ~171 units
(~7 screens), with the "what is running right now" table added last — at the very
bottom, below 8 charts for a supporting registry service.

Rearranged to 6 rows, 102 units, 4 expanded:

1. **Runner fleet** — 6 stat panels, then the running-jobs table **full width at `y=5`**,
   then capacity graphs. The "right now" answer moved from `y=162` to `y=5`.
2. **Jobs** — RED. Throughput | duration, then failures-by-workflow promoted above the
   slowest/busiest tables.
3. **Pods & node** — USE. Disk I/O and disk-saturation panels moved from last in the row
   to first: an IO-pressure incident was the node's known failure mode, and those were
   the panels that showed it while CPU looked fine.
4. **Cache server** — expanded; cache misses show up directly in job duration.
5. **Object storage** — collapsed drill-down.
6. **Container registries** — collapsed supporting service.

Verified as a pure layout change: 71/72 panels preserved (the one loss was an emptied row
wrapper, passed via `--allow-dropped`), zero drift in any `targets`/`fieldConfig`, no
overlaps.
