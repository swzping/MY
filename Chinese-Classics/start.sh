#!/bin/bash

# Start all services for Chinese-Classics project
# Usage: ./start.sh [command]
# Commands: up (default), up-d (detached), down, restart, logs, status

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Check if .env exists, create from example if not
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        echo "Creating .env from .env.example..."
        cp .env.example .env
        echo "Please edit .env and set your OPENAI_API_KEY"
    else
        echo "Error: .env.example not found"
        exit 1
    fi
fi

# Load environment variables
source .env

# Display status
show_status() {
    echo ""
    echo "=== Chinese-Classics Services ==="
    echo "Frontend:     http://localhost:5173 (dev) / http://localhost:80 (prod)"
    echo "Backend API:  http://localhost:8000"
    echo "API Docs:     http://localhost:8000/docs"
    echo "Milvus UI:    http://localhost:9091"
    echo "PostgreSQL:   localhost:5432"
    echo "Redis:        localhost:6379"
    echo "==================================="
    echo ""
}

# Parse command
COMMAND="${1:-up}"

case "$COMMAND" in
    up)
        echo "Starting all services..."
        docker compose up
        ;;
    up-d|up-d)
        echo "Starting all services in detached mode..."
        docker compose up -d
        show_status
        ;;
    down)
        echo "Stopping all services..."
        docker compose down
        ;;
    restart)
        echo "Restarting all services..."
        docker compose restart
        show_status
        ;;
    logs)
        docker compose logs -f
        ;;
    status)
        docker compose ps
        show_status
        ;;
    rebuild)
        echo "Rebuilding and starting all services..."
        docker compose up -d --build
        show_status
        ;;
    *)
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  up       - Start all services (attach to logs)"
        echo "  up-d     - Start all services in detached mode"
        echo "  down     - Stop all services"
        echo "  restart  - Restart all services"
        echo "  logs     - View logs (follow mode)"
        echo "  status   - Show service status"
        echo "  rebuild  - Rebuild and start all services"
        exit 1
        ;;
esac
