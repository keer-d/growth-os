# Creator Discovery OS

Backend-only V1 implementation case for discovering and prioritizing synthetic
creator profiles for an AI website/portfolio builder campaign.

## What works

- Formal `RawCreatorProfile` contract with observed facts and provenance.
- Natural-language Campaign Brief parsing into a validated, provider-neutral
  Campaign Definition, with explicit incomplete/clarification/failure states.
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

## Campaign Brief parsing

A Campaign Brief is the Growth/GTM manager's original natural-language request:
the outcome, markets, creator content themes, intended audience, and any explicit
exclusions. The parser preserves that original text and produces a separate
structured definition so later pipeline stages can consume validated fields
instead of guessing from prose.

Run the offline Campaign Demo:

```bash
python3 -m pipeline.campaign_demo
```

Try the incomplete or ambiguous synthetic fixtures:

```bash
python3 -m pipeline.campaign_demo --fixture-id campaign_demo_003
python3 -m pipeline.campaign_demo --fixture-id campaign_demo_005
```

The default deterministic provider requires no credential. An optional
OpenAI-compatible live provider reads its endpoint, credential, provider name,
and model only from the environment variables documented in `.env.example`.
Malformed provider output returns an explicit failed result; missing critical
fields produce `incomplete` or `needs_clarification` with questions.

This parser deliberately does not generate search queries, retrieve creators,
assign priorities, infer creator audiences, or create outreach instructions.

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
- AI Query Generator or Human Query Review UI
- Instagram or X live connectors
- Autonomous query diversification or agent loops
- Outreach, email, CRM follow-up, or production deployment
- Follower growth history or cross-platform identity resolution
- Automatic learning from review or feedback

All included creators, handles, content, reviews, and URLs are synthetic. The
project contains no production database connection and no credentials.
