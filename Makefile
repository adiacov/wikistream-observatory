.PHONY: test build up replay down clean-snapshots prune-images

test:
	PYTHONPATH=. uv run pytest

build:
	docker compose build

up:
	docker compose up

replay:
	WIKISTREAM_MODE=replay docker compose up

down:
	docker compose down

clean-snapshots:
	rm -rf data/snapshots/*

prune-images:
	docker image prune
