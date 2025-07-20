# Vidzilla Project Makefile

.PHONY: help install test lint format wiki-sync wiki-preview clean

# Default target
help: ## Show this help message
	@echo "🎬 Vidzilla - Social Media Video Downloader Bot"
	@echo "================================================"
	@echo ""
	@echo "Available commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""

# Development setup
install: ## Install dependencies
	@echo "📦 Installing dependencies..."
	python -m pip install --upgrade pip
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	@echo "✅ Dependencies installed"

install-dev: install ## Install development dependencies
	@echo "🛠️ Setting up development environment..."
	pre-commit install
	@echo "✅ Development environment ready"

# Testing
test: ## Run all tests
	@echo "🧪 Running tests..."
	pytest tests/ -v

test-cov: ## Run tests with coverage
	@echo "🧪 Running tests with coverage..."
	pytest tests/ -v --cov=utils --cov=handlers --cov-report=html --cov-report=xml

test-fast: ## Run fast tests only
	@echo "⚡ Running fast tests..."
	pytest tests/ -v -m "not slow"

# Code quality
lint: ## Run linting
	@echo "🔍 Running linters..."
	flake8 --max-line-length=100 .
	mypy .
	bandit -r . -f json -o bandit-report.json

format: ## Format code
	@echo "🎨 Formatting code..."
	black --line-length=100 .
	isort --profile black --line-length=100 .
	@echo "✅ Code formatted"

format-check: ## Check code formatting
	@echo "🔍 Checking code formatting..."
	black --check --line-length=100 .
	isort --check-only --profile black --line-length=100 .

# Wiki management
wiki-sync: ## Sync wiki to GitHub
	@echo "📚 Syncing wiki to GitHub..."
	@if [ -f scripts/sync-wiki.sh ]; then \
		chmod +x scripts/sync-wiki.sh && ./scripts/sync-wiki.sh; \
	else \
		echo "❌ Wiki sync script not found"; \
		exit 1; \
	fi

wiki-preview: ## Preview wiki locally
	@echo "👀 Starting wiki preview server..."
	@if command -v mkdocs >/dev/null 2>&1; then \
		mkdocs serve; \
	elif command -v grip >/dev/null 2>&1; then \
		echo "📖 Starting Grip server for wiki/Home.md..."; \
		grip wiki/Home.md; \
	else \
		echo "📝 Install mkdocs or grip for wiki preview:"; \
		echo "  pip install mkdocs mkdocs-material"; \
		echo "  # or"; \
		echo "  pip install grip"; \
	fi

wiki-stats: ## Show wiki statistics
	@echo "📊 Wiki Statistics"
	@echo "=================="
	@echo "📄 Total pages: $$(find wiki -name "*.md" | wc -l)"
	@echo "📝 Total lines: $$(cat wiki/*.md | wc -l)"
	@echo "💾 Total size: $$(du -sh wiki | cut -f1)"
	@echo "📅 Last modified: $$(find wiki -name "*.md" -exec stat -f "%Sm %N" -t "%Y-%m-%d %H:%M" {} \; | sort -r | head -1)"

# Docker operations
docker-build: ## Build Docker image
	@echo "🐳 Building Docker image..."
	docker build -t vidzilla:latest .

docker-run: ## Run Docker container
	@echo "🐳 Running Docker container..."
	docker run -d --name vidzilla --env-file .env vidzilla:latest

docker-logs: ## Show Docker logs
	@echo "📋 Docker logs:"
	docker logs -f vidzilla

docker-stop: ## Stop Docker container
	@echo "🛑 Stopping Docker container..."
	docker stop vidzilla
	docker rm vidzilla

# Database operations
db-backup: ## Backup MongoDB database
	@echo "💾 Creating database backup..."
	@if [ -z "$$MONGODB_URI" ]; then \
		echo "❌ MONGODB_URI not set"; \
		exit 1; \
	fi
	mongodump --uri="$$MONGODB_URI" --out=backup/$$(date +%Y%m%d_%H%M%S)
	@echo "✅ Backup created"

db-restore: ## Restore MongoDB database (specify BACKUP_DIR)
	@echo "📥 Restoring database..."
	@if [ -z "$$BACKUP_DIR" ]; then \
		echo "❌ Please specify BACKUP_DIR: make db-restore BACKUP_DIR=backup/20240101_120000"; \
		exit 1; \
	fi
	mongorestore --uri="$$MONGODB_URI" --drop "$$BACKUP_DIR"
	@echo "✅ Database restored"

# Deployment
deploy-staging: ## Deploy to staging
	@echo "🚀 Deploying to staging..."
	# Add your staging deployment commands here

deploy-prod: ## Deploy to production
	@echo "🚀 Deploying to production..."
	# Add your production deployment commands here

# Monitoring
logs: ## Show application logs
	@echo "📋 Application logs:"
	@if [ -f logs/bot.log ]; then \
		tail -f logs/bot.log; \
	else \
		echo "❌ Log file not found. Is the bot running?"; \
	fi

logs-compression: ## Show compression logs
	@echo "📋 Compression logs:"
	@if [ -f compression.log ]; then \
		tail -f compression.log; \
	else \
		echo "❌ Compression log file not found"; \
	fi

status: ## Show system status
	@echo "📊 System Status"
	@echo "==============="
	@echo "🐍 Python: $$(python --version)"
	@echo "📦 Pip packages: $$(pip list | wc -l) installed"
	@echo "💾 Disk usage: $$(df -h . | tail -1 | awk '{print $$5}') used"
	@echo "🧠 Memory: $$(free -h | grep '^Mem:' | awk '{print $$3 "/" $$2}') used" 2>/dev/null || echo "🧠 Memory: N/A (not Linux)"
	@echo "📁 Temp files: $$(find temp_videos -type f 2>/dev/null | wc -l) files" 2>/dev/null || echo "📁 Temp files: 0 files"

# Cleanup
clean: ## Clean temporary files
	@echo "🧹 Cleaning temporary files..."
	rm -rf temp_videos/*
	rm -rf __pycache__/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf *.log
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete
	@echo "✅ Cleanup completed"

clean-all: clean ## Clean everything including dependencies
	@echo "🧹 Deep cleaning..."
	rm -rf .myebv/
	rm -rf node_modules/
	rm -rf dist/
	rm -rf build/
	@echo "✅ Deep cleanup completed"

# Security
security-check: ## Run security checks
	@echo "🔒 Running security checks..."
	bandit -r . -f json -o bandit-report.json
	safety check
	@echo "✅ Security check completed"

# Release
version: ## Show current version
	@echo "📋 Version Information"
	@echo "====================="
	@echo "🏷️ Git tag: $$(git describe --tags --abbrev=0 2>/dev/null || echo 'No tags')"
	@echo "📝 Git commit: $$(git rev-parse --short HEAD)"
	@echo "🌿 Git branch: $$(git branch --show-current)"
	@echo "📅 Last commit: $$(git log -1 --format='%cd' --date=short)"

release-check: ## Check if ready for release
	@echo "🔍 Release readiness check..."
	@echo "✅ Running tests..."
	@make test-fast
	@echo "✅ Checking code format..."
	@make format-check
	@echo "✅ Running security checks..."
	@make security-check
	@echo "✅ Checking wiki sync..."
	@make wiki-stats
	@echo "🎉 Ready for release!"

# Development helpers
dev-setup: install-dev ## Complete development setup
	@echo "🛠️ Setting up development environment..."
	mkdir -p temp_videos/compression
	mkdir -p logs
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "📝 Created .env file from template"; \
		echo "⚠️  Please edit .env with your configuration"; \
	fi
	@echo "✅ Development setup completed"

dev-run: ## Run bot in development mode
	@echo "🚀 Starting bot in development mode..."
	python bot.py

dev-test-watch: ## Run tests in watch mode
	@echo "👀 Running tests in watch mode..."
	@if command -v pytest-watch >/dev/null 2>&1; then \
		ptw tests/; \
	else \
		echo "📦 Install pytest-watch: pip install pytest-watch"; \
		echo "🔄 Running tests once..."; \
		make test; \
	fi