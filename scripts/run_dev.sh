#!/bin/bash

# Script to run bot in development mode (outside Docker)

set -e

echo "🔧 Running News Relay Bot in development mode..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found"
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Check for required environment variables
if [ -z "$TG_BOT_TOKEN" ]; then
    echo "❌ TG_BOT_TOKEN not set in .env"
    exit 1
fi

# Adjust DATABASE_URL for local development
export DATABASE_URL="postgresql+asyncpg://news_relay:password@localhost:5432/news_relay"
export REDIS_URL="redis://localhost:6379/0"

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install poetry
    poetry install
else
    source venv/bin/activate
fi

# Run migrations
echo "🗄️  Running migrations..."
alembic upgrade head

# Run bot
echo "🚀 Starting bot..."
python -m app.main

