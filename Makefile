.PHONY: test up replay down clean-snapshots

test:
	PYTHONPATH=. uv run pytest

up:
	docker compose up --build

replay:
	WIKISTREAM_MODE=replay docker compose up --build

down:
	docker compose down

clean-snapshots:
	rm -rf data/snapshots/*
