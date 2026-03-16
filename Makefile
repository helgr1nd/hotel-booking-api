.PHONY: up down logs restart build migrate test lint clean

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

restart:
	docker-compose restart

build:
	docker-compose build

migrate:
	docker-compose exec api alembic upgrade head

migrate-create:
	docker-compose exec api alembic revision --autogenerate -m "$(message)"

test:
	docker-compose exec api pytest -v

test-cov:
	docker-compose exec api pytest --cov=app --cov-report=html

lint:
	docker-compose exec api black app tests
	docker-compose exec api flake8 app tests

clean:
	docker-compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache htmlcov .coverage

shell:
	docker-compose exec api python

db-shell:
	docker-compose exec db psql -U postgres -d room_booking
