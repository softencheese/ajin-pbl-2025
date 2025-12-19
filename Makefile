# Makefile for RFID Logistics Tracking System

.PHONY: help setup clean deep-clean fclean up down logs

help:
	@echo "Available commands:"
	@echo "  make setup       - Initialize environment (create .env, install dependencies)"
	@echo "  make up          - Start all services with Docker Compose"
	@echo "  make down        - Stop all services"
	@echo "  make logs        - View service logs"
	@echo "  make clean       - Remove temporary files (__pycache__, etc.)"
	@echo "  make deep-clean  - Remove ALL generated files (venv, node_modules, data, .env)"
	@echo "  make test        - Run backend tests"

setup:
	@echo "Initializing environment..."
	@if [ ! -f .env ]; then cp .env.example .env && echo "Created .env"; fi
	@echo "Checking Implementation Directory..."
	@mkdir -p implementation/data/mysql
	@echo "Setup complete. Run 'make up' to start services."

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

test:
	@echo "Running tests..."
	@cd implementation/api && . venv/bin/activate && pytest tests/ -v

test-cov:
	@echo "Running tests with coverage..."
	@cd implementation/api && . venv/bin/activate && pytest tests/ -v --cov=app

clean:
	@echo "Cleaning temporary files..."
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type d -name ".pytest_cache" -exec rm -rf {} +
	@find . -type d -name ".mypy_cache" -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name ".coverage" -delete
	@echo "Clean complete."

deep-clean: clean
	@echo "Performing deep clean (removing data and environments)..."
	@docker-compose down
	@rm -rf implementation/data
	@rm -rf implementation/api/venv
	@rm -rf implementation/frontend/node_modules
	@rm -rf implementation/api/logs
	@rm -rf implementation/backups
	@rm -f .env
	@echo "Deep clean complete. System is factory reset."

fclean: deep-clean


