.PHONY: up down test seed logs
up:
docker compose up -d
down:
docker compose down -v
test:
docker compose exec api pytest -v
seed:
docker compose exec api python scripts/seed.py
logs:
docker compose logs -f
