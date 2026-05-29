---
name: helm-chart-functional-testing
description: Use when writing functional tests for a Helm chart to verify deployed services work correctly. Apply when a chart wires multiple services together and config changes could silently break the pipeline.
---

# Helm Chart Functional Testing

## Philosophy

Test each service in the pipeline independently, in order. Each step must pass before moving to the next. The final step confirms the full end-to-end flow.

This catches exactly which service broke when a config change is made.

## Test Shape

One script per chart. Steps follow the data flow of the system — same order data travels through the architecture.

```
Step 1: Service A accepts input
Step 2: Service B receives from A
Step 3: Service C receives from B
...
Step N: All engines return correct data
```

Each step:
- Does one thing (register, produce, query, validate)
- Logs clearly what it's testing
- Fails immediately with a clear message if it breaks
- Only passes if the real service responded correctly

## Step Design

**Register / Setup** — verify the service accepts configuration (schema, connector, topic). Confirms service is up and API works.

**Produce / Ingest** — send known data into the entry point. Verify the service confirmed receipt (offset, ack, count).

**Poll for output** — wait for downstream service to process. Poll on interval with timeout. Confirms data moved between services.

**Query** — ask each query engine for a count. Must equal exact number produced. Confirms data reached that engine intact.

**Validate record identity** — produce one record with known values. Query it by a fixed field in every engine. Compare `id` + timestamp exactly. Confirms no corruption or data loss.

## Validation Levels

| Level | What it proves |
|---|---|
| Count matches | No data was dropped in transit |
| Record identity matches | No corruption, correct deserialization |
| Same result across engines | Both engines read from the same source correctly |

Always validate record identity — count alone does not catch corruption.

## Cleanup

Every resource created by the test must be deleted after, even on failure. Test each delete separately so one failure doesn't skip others. Log a warning when a cleanup step fails, don't abort.

## When a Step Fails

The failing step tells you which service broke. Check only that service — no need to debug the rest of the pipeline.

Example: if step 4 (poll for parquet files) times out after a connector config change, the Iceberg sink connector is misconfigured. Steps 1–3 already confirmed Kafka and Schema Registry are fine.

## Makefile target

Expose as `make smoke` so anyone can run it with one command. Accept `--namespace` arg for non-default deployments.

## Anti-patterns

- Testing only "did it start" — misses silent data loss
- Mocking services — hides the integration failures that actually happen in prod
- Skipping record identity check — count match does not prove correct data
- Single cleanup block — one failure skips all remaining cleanup
- Hardcoding resource names — breaks between runs; generate unique names per run (uid suffix)
