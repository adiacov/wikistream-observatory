# WikiStream Observatory Brief

## Project name

`wikistream-observatory`

## Product name

WikiStream Observatory

## Tagline

Real-time observability for Wikimedia edit activity, automation patterns, and review workload.

---

## Origin

The user wants to build a serious data engineering showcase project while unemployed and searching for a data engineering role.

The project must:

- run locally with Docker / Docker Compose;
- use real data or solve a real problem;
- use only free tools and free data sources;
- feel close to a production-style data processing system;
- be reviewable by other professionals;
- preferably expose visible results through a local dashboard and/or GitHub Pages artifact.

Streaming was selected as the first showcase direction because it complements the user's previous batch-oriented Citibike capstone and avoids repeating the same project shape.

Wikimedia RecentChanges was selected as a promising data source because it is a real public event stream, free to access, high-volume, and operationally meaningful.

Initial exploration showed that a simple bot-vs-human count dashboard would be too shallow. The stronger project framing is observability: transform raw Wikimedia edit events into signals about automation patterns, spikes, review workload, and areas that may deserve human attention.

---

## Core problem framing

Wikimedia projects rely heavily on automation. Bots perform useful maintenance, categorization, cleanup, link repair, vandalism response, and other repetitive work. At the same time, automation creates operational and governance risks:

- bots can malfunction or be misused;
- bot-like activity can create large bursts of edits;
- bot edits may be hidden from default Recent Changes views;
- smaller wikis may be more vulnerable to spam, vandalism, or low-review-capacity bursts;
- human reviewers need help focusing attention on relevant activity;
- cross-wiki automation patterns are distributed and hard to summarize manually.

This project should not pretend that Wikimedia lacks safeguards. Wikimedia already has bot policies, bot flags, abuse filters, edit review tools, counter-vandalism workflows, and machine-learning assisted review systems.

The project's value is not enforcement.

The project's value is observability:

> Turn the live cross-wiki RecentChanges stream into useful operational signals that help understand what is happening, where automation is concentrated, where activity spikes occur, and where human review workload may be high.

---

## What this project is not

Avoid framing this as:

- a system to block Wikimedia edits;
- a replacement for Wikimedia's bot approval process;
- a replacement for AbuseFilter, ORES, LiftWing, Recent Changes filters, or patrol tools;
- a system that accuses individual users of abuse;
- a simplistic bot-vs-human dashboard;
- an AI hype project.

Prefer framing it as:

- a streaming data engineering observability platform;
- a transparency dashboard over public Wikimedia edit activity;
- a local, reproducible pipeline that detects signals, not guilt;
- a portfolio project demonstrating practical streaming ingestion, processing, storage, data quality, and dashboarding.

---

## Research evidence and useful references

Future agents should continue web research during planning and implementation. Do not rely only on model training knowledge, because Wikimedia infrastructure, APIs, schemas, and ML services may have changed.

Initial research found these relevant sources:

### Wikimedia EventStreams

RecentChanges stream:

```text
https://stream.wikimedia.org/v2/stream/recentchange
```

EventStreams documentation:

```text
https://wikitech.wikimedia.org/wiki/Event_Platform/EventStreams
```

Important implementation note from documentation: server-side filtering is not supported; consumers should filter client-side.

### RecentChange schema

Schema endpoint:

```text
https://schema.wikimedia.org/repositories/primary/jsonschema/mediawiki/recentchange/latest
```

Relevant fields observed in live events include:

- `meta.domain`
- `type`
- `namespace`
- `title`
- `timestamp`
- `user`
- `bot`
- `minor`
- `patrolled`
- `length.old`
- `length.new`
- `revision.old`
- `revision.new`
- `comment`

The `bot` field is important, but should not be the only signal.

### Bot policy and bot risk

Wikimedia / Wikipedia bot docs indicate that bots are useful but may cause disruption if malfunctioning or misused. Bot approval, bot flags, global bots, and operator responsibilities are real governance topics.

Useful references:

```text
https://en.wikipedia.org/wiki/Wikipedia:Bots
https://en.wikipedia.org/wiki/Wikipedia:Bot_policy
https://meta.wikimedia.org/wiki/Bot
https://meta.wikimedia.org/wiki/Bot_policy
https://www.mediawiki.org/wiki/Manual:Bots
```

Key research points found:

- bots can make edits very rapidly;
- bots must generally be useful, harmless, approved, and responsibly operated;
- bot flags can hide bot edits from default Recent Changes;
- bot operators are expected to monitor bot behavior and respond to issues;
- global and local bot policies differ across wikis.

### Vandalbot / spambot and small-wiki monitoring context

Useful references:

```text
https://meta.wikimedia.org/wiki/Vandalbot
https://meta.wikimedia.org/wiki/Small_Wiki_Monitoring_Team
https://meta.wikimedia.org/wiki/Countervandalism_Network
```

Key research points found:

- vandalbots and spambots are known concerns;
- small-wiki monitoring exists because smaller wikis may be targeted or lack local review capacity;
- counter-vandalism workflows use real-time monitoring and coordination.

### Edit review and ML-assisted filtering context

Useful references:

```text
https://www.mediawiki.org/wiki/Help:New_filters_for_edit_review
https://www.mediawiki.org/wiki/Edit_Review_Improvements/New_filters_for_edit_review
https://www.mediawiki.org/wiki/ORES
```

Key research points found:

- Recent Changes filters are designed to help reviewers focus their effort;
- quality and intent filters have used machine learning predictions;
- ORES has been deprecated/modernized toward newer Wikimedia ML infrastructure such as LiftWing, so future agents must verify current status before depending on it;
- the project should avoid depending on paid or unstable external ML services for MVP.

---

## Web research requirement for future agents

Future agents working on this project should actively use web research when making design or implementation decisions.

Reason:

- LLM training data may be stale;
- Wikimedia APIs, schemas, rate limits, stream behavior, and ML infrastructure may change;
- project value depends on grounding the work in real Wikimedia practices and current documentation;
- shallow generic streaming ideas should be avoided.

Before implementing any major feature, verify current documentation or live behavior for:

- EventStreams connection behavior;
- RecentChange schema fields;
- expected rate limits / etiquette / user-agent requirements;
- bot flag semantics;
- availability of ORES / LiftWing or any scoring APIs if considered;
- current Wikimedia bot, vandalism, and edit review workflows;
- any restrictions on consuming or publishing derived data.

Preserve important research findings in the target project documentation, with source links and dates where useful.

---

## Candidate users / reviewers

Primary portfolio audience:

- data engineering hiring managers;
- senior data engineers reviewing project architecture;
- technical recruiters who need a clear project story;
- peers who want to run the system locally.

Problem-domain users / conceptual users:

- Wikimedia patrollers;
- small-wiki monitoring volunteers;
- bot operators;
- community members interested in automation transparency;
- researchers interested in cross-wiki activity patterns.

The MVP does not need actual Wikimedia adoption. It must, however, solve a plausible real observability problem and be honest about its limits.

---

## Business / operational value hypotheses

The project should be designed around one or more of these value hypotheses:

### 1. Automation spike detection

Detect when a bot or automation-heavy account suddenly increases activity compared with a recent baseline.

Value:

- highlights possible malfunctioning bots;
- surfaces large maintenance runs;
- helps distinguish normal background automation from unusual bursts.

### 2. Human-review workload monitoring

Estimate where human attention may be needed after excluding known bot activity.

Value:

- helps understand which domains/wikis have high non-bot edit volume;
- can highlight unpatrolled, anonymous, or high-change-size edits where fields are available;
- connects to Recent Changes patrol and edit review workflows.

### 3. Small-wiki risk signals

Track bursts on lower-volume wikis, especially from non-bot or automation-like accounts.

Value:

- aligns with Small Wiki Monitoring Team concerns;
- small wikis may have less local review capacity;
- unusual bursts on small projects are easier to miss globally.

### 4. Automation-like behavior among non-bot accounts

Detect accounts that are not flagged as bots but behave with automation-like patterns, such as very high event frequency in a short window.

Value:

- useful as a transparency signal;
- may reveal semi-automated tools or unflagged automation;
- must be presented carefully and never as an accusation.

Recommended wording: `automation-like activity`, not `bad bot` or `abuse`.

### 5. Cross-wiki transparency reporting

Produce a digest of edit stream activity:

- top active wikis;
- top bot accounts;
- top non-bot accounts by activity;
- bot share by wiki;
- edit-size-change distributions;
- namespace activity;
- event type breakdown;
- anomalies / notable changes.

Value:

- makes a complex public stream understandable;
- creates a visible GitHub Pages artifact;
- gives recruiters a clear output to inspect.

---

## MVP scope

The MVP should be a local Dockerized streaming platform that:

1. connects to Wikimedia RecentChanges EventStreams;
2. ingests live events into a local Kafka-compatible broker, preferably Redpanda for simpler local operation;
3. processes events into normalized facts and time-windowed metrics;
4. stores data locally in DuckDB if feasible, because it is lightweight and easy to inspect;
5. computes a small set of observability signals;
6. exposes a Streamlit dashboard for local exploration;
7. optionally exports a static summary report suitable for GitHub Pages.

The MVP should be runnable by another professional with a simple command such as:

```bash
docker compose up --build
```

The local dashboard should then be available at something like:

```text
http://localhost:8501
```

---

## Suggested MVP signals

Start with simple, explainable signals rather than complex ML.

### Live activity overview

- events per minute;
- bot vs non-bot share;
- event type breakdown;
- top domains/wikis by event count.

This is necessary context but not sufficient as the main value.

### Bot spike detector

For each flagged bot account and/or domain:

- compute events per rolling window;
- compare to recent baseline;
- flag sudden increases.

Example output:

```text
SuperGrey-bot produced 4.8x its 30-minute baseline on zh.wikisource.org.
```

### Non-bot automation-like activity detector

For non-bot users:

- detect high event frequency within short windows;
- optionally combine with repeated event types, repeated domains, or low variation in comments;
- label as `automation-like activity`.

Important: present as a signal requiring review, not proof of misuse.

### Small-wiki burst detector

For domains with low recent baseline volume:

- detect sudden event bursts;
- show whether activity is bot, non-bot, anonymous, or mixed where fields allow.

### Review workload proxy

Estimate workload using available fields:

- non-bot edits per wiki;
- unpatrolled events where `patrolled` exists;
- anonymous edits if user identity fields allow reliable detection;
- large edit-size changes;
- new page events.

### Daily / session summary

Generate a report for the captured period:

- number of events processed;
- top wikis;
- top bots;
- top automation-like non-bot accounts;
- top spike incidents;
- small-wiki bursts;
- data quality notes;
- limitations.

---

## Architecture direction

Preferred local architecture:

```text
Wikimedia EventStreams
  -> stream ingestor service
  -> Redpanda / Kafka topic: raw_recentchange
  -> stream processor service
  -> normalized events + windowed metrics
  -> DuckDB local analytical store
  -> Streamlit dashboard
  -> optional static report export for GitHub Pages
```

Recommended components:

- Docker Compose for local orchestration;
- Redpanda as Kafka-compatible broker, unless Kafka is clearly better;
- Python for ingestion and processing;
- DuckDB for lightweight local analytical storage, if concurrent write/read behavior is manageable;
- Streamlit for dashboard UI;
- pytest for unit tests;
- Ruff or similar for linting if helpful;
- Makefile or task runner for common commands.

DuckDB note:

- DuckDB is attractive because it is lightweight, easy to inspect, and avoids heavier database setup.
- The implementation should verify safe access patterns. A simple design is one writer process and read-only dashboard queries, or periodic Parquet/DuckDB snapshots if needed.

Streamlit note:

- Streamlit is preferred for the local dashboard because it is simple, free, and easy for reviewers to run.

---

## Data quality / reliability requirements

The project should demonstrate production-like thinking.

Include at least some of:

- schema validation for incoming events;
- dead-letter handling for malformed events;
- reconnect logic for EventStreams;
- consumer offset / restart behavior;
- deduplication using event id or metadata where appropriate;
- event-time vs processing-time distinction;
- basic lag / throughput metrics;
- data freshness checks;
- reproducible sample/replay mode for demos and tests.

The sample/replay mode is important because a reviewer should be able to see meaningful dashboard data without waiting for long live collection.

---

## Dashboard expectations

The Streamlit dashboard should answer questions like:

- What is happening in the Wikimedia edit stream right now?
- Which wikis are most active?
- Which bots are most active?
- Which bots or domains show unusual spikes?
- Which non-bot accounts show automation-like activity?
- Which small wikis show unusual bursts?
- Where might human review workload be concentrated?
- What are the limitations of these signals?

The dashboard should avoid moralizing language. Use terms like:

- `signal`
- `spike`
- `automation-like`
- `requires review`
- `unusual relative to recent baseline`

Avoid:

- `abuser`
- `bad bot`
- `malicious`
- `guilty`
- `vandal` unless directly quoting Wikimedia concepts or using clearly defined criteria.

---

## GitHub Pages / public artifact

Bonus goal: generate a static report suitable for GitHub Pages.

Possible artifact:

```text
reports/latest/index.html
```

or Markdown converted to static HTML.

The public artifact could show:

- a sample captured session;
- key metrics and charts;
- top signals;
- architecture diagram;
- limitations and methodology.

Important: be careful with displaying individual usernames publicly. Wikimedia data is public, but the project should still present derived signals responsibly. For GitHub Pages, consider aggregating or limiting sensitive/account-level details, or clearly explain that all data comes from public Wikimedia streams.

---

## Non-goals for MVP

- no paid cloud;
- no paid APIs;
- no production deployment requirement;
- no edit blocking;
- no writing to Wikimedia;
- no user accusation system;
- no complex ML in MVP;
- no dependency on ORES/LiftWing unless current docs and access are verified;
- no full historical backfill;
- no Kubernetes;
- no over-engineered microservice sprawl.

---

## Open questions

- Which exact signal set should be in the MVP?
- Should the MVP focus on all Wikimedia projects or a selected subset first?
- How should "small wiki" be defined without historical project-size data?
- Should the system store raw events, normalized events, aggregates, or all three?
- Is DuckDB sufficient for live dashboard reads while streaming writes occur?
- Should processed data be written to DuckDB directly or via Parquet files?
- How should demo/replay data be captured and shipped without making the repo too large?
- How much account-level detail is acceptable in public reports?
- Should GitHub Pages be part of MVP or a post-MVP enhancement?

---

## First implementation recommendation

Start narrow and build vertically.

Recommended first milestone:

1. Docker Compose with Redpanda, ingestor, processor, DuckDB volume, and Streamlit dashboard.
2. Ingest Wikimedia RecentChanges events into `raw_recentchange` topic.
3. Normalize selected fields into a local store.
4. Display basic live metrics in Streamlit.
5. Add one non-trivial signal: bot spike detection or small-wiki burst detection.
6. Add sample/replay mode.
7. Document architecture, assumptions, and limitations.

Do not start with all signals at once.

A strong MVP is better than a broad unfinished platform.

---

## Success criteria

The project is successful as a portfolio showcase if another data professional can:

1. clone the repo;
2. run the full system locally with Docker Compose;
3. watch real Wikimedia stream data flow through the pipeline;
4. inspect code, tests, and architecture;
5. understand why Redpanda/Kafka, DuckDB, and Streamlit were used;
6. see meaningful observability signals beyond bot/human counts;
7. read clear documentation explaining the real-world problem, limitations, and future work.

The project should demonstrate:

- streaming ingestion;
- event normalization;
- local analytical storage;
- windowed metrics;
- anomaly/signal detection;
- data quality/reliability thinking;
- dashboard/reporting;
- responsible problem framing.
