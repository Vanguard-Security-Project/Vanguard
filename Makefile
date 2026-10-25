.PHONY: up down logs build test cli clean health

up:
	docker compose up --build -d
	@echo "Dashboard: http://localhost:8000"
	@echo "Neo4j:     http://localhost:7474 (neo4j / vanguard-local)"

down:
	docker compose down

logs:
	docker compose logs -f backend

build:
	docker compose build

health:
	@curl -s http://localhost:8000/api/health | python -m json.tool

test:
	python run_tests.py -v

cli:
	@test -n "$(FILE)" || (echo "Usage: make cli FILE=path/to/export.zip" && exit 1)
	python cli.py pipeline $(FILE)

clean:
	docker compose down -v
	rm -rf data/ evidence/ plans/ scripts/generated/
