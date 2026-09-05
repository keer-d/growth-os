# Growth OS

**From a testable ICP hypothesis to evidence-backed partner discovery** / 从 ICP 假设到增长证据。

Growth OS is a public implementation case for Growth and GTM operators who need to
decide who to target before they decide whom to source. It adds an upstream ICP
Discovery layer to the existing partner-discovery backend, then preserves the existing
human approval, retrieval, qualification, review, feedback, and run-evidence layers.
Bundled ICP hypotheses and workflow decisions are synthetic. Controlled Demo partner
identities are curated snapshots of public profiles so each displayed name, handle,
summary, and profile URL refers to the same account.

## The two audiences are different

- A **Customer ICP** is a testable hypothesis about who may buy or use the product.
- A **Partner / Creator Profile** describes who may help a Growth team reach that
  customer audience.

Growth OS never collapses those concepts. A selected Customer ICP is translated into a
separate, human-editable Partner Discovery Criteria snapshot. Only after the human
confirms that translation does the existing query-planning workflow begin.

## What "Partner" means here

**Partner** is the umbrella term for everyone this system can surface. A Partner may be a:

- creator
- KOL
- influencer
- micro-influencer
- affiliate partner
- community partner
- media / publisher
- industry expert

Growth and GTM teams do not run eight separate searches for eight separate words, so
V1 does not model eight separate entities. Every discovered record uses one shape and
one qualification path; the partner type is a **presentation label derived from
observable facts** — a bio keyword or the follower count — and it never enters
prioritization. A label nobody can re-check in a second is worse than no label.

## Growth OS V1 data flow

```text
Business Context (human-confirmed)
  -> exactly 3 testable Customer ICP Hypotheses
  -> AI-estimated side-by-side comparison + explicit unknowns
  -> Human selects one hypothesis to test
  -> Partner Discovery Criteria draft
  -> Human confirms or edits the criteria
  -> validated Campaign Definition
  -> AI Draft Search Plan
  -> Human Query Review
  -> Approved Search Plan
  -> controlled fixtures OR live retrieval on Instagram / X / YouTube / Web
  -> raw partner records
  -> same-channel URL deduplication
  -> observable signal extraction
  -> audience-only inference
  -> P1 / P2 / P3 / Needs Review
  -> SQLite system of record
  -> human review and feedback
  -> run/query history, New Partners, and New Partner Yield
```

Users who already know their ICP can enter the existing Campaign Brief path directly.
Users who are not confident yet can use the guided Business Context → ICP path. Both
paths converge on the same validated Campaign and Draft Search Plan contracts.

The boundaries are deliberate:

- An ICP is always labeled a **hypothesis**, never the “correct” market answer.
- ICP comparison scores are AI estimates for prioritizing tests; they are not proof.
- Editing a hypothesis creates `v2`, `v3`, and so on. Earlier versions are immutable.
- The selected hypothesis and its exact criteria snapshot are linked to every run it
  starts, so later evidence can be interpreted against what was actually tested.
- The original human brief is preserved separately from its parsed definition.
- **Draft is not permission to retrieve.** Only an `ApprovedSearchPlan` can reach
  a controlled or live provider.
- Retrieval observes candidate records; it does not decide partner quality.
- Signals explain public evidence, audience inference estimates likely audience,
  and priority remains a separate transparent decision.
- Human feedback is stored for analysis but does not automatically change queries,
  prompts, signals, or priority rules.

## ICP Discovery

Business Context captures only information with a downstream purpose: product identity
and description, the painful problem, strongest value, current or potential users,
current alternatives, observable pain signals, optional geography, and company stage.
A website URL can be recorded, but the offline demo does not pretend to have analyzed
it; a manual product description is required in deterministic mode.

The provider returns exactly three structured hypotheses. Each includes who, context,
pain, why the pain matters, current alternative, value proposition, trigger event,
intent signals, where the audience may be found, why the hypothesis may work, explicit
unknowns, and a test-priority explanation. The comparison dimensions are:

- Pain Severity
- Problem Frequency
- Value Proposition Strength
- Reachability
- Intent Signal Availability
- Potential Commercial Value
- Product Fit

The built-in provider is deterministic and credential-free. An OpenAI-compatible live
provider can be configured with `ICP_LLM_PROVIDER`, `ICP_LLM_BASE_URL`,
`ICP_LLM_API_KEY`, and `ICP_LLM_MODEL`. Credentials are read from the process
environment only. Malformed output, missing context, website-only offline input,
unusable hypotheses, and incomplete discovery criteria all fail explicitly.

V1 stops at storing evidence. It does not yet calculate hypothesis confidence from run
outcomes or recommend keep/refine/drop decisions automatically.

### ICP persistence and observability

SQLite adds append-oriented `business_contexts`, `icp_hypotheses`, `icp_selections`,
`discovery_criteria`, `icp_run_links`, and `product_events` tables. A run link stores
the hypothesis ID, immutable version, name, hypothesis creation time, human selection
time, criteria ID, and exact criteria JSON snapshot.

The product event stream records `icp_discovery_started`,
`business_context_completed`, `icp_hypotheses_generated`,
`icp_hypothesis_selected`, `icp_hypothesis_edited`,
`discovery_criteria_generated`, `discovery_criteria_confirmed`, and
`discovery_run_started_from_icp`. Generation metadata includes provider, model,
prompt/criteria version, duration, and safe error codes; it never stores credentials.

## Channels and connectors

The product surface talks about **channels**. Vendor identity is an implementation
detail that belongs in exactly two places: this section, and the collapsed Technical
Details in the UI. It is never the primary label anywhere a business user reads.

| Channel | Backed by | Environment variable names |
| --- | --- | --- |
| Instagram | Apify actor (`apify/instagram-search-scraper`) | `APIFY_API_TOKEN`, `APIFY_INSTAGRAM_ACTOR_ID`, `APIFY_INSTAGRAM_RESULTS_LIMIT`, `APIFY_INSTAGRAM_TIMEOUT_SECONDS`, `APIFY_INSTAGRAM_MAX_TOTAL_CHARGE_USD` |
| X | Official X API v2 recent search | `X_BEARER_TOKEN`, `X_API_BASE_URL`, `X_API_TIMEOUT_SECONDS`, `X_RESULTS_PER_QUERY` |
| YouTube | YouTube Data API v3 search | `YOUTUBE_API_KEY`, `YOUTUBE_API_BASE_URL`, `YOUTUBE_API_TIMEOUT_SECONDS`, `YOUTUBE_RESULTS_PER_QUERY` |
| Web | A configurable search API | `WEB_SEARCH_API_KEY`, `WEB_SEARCH_BASE_URL`, `WEB_SEARCH_ENGINE_ID`, `WEB_SEARCH_TIMEOUT_SECONDS`, `WEB_RESULTS_PER_QUERY` |

The first variable in each row is the credential that decides whether the channel can
run live. The rest are optional bounds with defaults.

### Instagram

Instagram uses the Apify-maintained `apify/instagram-search-scraper`. The token is sent
only in the Authorization header. Actor timeout, result count, and maximum total charge
remain bounded.

The bounded 2026-09-01 verification reached Apify successfully after the verified
CA-bundle fix. The Actor returned its `no_items` sentinel (`Empty or private data
for provided input`) for the one approved query. That provider sentinel is classified
as a successful zero-result response instead of an invalid partner record. The paid
call was not retried.

The separate one-query smoke command remains:

```bash
python3 -m pipeline.instagram_live_demo
```

### X

X uses the official X API v2 recent-search endpoint with app-only Bearer Token
authentication. It requests the `author_id` expansion and public user fields, then maps
each unique author and matching public Post samples into the shared raw record
contract. See the official
[Recent Search guide](https://docs.x.com/x-api/posts/search/quickstart/recent-search).

### YouTube

YouTube uses the public YouTube Data API v3 search endpoint with an API key, mapping
each returned channel into the shared raw record contract. Google reports quota
exhaustion as HTTP 403 — the same status as a rejected key — so the adapter reads the
response body reason to separate `provider_rate_limit_or_quota` from
`provider_authentication_failure`.

### Web

Web is deliberately vendor-neutral: the adapter maps a generic result-list shape, so
swapping the search vendor is a provider change rather than an adapter change. The
default base URL targets a Google Programmable Search-compatible JSON response, which
is why `WEB_SEARCH_ENGINE_ID` exists. URLs that belong to Instagram, X, or YouTube are
rejected here so a channel cannot smuggle results in through Web.

### Verification status, stated honestly

Automated tests mock every provider response for all four channels. Only Instagram has
been exercised against a real credential, in the single bounded call described above.
**X, YouTube, and Web live retrieval have not been run against real credentials**; they
are verified against mocked provider responses and their error taxonomy only.

## Configuring a channel

Credentials are **server-side environment variables only**. They are read by name,
never parsed from a request, and never sent to the browser: the UI receives a presence
boolean per channel and nothing else. No credential value is printed, logged,
serialized, or written to a run log.

An unconfigured channel is not an error and never blocks a run. It truthfully reports
**"Not configured"** and records `SKIPPED_NOT_CONFIGURED` for each of its approved
queries, while other configured channels continue in the same run. V1 never fabricates
a result for a channel it could not reach.

`.env.example` lists variable names with blank values only. To configure a channel,
copy it, fill in your own values locally, and export them into the server process —
neither the server nor the demo commands parse `.env` automatically:

```bash
set -a
source .env
set +a
python3 -m pipeline.ui_server
```

## Naming: product surface vs storage contract

The internal backend still uses the name `RawCreatorProfile` and the SQLite `creators`
table, and this is deliberate. The public product is **Growth OS** and its discovery
entity is **Partner**; the validated raw storage contract was not renamed. Renaming a
dataclass and a live table to match vocabulary would rewrite the system of record for a
cosmetic reason and invalidate every stored run, so the rename stopped at the boundary
where it earns its cost. The same reasoning keeps the `new_creator_yield` column behind the
"New Partner Yield" metric.

## Local interactive UI

The UI is a thin, credential-safe application layer over the existing discovery backend. It does not
duplicate campaign parsing, query generation, human approval, retrieval, deduplication,
signal extraction, audience inference, priority, or SQLite history logic. The local
browser receives partner evidence, run metrics, and channel readiness booleans; it never
receives channel credentials.

Launch the safe Controlled Demo from the repository root:

```bash
python3 -m pipeline.ui_server
```

Then open [http://127.0.0.1:8765](http://127.0.0.1:8765). The default database is
`data/creator_discovery_os_v1.db`. To keep a separate demo workspace, pass
`--database-path /absolute/path/to/demo.db`.

The six UI areas are:

- **Overview** — the Growth Command Center: current ICP and data context, a real discovery
  funnel, source/query performance, human-review operations, system health, evidence-based
  learnings, and one deterministic next action.
- **ICP** — the two entry paths, progressive Business Context, exactly three
  hypothesis cards, side-by-side evaluation, immutable editing, selection, and
  human-confirmed Partner Discovery Criteria.
- **Discovery** — Campaign Brief → real Draft Search Plan → approve/edit/reject →
  Approved Search Plan → Controlled Demo or explicitly confirmed live execution.
- **Review** — evidence-first partner cards plus detail sections for Observed Facts,
  Derived Signals, AI audience inference, and Human Decision.
- **Runs** — a business-first view of real SQLite New Partner Yield,
  saturation, and query-level evidence. Run IDs and timestamps remain in expandable
  technical details instead of leading the page.
- **Data Sources** — per-channel purpose and a truthful Configured / Not configured
  state, with vendor and variable names kept in Technical Details.

The interface uses a centralized English/Chinese text layer and persists the selected
language in the browser. It also includes purpose-built light and dark themes; both
preserve the blue/purple/pink ambient visual language and meaningful status colors.
Partner and source content is never translated or rewritten.

Instagram, X, YouTube, and Web use consistent accessible channel marks across search
planning, partner records, evidence detail, and query performance. Motion is limited to
interaction feedback, query entry, and actual request processing, and the UI disables
nonessential motion when the browser requests reduced motion.

### Growth Command Center metric definitions

Dashboard metrics are computed from stored run, query, partner, inference, priority, and
review records. Filters are applied to the same cohort before every module is calculated.

- **Discovered** — unique stored partner records in the selected cohort.
- **High Priority** — partners assigned P1 or P2 by the existing priority layer. This is
  explicitly not a claim that a partner is qualified.
- **Review Queue** — partners whose latest human-review state is missing, `unreviewed`, or
  `needs_review`.
- **Approved** — partners whose latest human-review decision is `approve`.
- **Approval Rate** — approved divided by approved plus rejected. It displays `—` when no
  approve/reject decision exists instead of implying a zero-percent rate.
- **Latest New Partners** — new unique partner records produced by the latest selected run.
- **New Partner Yield** — new unique partners divided by raw retrieved results.
- **Human Reviewed** — partners with any stored human-review event, including a
  `needs_review` outcome.

The discovery funnel uses only observed stage counts: Raw Results → New Unique → Signals →
Audience Inference → Priority → Human Reviewed → Approved. The dashboard does not invent
qualification, agreement, conversion, revenue, outreach, latency, or cost metrics when the
backend does not store those facts. Controlled fixtures are always labeled **Sample Data**.

Controlled Demo is the default and requires no credentials. Live retrieval is visually
separate and requires an explicit checkbox before the UI can call the configured
external providers.

Controlled Demo uses a small curated snapshot of public Instagram and X profiles. A
record's displayed name, handle, summary, and external profile URL describe the same
public account; the profile button opens that exact account. The snapshot deliberately
does not claim live retrieval, current follower counts, or observed posting recency.
Derived signals remain conservative when the stored evidence is incomplete. Synthetic
edge cases used to test scoring policy live in a separate test-only fixture and never
appear as clickable partner records. Records produced by configured live providers
continue to show their source-observed external profile link.

### Hosted portfolio demo

The deployed Sites version reuses the same browser interface and runs the deterministic
Controlled Demo in a Cloudflare Worker-compatible application layer. D1 stores workflow,
run, partner, review, and ICP state per browser session so a visitor can complete the
end-to-end demo and revisit the resulting evidence. Live provider credentials are not
shipped to the hosted case: Instagram, X, YouTube, and Web remain truthfully marked as
not configured.

The Python/SQLite implementation remains the canonical local backend. The hosted adapter
exists only to make the public portfolio case runnable in a browser without exposing a
local machine or copying private provider credentials.

## Setup and tests

Python 3.11 or newer is supported. Controlled mode uses only the standard library.
Live HTTPS calls can use the `certifi` trust bundle declared in `requirements.txt`:

```bash
python3 -m pip install -r requirements.txt
python3 -m unittest discover -s tests -v
```

Provider code creates a verified TLS context. It prefers a usable Python/system CA path
and otherwise uses the installed `certifi` bundle. Hostname and certificate verification
stay enabled; the project never uses `verify=False` or an unverified context.

## Complete backend command

The reliable, credential-free portfolio path is:

```bash
python3 -m pipeline.os_demo --mode controlled --reset
```

Repeat the same curated snapshot fixture to create real saturation evidence rather than
hardcoded history:

```bash
python3 -m pipeline.os_demo --mode controlled --reset --runs 2
```

The command executes and displays Campaign, Draft Plan, Human Review, Approved Queries,
Discovery, Deduplication, Signals, Audience Inference, Priority, SQLite, and Discovery
Insights. The first fixture run retrieves 12 raw records containing two same-channel
duplicates; subsequent runs encounter the already stored partners.

Live mode is available when channel credentials are configured in the process
environment:

```bash
python3 -m pipeline.os_demo --mode live
```

Live mode never fabricates an unavailable provider result. A missing channel is recorded
per query as `SKIPPED_NOT_CONFIGURED`; another configured channel can continue in the
same run.

## Query outcomes and history

Each approved query has exactly one execution status:

- `SUCCESS_WITH_RESULTS`
- `SUCCESS_ZERO_RESULTS`
- `FAILED`
- `SKIPPED_NOT_CONFIGURED`

SQLite stores run ID, Campaign and Approved Plan IDs, approved query/source IDs, channel,
connector, final query text, search angle, status, retrieved/duplicate/new counts, error
code, timestamps, and New Partner Yield. Yield is `NULL` for a failed or skipped query,
so it cannot be mistaken for a successful 0% yield.

`get_saturation_evidence()` exposes real per-run evidence by stable query and search
angle. V1 observes that evidence but never changes or diversifies queries autonomously.

## Errors and logging

V1 distinguishes configuration missing, authentication, TLS, network, timeout, provider
quota/rate limit, malformed response, invalid partner record, and SQLite write failure.
Provider/query failures remain local to their query where possible.

The OS command writes lightweight JSON run logs containing IDs, channel, connector,
status, counts, error code, and duration. Credentials and partner contact/profile
content are not logged.

## Local data and security

The default database is `data/creator_discovery_os_v1.db`; SQLite artifacts and all
`.env` variants except `.env.example` are ignored. `.env.example` contains variable
names with blank values only. No production repository, database, prompt, rule,
credential, or external system is imported or connected.

## Deliberately outside V1

- Voice input
- Automatic outreach, CRM follow-up, or assignment
- Follower-growth tracking or cross-channel identity resolution
- Autonomous/infinite search, automatic learning, or query diversification
- Billing, authentication, multi-user roles, and deployment

The existing discovery, qualification, human review, feedback, and run-history logic
remains intact. Growth OS V1 adds the upstream ICP layer and its traceability tables;
it does not deploy or automate outreach.
