# Tasks: WikiStream MVP Vertical Slice

**Input**: Design documents from `/specs/001-wikistream-mvp-slice/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`, `.specify/memory/constitution.md`

**Tests**: Include validation tasks because this feature explicitly requires testable parsing, normalization, aggregation, signal detection, replay/demo behavior, data-quality behavior, and local run validation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing. Preserve responsible-observability language and avoid accusation-oriented outputs.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Initialize the local multi-service Python project and Docker Compose skeleton.

- [X] T001 Create repository runtime directories with `.gitkeep` files in `services/ingestor/wikistream_ingestor/`, `services/processor/wikistream_processor/`, `services/dashboard/app/`, `src/wikistream_observatory/`, `tests/unit/`, `tests/integration/`, `tests/fixtures/`, `schemas/`, `data/replay/`, and `data/snapshots/`
- [X] T002 Create root Python package configuration with Python 3.12 dependencies and pytest settings in `pyproject.toml`
- [X] T003 [P] Create shared package initializer in `src/wikistream_observatory/__init__.py`
- [X] T004 [P] Create service package initializers in `services/ingestor/wikistream_ingestor/__init__.py`, `services/processor/wikistream_processor/__init__.py`, and `services/dashboard/app/__init__.py`
- [X] T005 Create Docker Compose stack with Redpanda, ingestor, processor, dashboard, ports, environment variables, and snapshot volume in `compose.yaml`
- [X] T006 [P] Create ingestor Dockerfile installing the shared package and service code in `services/ingestor/Dockerfile`
- [X] T007 [P] Create processor Dockerfile installing the shared package and service code in `services/processor/Dockerfile`
- [X] T008 [P] Create dashboard Dockerfile exposing Streamlit on port 8501 in `services/dashboard/Dockerfile`
- [X] T009 [P] Create local configuration example for live/replay mode, Kafka addresses, snapshot path, and thresholds in `.env.example`
- [X] T010 [P] Update generated data exclusions while keeping replay data in version control in `.gitignore`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build shared configuration, contracts, schemas, logging, storage helpers, and Kafka utilities required by all stories.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T011 Define strongly typed configuration loading for mode, Kafka, snapshot paths, freshness, replay, and signal thresholds in `src/wikistream_observatory/config.py`
- [X] T012 [P] Implement JSON-style structured logging helper with service/event/mode fields in `src/wikistream_observatory/logging.py`
- [X] T013 [P] Define dataclasses or typed dictionaries for normalized events, activity metrics, bot spike signals, and data-quality counts in `src/wikistream_observatory/models.py`
- [X] T014 [P] Create normalized RecentChanges JSON schema matching `data-model.md` fields in `schemas/recentchange_normalized.schema.json`
- [X] T015 Implement atomic Parquet snapshot writer, snapshot dataset path conventions, and 6-hour live retention helper in `src/wikistream_observatory/storage.py`
- [X] T016 Implement DuckDB snapshot query helpers that tolerate missing or empty Parquet datasets in `src/wikistream_observatory/queries.py`
- [X] T017 Implement Kafka producer/consumer utility wrappers for `raw_recentchange`, message keys, JSON serialization, and broker readiness retries in `src/wikistream_observatory/kafka.py`
- [X] T018 Implement shared time utilities for UTC parsing, event-time fallback, bucket boundaries, and freshness classification in `src/wikistream_observatory/time_utils.py`
- [X] T019 Add foundational import/config/storage smoke tests in `tests/unit/test_foundation.py`

- [X] T020 [P] Verify current Wikimedia EventStreams documentation, RecentChange schema fields, rate-limit/etiquette/user-agent guidance, and bot flag semantics before implementation; preserve findings first in `specs/001-wikistream-mvp-slice/research.md` for later README incorporation

**Checkpoint**: Foundation ready - user story implementation can now begin in priority order or in parallel by story.

---

## Phase 3: User Story 1 - Observe Live Edit Activity (Priority: P1) 🎯 MVP

**Goal**: A reviewer starts the local stack and sees live Wikimedia RecentChanges activity summarized in the dashboard with freshness status.

**Independent Test**: Run live mode, open `http://localhost:8501`, and verify event volume, top domains, event types, bot/non-bot share, and latest observed event/freshness update over time.

### Tests for User Story 1

> **NOTE: Write these tests FIRST and ensure they fail before implementation.**

- [X] T021 [P] [US1] Add normalization tests for required fields, optional missing fields, bot default behavior, and timestamp fallback in `tests/unit/test_normalization.py`
- [X] T022 [P] [US1] Add activity-window aggregation tests for events per minute, top domains, event types, and bot/non-bot share in `tests/unit/test_windows.py`
- [X] T023 [P] [US1] Add live pipeline integration smoke test using a fake raw Kafka payload and snapshot output in `tests/integration/test_live_pipeline_smoke.py`

### Implementation for User Story 1

- [X] T024 [US1] Implement RecentChanges normalization and deterministic fallback event IDs in `src/wikistream_observatory/normalization.py`
- [X] T025 [US1] Implement activity metric aggregation for 1-minute windows, top domains, event types, and bot/non-bot share in `src/wikistream_observatory/windows.py`
- [X] T026 [US1] Implement Wikimedia EventStreams SSE client with `httpx`/`httpx-sse`, public endpoint, and capped exponential reconnect backoff in `services/ingestor/wikistream_ingestor/eventstreams.py`
- [X] T027 [US1] Implement ingestor main loop publishing live `source_mode=live` raw events to `raw_recentchange` in `services/ingestor/wikistream_ingestor/main.py`
- [X] T028 [US1] Implement processor consumer loop that normalizes raw events, updates activity metrics, writes normalized and metric snapshots every 15 seconds in `services/processor/wikistream_processor/main.py`
- [X] T029 [P] [US1] Implement dashboard data-loading functions for overview metrics and freshness using DuckDB snapshots in `services/dashboard/app/data.py`
- [X] T030 [US1] Implement Streamlit mode/freshness section and overview charts in `services/dashboard/app/main.py`
- [X] T031 [US1] Add Streamlit entry point and page configuration for Docker execution in `services/dashboard/app/main.py`
- [X] T032 [US1] Add empty-state handling for missing snapshots and unavailable live data in `services/dashboard/app/main.py`
- [X] T033 [US1] Verify live-mode local run behavior and record manual validation notes in `specs/001-wikistream-mvp-slice/quickstart.md`

**Checkpoint**: User Story 1 is fully functional and testable independently as the MVP live overview.

---

## Phase 4: User Story 5 - Understand Project Purpose and Usage (Priority: P1)

**Goal**: A first-time reviewer understands the project purpose, local run path, dashboard usage, responsible framing, and limitations.

**Independent Test**: Read `README.md`, start the stack with the documented command, open the dashboard, and identify live/replay behavior and signal limitations without source-code knowledge.

### Implementation for User Story 5

- [X] T034 [US5] Write project README with problem framing, architecture, MVP scope, prerequisites, live quickstart, replay quickstart, dashboard guide, cleanup command, limitations, and Wikimedia validation findings from `specs/001-wikistream-mvp-slice/research.md` in `README.md`
- [X] T035 [US5] Add Mermaid or text architecture diagram for EventStreams → Redpanda → processor → snapshots → Streamlit in `README.md`
- [X] T036 [US5] Document environment variables and local port expectations in `.env.example`
- [X] T037 [US5] Document replay sample provenance, expected signal domain, and expected data-quality counts in `data/replay/README.md`

### Validation for User Story 5

- [X] T038 [US5] Manually audit reviewer-facing documentation against FR-015/SC-009: confirm README covers purpose, problem framing, observability solution, MVP scope, local run path, dashboard usage, replay mode, data-quality behavior, responsible-use boundaries, known limitations, dashboard URL, cleanup command, and local ports; record any gaps or validation notes in `specs/001-wikistream-mvp-slice/quickstart.md`

**Checkpoint**: Reviewer-facing documentation supports running and interpreting the MVP independently.

---

## Phase 5: User Story 2 - Inspect an Explainable Bot Spike Signal (Priority: P2)

**Goal**: A reviewer can inspect a domain-level bot spike signal with current-vs-baseline comparison and careful limitations.

**Independent Test**: Feed live or replay data with a clear domain-level bot spike and verify the dashboard shows spike magnitude, windows, thresholds, optional top bot labels, and non-accusatory limitation text.

### Tests for User Story 2

- [X] T039 [P] [US2] Add bot spike detection tests for normal spike, no-signal case, zero-baseline label, thresholds, and top-3 bot label context in `tests/unit/test_signals.py`
- [ ] T040 [P] [US2] Add responsible-language tests for bot spike wording in `tests/unit/test_responsible_language.py`

### Implementation for User Story 2

- [ ] T041 [US2] Implement domain-level bot spike detector with 5-minute current window, previous 30-minute baseline, 20-event minimum, 3.0x threshold, and zero-baseline handling in `src/wikistream_observatory/signals.py`
- [ ] T042 [US2] Implement non-accusatory bot spike wording and mandatory limitations text in `src/wikistream_observatory/signals.py`
- [ ] T043 [US2] Extend processor loop to compute bot spike signals and write `bot_spike_signals` snapshots in `services/processor/wikistream_processor/main.py`
- [ ] T044 [US2] Add dashboard data-loading functions for bot spike snapshots and no-signal empty state in `services/dashboard/app/data.py`
- [ ] T045 [US2] Implement Streamlit bot spike signal section with domain, current count, baseline, ratio/category, windows, threshold context, optional top bot labels, and limitation text in `services/dashboard/app/main.py`
- [ ] T046 [US2] Add bot spike snapshot contract fixtures for dashboard rendering in `tests/fixtures/bot_spike_signals.parquet`
- [ ] T047 [US2] Verify bot spike signal behavior against `contracts/dashboard-contract.md` and record validation notes in `specs/001-wikistream-mvp-slice/quickstart.md`

**Checkpoint**: User Story 2 works independently with either live spike data or controlled replay fixtures.

---

## Phase 6: User Story 3 - Demonstrate with Sample or Replay Data (Priority: P3)

**Goal**: A reviewer can run replay mode using bundled representative sample data that populates metrics and a known bot spike quickly.

**Independent Test**: Run `WIKISTREAM_MODE=replay docker compose up --build`, open the dashboard, and verify replay-labeled metrics and at least one expected bot spike appear within 2 minutes.

### Tests for User Story 3

- [ ] T048 [P] [US3] Add replay data parsing tests for wrapper records, plain RecentChanges-like records, malformed lines, pacing metadata, and source mode in `tests/unit/test_replay.py`
- [ ] T049 [P] [US3] Add end-to-end replay pipeline integration test asserting overview metrics, expected signal domain, and quality counts in `tests/integration/test_replay_pipeline.py`

### Implementation for User Story 3

- [ ] T050 [US3] Create bundled representative JSONL sample with normal activity, a known bot spike, missing-field examples, and malformed/rejected examples in `data/replay/recentchange_sample.jsonl`
- [ ] T051 [US3] Implement replay reader and publisher preserving event order and labeling `source_mode=replay` in `services/ingestor/wikistream_ingestor/replay.py`
- [ ] T052 [US3] Route ingestor startup between live EventStreams and replay publisher based on `WIKISTREAM_MODE` in `services/ingestor/wikistream_ingestor/main.py`
- [ ] T053 [US3] Ensure processor writes replay-labeled snapshots and flushes final replay snapshots at completion in `services/processor/wikistream_processor/main.py`
- [ ] T054 [US3] Update dashboard freshness/status behavior so replay data is never presented as current live activity in `services/dashboard/app/main.py`
- [ ] T055 [US3] Verify replay-mode quickstart and record expected sample outputs in `specs/001-wikistream-mvp-slice/quickstart.md`

**Checkpoint**: User Story 3 provides a deterministic demo path independent of live stream availability.

---

## Phase 7: User Story 4 - Understand Data Quality and Limitations (Priority: P4)

**Goal**: A reviewer sees malformed/rejected counts, missing-field counts, freshness behavior, and limitations for metrics/signals.

**Independent Test**: Feed replay fixtures with malformed and missing-field events and verify separate counts plus explanatory dashboard/documentation text.

### Tests for User Story 4

- [ ] T056 [P] [US4] Add data-quality classification tests for malformed JSON, rejected missing required fields, accepted missing optional fields, and timestamp issues in `tests/unit/test_quality.py`
- [ ] T057 [P] [US4] Add freshness classification tests for live fresh, live stale, no-data, and replay status in `tests/unit/test_freshness.py`

### Implementation for User Story 4

- [ ] T058 [US4] Implement data-quality classification and counters for malformed/rejected, missing-field, accepted, and timestamp fallback records in `src/wikistream_observatory/quality.py`
- [ ] T059 [US4] Extend processor to persist `data_quality_counts` snapshots with latest observed event time and freshness status inputs in `services/processor/wikistream_processor/main.py`
- [ ] T060 [US4] Implement dashboard data-quality section with separate malformed/rejected and missing-field counts plus explanatory notes in `services/dashboard/app/main.py`
- [ ] T061 [US4] Add data-quality and derived-signal limitation text to user-facing documentation in `README.md`

**Checkpoint**: User Story 4 makes reliability and interpretation limits visible and independently testable.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Validate the whole MVP, improve reviewer ergonomics, and ensure constitution compliance.

- [ ] T062 [P] Add Makefile targets for `make test`, `make up`, `make replay`, `make down`, and `make clean-snapshots` in `Makefile`
- [ ] T063 [P] Add a lightweight local run helper for live and replay modes in `bin/wikistream-dev`
- [ ] T064 Run unit and integration tests and fix discovered issues in `tests/unit/` and `tests/integration/`
- [ ] T065 Run Docker Compose live quickstart validation and fix discovered issues in `compose.yaml`
- [ ] T066 Run Docker Compose replay quickstart validation and fix discovered issues in `data/replay/recentchange_sample.jsonl`
- [ ] T067 Validate the MVP processes at least 300 RecentChanges events per minute with bounded memory and summarized dashboard output using replay or synthetic fixtures in `tests/integration/test_throughput.py`
- [ ] T068 Assert at least 95% handling/rejection coverage for intentionally malformed or missing-field replay fixtures in `tests/integration/test_replay_pipeline.py`
- [ ] T069 Validate restart/idempotence behavior by rerunning replay or restarting processor and checking deterministic event IDs prevent unsafe duplicate metrics/signals in `tests/integration/test_restart_idempotence.py`
- [ ] T070 Review all user-facing text for responsible-observability wording and remove accusation-oriented language in `README.md` and `services/dashboard/app/main.py`
- [ ] T071 Update project state after implementation readiness in `STATE.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories.
- **User Stories (Phase 3+)**: Depend on Foundational completion.
- **Polish (Phase 8)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational; no dependency on other user stories; suggested MVP scope.
- **User Story 5 (P1)**: Can start after Foundational; documentation may be refined as later stories land.
- **User Story 2 (P2)**: Can start after Foundational and uses shared snapshots/dashboard components from US1 when available.
- **User Story 3 (P3)**: Can start after Foundational and is most useful after US1 and US2 exist, but replay ingestion is independently implementable.
- **User Story 4 (P4)**: Can start after Foundational; integrates with normalization, processor snapshots, and dashboard.

### Within Each User Story

- Tests are listed first and should be written before implementation.
- Shared models/config/storage precede services.
- Core transformation logic precedes processor integration.
- Processor snapshot outputs precede dashboard rendering.
- Story checkpoint validates independent behavior before moving to the next priority.

### Dependency Graph

```text
Phase 1 Setup
  -> Phase 2 Foundational
      -> US1 Live Activity Overview (MVP)
      -> US5 Documentation and Usage
      -> US2 Bot Spike Signal
      -> US3 Replay Demo
      -> US4 Data Quality and Limitations
  -> Phase 8 Polish after selected stories
```

Recommended sequential delivery: Setup → Foundational → US1 → US5 → US2 → US3 → US4 → Polish.

---

## Parallel Opportunities

- Setup tasks T003, T004, T006, T007, T008, T009, and T010 can run in parallel after T001 creates directories.
- Foundational tasks T012, T013, and T014 can run in parallel with each other after T011 is sketched.
- US1 tests T021, T022, and T023 can run in parallel; dashboard data work T029 can run after snapshot contracts are known while ingestor work T026/T027 proceeds.
- US5 documentation work T034-T037 should be implemented first; T038 is a manual acceptance audit after the reviewer-facing docs exist.
- US2 tests T039 and T040 can run in parallel; dashboard fixture task T046 can run once the signal model is defined.
- US3 tests T048 and T049 can run in parallel; replay data T050 and replay publisher T051 can be developed in parallel after replay contract review.
- US4 tests T056 and T057 can run in parallel before quality implementation.
- Polish tasks T062 and T063 can run in parallel because they touch different files.

---

## Parallel Example: User Story 1

```bash
Task: "T021 [P] [US1] Add normalization tests for required fields, optional missing fields, bot default behavior, and timestamp fallback in tests/unit/test_normalization.py"
Task: "T022 [P] [US1] Add activity-window aggregation tests for events per minute, top domains, event types, and bot/non-bot share in tests/unit/test_windows.py"
Task: "T023 [P] [US1] Add live pipeline integration smoke test using a fake raw Kafka payload and snapshot output in tests/integration/test_live_pipeline_smoke.py"
```

## Parallel Example: User Story 2

```bash
Task: "T039 [P] [US2] Add bot spike detection tests for normal spike, no-signal case, zero-baseline label, thresholds, and top-3 bot label context in tests/unit/test_signals.py"
Task: "T040 [P] [US2] Add responsible-language tests for bot spike wording in tests/unit/test_responsible_language.py"
Task: "T046 [US2] Add bot spike snapshot contract fixtures for dashboard rendering in tests/fixtures/bot_spike_signals.parquet"
```

## Parallel Example: User Story 3

```bash
Task: "T048 [P] [US3] Add replay data parsing tests for wrapper records, plain RecentChanges-like records, malformed lines, pacing metadata, and source mode in tests/unit/test_replay.py"
Task: "T050 [US3] Create bundled representative JSONL sample with normal activity, a known bot spike, missing-field examples, and malformed/rejected examples in data/replay/recentchange_sample.jsonl"
Task: "T051 [US3] Implement replay reader and publisher preserving event order and labeling source_mode=replay in services/ingestor/wikistream_ingestor/replay.py"
```

## Parallel Example: User Story 4

```bash
Task: "T056 [P] [US4] Add data-quality classification tests for malformed JSON, rejected missing required fields, accepted missing optional fields, and timestamp issues in tests/unit/test_quality.py"
Task: "T057 [P] [US4] Add freshness classification tests for live fresh, live stale, no-data, and replay status in tests/unit/test_freshness.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1.
4. Complete Phase 4: User Story 5 enough to document live-mode quickstart.
5. **STOP and VALIDATE**: Run `pytest` for US1 tests and validate `docker compose up --build` shows live dashboard metrics within 5 minutes.

### Incremental Delivery

1. Setup + Foundational → shared infrastructure ready.
2. US1 → live activity overview MVP.
3. US5 → reviewer-facing documentation for purpose and usage.
4. US2 → non-trivial bot spike observability signal.
5. US3 → deterministic replay demo path.
6. US4 → visible data-quality counts and limitations.
7. Polish → full quickstart validation and cleanup ergonomics.

### Parallel Team Strategy

1. Team completes Setup and Foundational together.
2. After Foundational:
   - Developer A: US1 live overview.
   - Developer B: US5 documentation.
   - Developer C: US2 signal logic.
   - Developer D: US3 replay path.
   - Developer E: US4 quality/freshness visibility.
3. Integrate through shared snapshot contracts and validate each story independently.

---

## Notes

- [P] tasks = different files and no dependency on incomplete same-file changes.
- [US1] through [US5] labels map to user stories in `spec.md`.
- All user-story tasks include exact file paths for immediate execution.
- Tests should fail before corresponding implementation tasks are completed.
- Preserve responsible observability: domain-level signals, careful bot-label context, and explicit limitations.
- Avoid scope creep: no cloud, Kubernetes, historical backfill, complex ML, enforcement, or extra signals in this MVP.
