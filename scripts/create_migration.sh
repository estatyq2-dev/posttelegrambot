#!/bin/bash

# Script to create database migration

if [ -z "$1" ]; then
    echo "Usage: ./scripts/create_migration.sh <migration_message>"
    exit 1
fi

echo "Creating migration: $1"

docker-compose exec bot alembic revision --autogenerate -m "$1"

echo "✅ Migration created"
echo "📝 Review the migration file in app/db/migrations/versions/"
echo "🚀 Apply with: docker-compose exec bot alembic upgrade head"

