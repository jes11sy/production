.PHONY: help install dev test coverage clean docker-build docker-up docker-down migrate

help:
	@echo "Доступные команды:"
	@echo "  install      - Установить зависимости"
	@echo "  dev          - Запустить в режиме разработки"
	@echo "  test         - Запустить тесты"
	@echo "  coverage     - Запустить тесты с покрытием"
	@echo "  clean        - Очистить временные файлы"
	@echo "  docker-build - Собрать Docker образ"
	@echo "  docker-up    - Запустить через Docker Compose"
	@echo "  docker-down  - Остановить Docker Compose"
	@echo "  migrate      - Применить миграции"

install:
	pip install -r requirements.txt

dev:
	python run.py

test:
	pytest

coverage:
	pytest --cov=app --cov-report=html --cov-report=term

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .coverage

docker-build:
	cd deployment && docker-compose build

docker-up:
	cd deployment && docker-compose up -d

docker-down:
	cd deployment && docker-compose down

migrate:
	alembic -c config/alembic.ini upgrade head

migrate-create:
	alembic -c config/alembic.ini revision --autogenerate -m "$(MSG)" 