# Feature Specification: WikiStream MVP Vertical Slice

**Feature Branch**: `001-wikistream-mvp-slice`

**Created**: 2026-06-05

**Status**: Draft

**Input**: User description: "Build the first WikiStream Observatory MVP vertical slice. A local user can run the project, ingest live public Wikimedia RecentChanges activity, view current edit-stream activity in a local dashboard, and inspect one meaningful observability signal beyond simple bot-vs-human counts. The feature should help data engineers understand what is happening in the live Wikimedia edit stream, which Wikimedia domains are most active, how automation is concentrated, and where unusual activity may deserve human review. It must frame outputs as observability signals, not enforcement decisions or accusations. Include these user outcomes: live overview metrics, one explainable non-trivial signal, sample/replay mode, and visibility into freshness, malformed/missing-field handling, and limitations. Scope excludes blocking/reporting/accusing users, paid services, cloud deployment, Kubernetes, complex ML, historical backfill, and shallow bot-vs-human-only dashboards."

## Clarifications

### Session 2026-06-05

- Q: Should the MVP bot spike signal be detected primarily by account, by Wikimedia domain, globally, or all as equal requirements? → A: Detect bot spikes primarily per Wikimedia domain, with optional top contributing bot accounts as context.
- Q: When should live dashboard data be considered fresh for user-facing freshness status? → A: Fresh if the latest event was observed within 60 seconds.
- Q: What replay/sample data capability is required for the MVP deterministic demo? → A: Include a bundled representative sample that demonstrates metrics and one bot spike signal.
- Q: How may account labels appear in MVP signal outputs? → A: Show only top contributing bot account labels as optional context with limitation text.
- Q: What data-quality categories must be visible for malformed or incomplete events? → A: Count malformed/rejected events and missing-field events separately.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Observe Live Edit Activity (Priority: P1)

A data engineer starts the local project and sees live Wikimedia edit-stream activity summarized in a local dashboard. The user can understand current event volume, active Wikimedia domains, event types, and the share of bot-flagged versus non-bot activity.

**Why this priority**: Live activity visibility is the minimum viable demonstration that the project can ingest real public stream data and convert it into useful operational context.

**Independent Test**: Start the local project, allow live events to arrive, and verify the dashboard shows current activity metrics, updates over time, and indicates when the latest event was observed.

**Acceptance Scenarios**:

1. **Given** the project is running locally and public edit events are available, **When** the user opens the dashboard, **Then** they see event volume over time, top active Wikimedia domains, event type breakdown, and bot/non-bot share.
2. **Given** live events continue arriving, **When** the user waits for at least one refresh interval, **Then** displayed activity metrics update without requiring a restart.
3. **Given** no event has arrived in the last 60 seconds, **When** the user views the dashboard, **Then** the dashboard clearly indicates stale data status rather than silently showing stale data.

---

### User Story 2 - Inspect an Explainable Bot Spike Signal (Priority: P2)

A data engineer inspects an explainable observability signal showing bot-flagged activity on a Wikimedia domain that is unusually high compared with that domain's recent baseline. The signal may include top contributing bot accounts as context, but the primary signal is domain-level and uses careful language, not accusations.

**Why this priority**: One meaningful signal proves the project goes beyond a shallow bot-vs-human count and demonstrates windowed metrics and anomaly-style reasoning.

**Independent Test**: Use live or replayed data containing a clear bot activity increase and verify the dashboard identifies the spike, shows the comparison to baseline, and explains limitations.

**Acceptance Scenarios**:

1. **Given** bot-flagged activity on a Wikimedia domain is substantially above that domain's recent baseline, **When** the user opens the signal view, **Then** the dashboard shows the spike magnitude, domain context, optional top contributing bot accounts, and the comparison window.
2. **Given** the signal is displayed, **When** the user reads its wording, **Then** it is framed as an observability signal requiring review, only shows top contributing bot account labels as optional context, and does not claim abuse, malfunction, or guilt.
3. **Given** no meaningful bot spike is present, **When** the user opens the signal view, **Then** the dashboard reports that no spike currently meets the signal threshold and still explains how the signal is evaluated.

---

### User Story 3 - Demonstrate with Sample or Replay Data (Priority: P3)

A data engineer can run a sample or replay mode using bundled representative sample data that populates the dashboard with meaningful example metrics and one bot spike signal without waiting for a long live collection period.

**Why this priority**: Users may evaluate the project at a time when the live stream is quiet, unavailable, or has not yet produced interesting signals.

**Independent Test**: Start the project in sample/replay mode and verify the bundled representative sample displays activity metrics and at least one bot spike signal from replayed public-data examples.

**Acceptance Scenarios**:

1. **Given** the user selects sample or replay mode, **When** the project starts, **Then** dashboard metrics populate from bundled representative events without requiring live stream availability.
2. **Given** replay data contains a known bot spike example, **When** the user views the signal section, **Then** the expected signal appears with baseline comparison and limitations.
3. **Given** replay mode is active, **When** the user views freshness information, **Then** the dashboard clearly distinguishes replayed data from live data.

---

### User Story 4 - Understand Data Quality and Limitations (Priority: P4)

A data engineer can understand how the project treats malformed events, missing fields, data freshness, and the limits of derived observability signals.

**Why this priority**: Production-like reliability thinking and responsible interpretation are essential to the project’s value as a local data engineering system.

**Independent Test**: Feed or replay events with missing or malformed fields and verify the dashboard or documentation reports handling behavior and limitations clearly.

**Acceptance Scenarios**:

1. **Given** malformed or incomplete events are encountered, **When** the user checks data quality information, **Then** they see separate counts for malformed/rejected events and missing-field events.
2. **Given** some event fields are unavailable, **When** metrics or signals depend on those fields, **Then** the dashboard or documentation explains the limitation rather than implying full certainty.
3. **Given** top contributing bot account labels appear in a signal, **When** they are shown to the user, **Then** the presentation includes limitation text explaining that the domain-level signal is not an abuse determination or account-level accusation.

---

### User Story 5 - Understand Project Purpose and Usage (Priority: P1)

A data engineer can read project documentation that explains the project goal, real-world problem, proposed observability solution, responsible framing, MVP scope, local start instructions, dashboard usage, live versus replay mode, and known limitations.

**Why this priority**: The project is a local observability system; without clear documentation, users cannot quickly understand why the project exists, how to run it, or how to evaluate the result.

**Independent Test**: A user who has not seen the code can read the project documentation, start the MVP locally, open the dashboard, understand what the displayed signals mean, and identify the stated limitations.

**Acceptance Scenarios**:

1. **Given** a user opens the project repository, **When** they read the project documentation, **Then** they understand the project goal, real-world problem, observability approach, and MVP scope.
2. **Given** a user follows the documented local start instructions, **When** prerequisites are available, **Then** they can start the MVP and find the dashboard without needing source-code knowledge.
3. **Given** a user reads the usage and limitations documentation, **When** they inspect live or replayed dashboard output, **Then** they understand how to interpret metrics, signals, freshness, replay mode, and responsible-use boundaries.

### Edge Cases

- Project documentation is the first thing a user sees and must be useful without prior chat context.
- Live public stream is temporarily unavailable or disconnects during local operation.
- Incoming events have missing, unexpected, or malformed fields and must be counted in distinct malformed/rejected and missing-field categories.
- No bot spike meets the configured signal criteria during a live session.
- Event volume is high enough that the dashboard must summarize rather than list every event.
- Replay/sample data is active and must not be mistaken for live current activity.
- Top contributing bot account labels may be displayed as optional signal context and require careful, non-accusatory limitation text.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST allow a local user to start the MVP and view a local dashboard for Wikimedia edit-stream observability.
- **FR-002**: The system MUST ingest live public Wikimedia RecentChanges activity for the purpose of local observability.
- **FR-003**: The system MUST present live activity overview metrics including event volume over time, top active Wikimedia domains, event type breakdown, and bot/non-bot share.
- **FR-004**: The system MUST track and display data freshness, including the latest observed event time or equivalent freshness indicator, and classify live data as fresh only when the latest observed event is no more than 60 seconds old.
- **FR-005**: The system MUST normalize incoming edit events into a consistent set of observable fields sufficient for activity metrics and the initial signal.
- **FR-006**: The system MUST provide one explainable domain-level bot spike observability signal comparing current bot-flagged activity for a Wikimedia domain against that domain's recent baseline.
- **FR-007**: The bot spike signal MUST display the current activity level, baseline comparison, domain context, optional top contributing bot account labels, and enough context for a user to understand why it appeared.
- **FR-008**: The system MUST avoid language that blocks, reports, accuses, or labels Wikimedia users as abusive, malicious, guilty, or bad bots.
- **FR-009**: The system MUST provide sample or replay mode with bundled representative sample data that demonstrates activity metrics and at least one bot spike signal without relying on a long live collection period.
- **FR-010**: The system MUST clearly distinguish live data from sample or replayed data wherever freshness or signals are shown.
- **FR-011**: The system MUST expose data quality information with separate counts for malformed/rejected events and missing-field events encountered during ingestion or replay.
- **FR-012**: The system MUST document or display limitations for derived signals, especially when optional top contributing bot account labels or bot-related activity are shown.
- **FR-013**: The MVP MUST remain narrow in scope: live activity, normalized events, basic metrics, one bot spike signal, local dashboard, and sample/replay support.
- **FR-014**: The MVP MUST NOT require paid services, paid APIs, cloud deployment, Kubernetes, complex machine learning, historical backfill, or any interaction that writes to Wikimedia.
- **FR-015**: The project MUST include user-facing documentation explaining the project goal, problem framing, observability solution, MVP scope, local start instructions, dashboard usage, live versus replay mode, data quality behavior, responsible-use boundaries, and known limitations.

### Key Entities *(include if feature involves data)*

- **Recent Change Event**: A public Wikimedia edit-stream event used for observability. Key attributes include source domain, event type, timestamp, user/account label, bot flag, namespace/title context, size-change information when available, and data-quality status.
- **Activity Metric**: A summarized measurement over a recent time window, such as event volume, domain counts, event type counts, and bot/non-bot share.
- **Bot Spike Signal**: An explainable domain-level observation that current bot-flagged activity on a Wikimedia domain is unusually high relative to that domain's recent baseline. It includes current level, baseline level, comparison magnitude, domain context, optional top contributing bot account labels, and limitations.
- **Replay Sample**: A bundled reusable set of public-data-derived example events that demonstrates dashboard metrics and one bot spike signal without requiring live collection.
- **Data Quality Count**: A recorded count or explanation of malformed/rejected events, missing-field events, stale data, or other conditions affecting interpretation. Malformed/rejected event counts and missing-field event counts are tracked separately.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can start the MVP locally and see dashboard activity metrics within 5 minutes of following the project instructions.
- **SC-002**: During a live run with available public edit events, the dashboard shows updated activity metrics and a freshness indicator within 60 seconds of receiving events, and marks data stale when no event has been observed for more than 60 seconds.
- **SC-003**: The live activity overview includes at least four metric groups: event volume over time, top domains, event type breakdown, and bot/non-bot share.
- **SC-004**: The bot spike signal shows a current-vs-baseline comparison with a numeric or categorical spike magnitude for at least one live or replayed scenario.
- **SC-005**: Sample/replay mode demonstrates dashboard metrics and at least one bot spike signal from bundled representative sample data within 2 minutes of starting that mode.
- **SC-006**: At least 95% of intentionally malformed or missing-field sample events used in validation are either handled safely or rejected, with separate visible counts for malformed/rejected events and missing-field events.
- **SC-007**: A user can identify whether displayed data is live or replayed and whether it is fresh or stale without reading source code.
- **SC-008**: User-facing text for the signal contains no accusation-oriented language and includes a limitation note explaining that signals are not enforcement decisions.
- **SC-009**: A first-time user can read the project documentation and identify the project purpose, the problem being addressed, the local run path, dashboard usage, replay mode, and limitations within 10 minutes.

## Assumptions

- The primary user is a data engineer running the project locally.
- Wikimedia RecentChanges public activity is an acceptable live source for the MVP because the project is read-only and observability-focused.
- Bot spike detection is selected as the first non-trivial signal because it directly supports the automation-observability framing and can be explained without complex machine learning.
- The MVP may show only top contributing bot account labels when needed for signal context, and the presentation must remain careful, contextual, and non-accusatory.
- Sample/replay data may be small, bundled, and curated, as long as it is clearly labeled and sufficient to demonstrate expected metrics and one bot spike signal.
- Historical backfill, public hosted reporting, additional signal types, and advanced review workflows are outside this feature scope.
- Project documentation is part of the MVP definition because the target audience includes users who need to understand and run the system without prior context.
