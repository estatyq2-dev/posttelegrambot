#!/bin/bash

# News Relay Bot Setup Script

set -e

echo "🚀 Setting up News Relay Bot..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cat > .env << EOF
# Telegram Bot Configuration
TG_BOT_TOKEN=YOUR_BOT_TOKEN_HERE
TG_API_ID=YOUR_API_ID_HERE
TG_API_HASH=YOUR_API_HASH_HERE
TG_SESSION_PATH=.tg_session/session.session

# OpenAI / GPT Configuration
OPENAI_API_KEY=YOUR_OPENAI_KEY_HERE
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini

# Database Configuration
DATABASE_URL=postgresql+asyncpg://news_relay:password@postgres:5432/news_relay

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# Application Configuration
TIMEZONE=Europe/Kyiv
LOG_LEVEL=INFO

# Worker Configuration
RQ_QUEUE_INGEST=ingest
RQ_QUEUE_REWRITE=rewrite
RQ_QUEUE_PUBLISH=publish

# Publishing Configuration
DEFAULT_PUBLISH_INTERVAL_MINUTES=60
MAX_POST_LENGTH=4096
EOF
    echo "⚠️  Please edit .env file with your actual tokens and credentials"
    exit 1
else
    echo "✅ .env file found"
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs
mkdir -p media_storage
mkdir -p .tg_session

# Build and start containers
echo "🐳 Building and starting Docker containers..."
docker-compose up -d --build

echo "⏳ Waiting for database to be ready..."
sleep 10

# Run migrations
echo "🗄️  Running database migrations..."
docker-compose exec -T bot alembic upgrade head

echo "✅ Setup complete!"
echo ""
echo "📊 Status:"
docker-compose ps
echo ""
echo "📝 View logs:"
echo "  Bot:    docker-compose logs -f bot"
echo "  Worker: docker-compose logs -f worker"
echo ""
echo "🛑 To stop:"
echo "  docker-compose down"
echo ""
echo "🎉 Your bot is ready! Open Telegram and send /start to your bot."

