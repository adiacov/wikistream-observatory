.PHONY: test build up replay down clean-snapshots prune-images

HOST_UID ?= $(shell id -u)
HOST_GID ?= $(shell id -g)
COMPOSE := HOST_UID=$(HOST_UID) HOST_GID=$(HOST_GID) docker compose

test:
	PYTHONPATH=. uv run pytest

build:
	$(COMPOSE) build

up:
	$(COMPOSE) up

replay:
	WIKISTREAM_MODE=replay $(COMPOSE) up

down:
	$(COMPOSE) down

clean-snapshots:
	mkdir -p data/snapshots
	docker run --rm -v "$(CURDIR)/data/snapshots:/snapshots" busybox sh -c 'rm -rf /snapshots/*'

prune-images:
	docker image prune
