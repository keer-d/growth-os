# Creator Discovery OS

Backend-only V1 implementation case for discovering and prioritizing synthetic
creator profiles for an AI website/portfolio builder campaign.

## What works

- Formal `RawCreatorProfile` contract with observed facts and provenance.
- Instagram and X profile URL normalization without overwriting source URLs.
- Same-platform, normalized-profile deduplication; no cross-platform merging.
- Deterministic activity, relevance, audience-size, market, actionability, and
  record-quality signals with human-readable evidence.
- Provider-agnostic audience inference plus an offline deterministic provider.
- Explainable `P1`, `P2`, `P3`, and `Needs Review` decisions without a 0–100 score.
- Run/query retrieval metrics and new-creator yield.
- Local SQLite persistence for creators, processing results, reviews, and feedback.
- One repeatable Controlled Demo using 12 fully synthetic retrieval records.

## Architecture and data flow

```text
Controlled JSON fixture
  -> Raw Creator Profile
  -> URL normalization + dedup
  -> observable signal extraction
  -> audience-only inference
  -> transparent priority decision
  -> SQLite system of record
  -> review + feedback storage
  -> run/query history
```

The layers remain separate:

1. **Facts** are public source values such as bio text, follower count, content,
   URLs, timestamps, query ID, and source connector.
2. **Signals** are deterministic interpretations of those facts, each with a
   reason and evidence.
3. **AI inference** is limited to likely audience, evidence, and confidence. The
   Controlled Demo uses a deterministic offline provider and no credential.
4. **Decision** assigns an explainable priority from the signals. It does not
   pretend to be a precise quality score.

## Run the Controlled Demo

Python 3.11 or newer is sufficient; the backend currently uses only the standard
library.

```bash
python3 -m pipeline.demo --reset
```

`--reset` removes only the selected local demo SQLite file so the documented
first-run result is repeatable. Without it, previously stored creators count as
existing duplicates, demonstrating saturation behavior.

Run the focused automated tests:

```bash
python3 -m unittest discover -v
```

## Local data

The default database is `data/controlled_demo.db` and is ignored by Git. Reviews
support `approve`, `reject`, and `needs_review`, with a structured reason and an
optional comment. Feedback is stored for later analysis only; it does not modify
queries, prompts, signals, or priority rules.

## Current limitations

- Relevance and market evidence use small, transparent English-language V1 rules.
- The deterministic audience provider is a safe demo substitute, not an LLM.
- Query definitions are fixed Controlled Demo metadata rather than AI-generated.
- There is no interactive human-review surface yet.

## Not implemented

- Frontend/UI or voice input
- Campaign Brief parser, AI Query Generator, or Human Query Review UI
- Instagram or X live connectors
- Autonomous query diversification or agent loops
- Outreach, email, CRM follow-up, or production deployment
- Follower growth history or cross-platform identity resolution
- Automatic learning from review or feedback

All included creators, handles, content, reviews, and URLs are synthetic. The
project contains no production database connection and no credentials.
