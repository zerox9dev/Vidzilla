.PHONY: help install install-dev test test-cov lint format clean run docker-build docker-run setup-dev

# Default target
help:
	@echo "Vidzilla Development Commands"
	@echo "============================="
	@echo ""
	@echo "Setup:"
	@echo "  install      Install production dependencies"
	@echo "  install-dev  Install development dependencies"
	@echo "  setup-dev    Complete development environment setup"
	@echo ""
	@echo "Development:"
	@echo "  run          Run the bot locally"
	@echo "  test         Run tests"
	@echo "  test-cov     Run tests with coverage"
	@echo "  lint         Run linting checks"
	@echo "  format       Format code with black and isort"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build Build Docker image"
	@echo "  docker-run   Run with Docker Compose"
	@echo "  docker-stop  Stop Docker containers"
	@echo ""
	@echo "Maintenance:"
	@echo "  clean        Clean temporary files"
	@echo "  logs         Show bot logs"

# Installation
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt
	pre-commit install

setup-dev: install-dev
	@echo "Setting up development environment..."
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "✅ Created .env file from .env.example"; \
		echo "⚠️  Please edit .env with your configuration"; \
	fi
	@mkdir -p temp_videos/compression logs
	@echo "✅ Created necessary directories"
	@echo "🚀 Development environment ready!"

# Development
run:
	@if [ ! -f .env ]; then \
		echo "❌ .env file not found. Run 'make setup-dev' first."; \
		exit 1; \
	fi
	python bot.py

test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=utils --cov=handlers --cov-report=html --cov-report=term

lint:
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=100 --statistics
	black --check --line-length=100 .
	isort --check-only --profile black --line-length=100 .
	bandit -r . -f json -o bandit-report.json || true
	mypy . --ignore-missing-imports || true

format:
	black --line-length=100 .
	isort --profile black --line-length=100 .

# Docker
docker-build:
	docker build -t vidzilla:latest .

docker-run:
	@if [ ! -f .env ]; then \
		echo "❌ .env file not found. Run 'make setup-dev' first."; \
		exit 1; \
	fi
	docker-compose up -d

docker-stop:
	docker-compose down

docker-logs:
	docker-compose logs -f vidzilla

# Maintenance
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.log" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf temp_videos/*
	rm -rf logs/*
	@echo "✅ Cleaned temporary files"

logs:
	@if [ -f temp_videos/compression.log ]; then \
		tail -f temp_videos/compression.log; \
	else \
		echo "No log file found. Start the bot first."; \
	fi

# Database
db-init:
	@echo "Initializing MongoDB..."
	@if command -v mongosh >/dev/null 2>&1; then \
		mongosh --file mongo-init.js; \
	elif command -v mongo >/dev/null 2>&1; then \
		mongo < mongo-init.js; \
	else \
		echo "❌ MongoDB client not found. Install mongosh or mongo."; \
	fi

# Release
release-check:
	@echo "Pre-release checks..."
	make test
	make lint
	@echo "✅ All checks passed!"

# Health check
health:
	@echo "Checking system health..."
	@python -c "
import sys
try:
    import ffmpeg
    print('✅ FFmpeg available')
except ImportError:
    print('❌ FFmpeg not available')
    sys.exit(1)

try:
    from pymongo import MongoClient
    print('✅ MongoDB driver available')
except ImportError:
    print('❌ MongoDB driver not available')
    sys.exit(1)

print('🚀 System health check passed!')
"

# Development server with auto-reload
dev:
	@echo "Starting development server with auto-reload..."
	@pip install watchdog
	@python -c "
import time
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class RestartHandler(FileSystemEventHandler):
    def __init__(self):
        self.process = None
        self.restart()
    
    def restart(self):
        if self.process:
            self.process.terminate()
            self.process.wait()
        print('🔄 Restarting bot...')
        self.process = subprocess.Popen(['python', 'bot.py'])
    
    def on_modified(self, event):
        if event.src_path.endswith('.py'):
            print(f'📝 File changed: {event.src_path}')
            self.restart()

handler = RestartHandler()
observer = Observer()
observer.schedule(handler, '.', recursive=True)
observer.start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    observer.stop()
    if handler.process:
        handler.process.terminate()
observer.join()
"