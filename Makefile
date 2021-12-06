up:
	docker compose up --build

down:
	docker compose down

shell:
	docker exec -it tsl_event_etl bash

format:
	docker exec tsl_event_etl python -m black -S --line-length 79 .

isort:
	docker exec tsl_event_etl isort .

type:
	docker exec tsl_event_etl mypy --ignore-missing-imports /app

lint:
	docker exec tsl_event_etl flake8 /app

ci: isort format type lint
