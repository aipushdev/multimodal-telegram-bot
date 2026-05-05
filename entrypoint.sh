#!/bin/sh
set -e

echo "Running migrations..."
uv run python migrate.py

echo "Starting bot..."
exec uv run python bot.py
