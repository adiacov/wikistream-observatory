from __future__ import annotations

import pytest

from services.ingestor.wikistream_ingestor.replay import read_replay_records


def test_reads_wrapper_records_with_payload_source_mode_and_pacing_seconds(tmp_path):
    sample = tmp_path / "sample.jsonl"
    sample.write_text(
        '{"source_mode":"replay","pacing_seconds":0.25,"payload":{"meta":{"id":"evt-1","domain":"en.wikipedia.org"},"type":"edit","timestamp":1780639710,"user":"ExampleBot","bot":true}}\n',
        encoding="utf-8",
    )

    records = list(read_replay_records(sample))

    assert len(records) == 1
    assert records[0].source_mode == "replay"
    assert records[0].pacing_seconds == pytest.approx(0.25)
    assert records[0].payload == {
        "meta": {"id": "evt-1", "domain": "en.wikipedia.org"},
        "type": "edit",
        "timestamp": 1780639710,
        "user": "ExampleBot",
        "bot": True,
    }
    assert records[0].malformed is False
    assert records[0].error is None


def test_reads_plain_recentchanges_like_records_as_replay_payloads(tmp_path):
    sample = tmp_path / "sample.jsonl"
    sample.write_text(
        '{"meta":{"id":"evt-2","domain":"commons.wikimedia.org"},"type":"new","timestamp":1780639720,"user":"HumanEditor","bot":false}\n',
        encoding="utf-8",
    )

    records = list(read_replay_records(sample))

    assert len(records) == 1
    assert records[0].source_mode == "replay"
    assert records[0].pacing_seconds == 0
    assert records[0].payload["meta"]["domain"] == "commons.wikimedia.org"
    assert records[0].payload["type"] == "new"
    assert records[0].malformed is False


def test_malformed_lines_are_returned_as_rejected_replay_records_without_stopping(tmp_path):
    sample = tmp_path / "sample.jsonl"
    sample.write_text(
        '\n'.join(
            [
                '{"meta":{"id":"evt-1","domain":"en.wikipedia.org"},"type":"edit"}',
                '{not valid json',
                '{"source_mode":"replay","payload":"not an object"}',
                '{"meta":{"id":"evt-3","domain":"de.wikipedia.org"},"type":"edit"}',
            ]
        )
        + '\n',
        encoding="utf-8",
    )

    records = list(read_replay_records(sample))

    assert [record.line_number for record in records] == [1, 2, 3, 4]
    assert [record.malformed for record in records] == [False, True, True, False]
    assert records[1].payload is None
    assert records[1].raw_line == "{not valid json"
    assert "json" in records[1].error.lower()
    assert records[2].payload is None
    assert "payload" in records[2].error.lower()
    assert records[3].payload["meta"]["domain"] == "de.wikipedia.org"


def test_pacing_metadata_accepts_milliseconds_and_defaults_when_absent(tmp_path):
    sample = tmp_path / "sample.jsonl"
    sample.write_text(
        '\n'.join(
            [
                '{"pacing_ms":150,"payload":{"meta":{"domain":"en.wikipedia.org"},"type":"edit"}}',
                '{"payload":{"meta":{"domain":"fr.wikipedia.org"},"type":"edit"}}',
            ]
        )
        + '\n',
        encoding="utf-8",
    )

    records = list(read_replay_records(sample, default_pacing_seconds=0.05))

    assert records[0].pacing_seconds == pytest.approx(0.15)
    assert records[1].pacing_seconds == pytest.approx(0.05)


def test_source_mode_is_forced_to_replay_for_all_accepted_records(tmp_path):
    sample = tmp_path / "sample.jsonl"
    sample.write_text(
        '\n'.join(
            [
                '{"source_mode":"live","payload":{"meta":{"domain":"en.wikipedia.org"},"type":"edit"}}',
                '{"source_mode":"live","meta":{"domain":"wikidata.org"},"type":"edit"}',
            ]
        )
        + '\n',
        encoding="utf-8",
    )

    records = list(read_replay_records(sample))

    assert [record.source_mode for record in records] == ["replay", "replay"]
    assert records[0].payload["meta"]["domain"] == "en.wikipedia.org"
    assert records[1].payload["meta"]["domain"] == "wikidata.org"
    assert all(record.malformed is False for record in records)
