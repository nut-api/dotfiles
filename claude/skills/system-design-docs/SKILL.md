---
name: system-design-docs
description: Use when writing or updating system design documentation — architecture READMEs, service overviews, stack descriptions, or any doc that explains what components do and why they were chosen.
---

# System Design Docs

## Style

Each component section follows this order:

1. **What** — one sentence: what it is and its role in the system
2. **Why** — one compact sentence: the key reason this tool was chosen over alternatives
3. **Detail** — bullet points for specifics (endpoints, config, credentials)

## Format Rationale

When a file format (Avro, Parquet, Protobuf, etc.) is first mentioned, add a one-line explanation focused on row vs column storage model:

- **Row-based** (Avro, CSV): write one record at a time — efficient for streaming and inserts
- **Columnar** (Parquet, ORC): store values by column — analytical queries read only needed columns

Add this at the point of first mention, as plain prose inline with the surrounding text.

## Rules

- "Why" is one sentence only — the main benefit, not a paragraph
- No blockquotes — plain prose
- No bold "Why:" label — blend naturally into the description
- Format rationale at first mention only, not repeated

## Example

```markdown
### Kafka Connect (`kafka-connect` service — port 8083)

Runs the Iceberg Sink Connector plugin. No custom consumer code — connector handles offsets, Parquet writes, and Nessie registration. Reads Avro messages from Kafka topics, converts them to Parquet columns, writes files to S3, and registers/updates the table in Nessie — all automatically.

Parquet is a columnar format — stores values by column not row, so analytical queries read only the columns they need.
```

## Anti-patterns

- Long "Why" paragraphs → cut to one sentence, main benefit only
- Blockquote formatting for "Why" → plain prose
- Repeating format rationale → first mention only
- Separate "Why" heading → blend into description flow
