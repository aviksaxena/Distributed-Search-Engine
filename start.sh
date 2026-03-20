#!/bin/bash

# Distributed Search Engine - Startup Script
# This script starts all necessary services for the search engine

set -e

echo "🚀 Starting Distributed Search Engine..."
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "✅ .env file created. Please review and update if needed."
fi

# Start Docker services
echo "📦 Starting Docker services (Redis, Elasticsearch, FastAPI)..."
docker-compose up -d

# Wait for services to be healthy
echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if services are running
BACKEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health || echo "000")
ES_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:9200/_cluster/health || echo "000")

if [ "$BACKEND_HEALTH" = "200" ]; then
    echo "✅ Backend API is healthy"
else
    echo "⚠️  Backend API not responding yet (code: $BACKEND_HEALTH)"
fi

if [ "$ES_HEALTH" = "200" ]; then
    echo "✅ Elasticsearch is healthy"
else
    echo "⚠️  Elasticsearch not responding yet (code: $ES_HEALTH)"
fi

echo ""
echo "✅ Services started!"
echo ""
echo "📋 Service URLs:"
echo "  • Backend API:        http://localhost:8000"
echo "  • API Docs:           http://localhost:8000/docs"
echo "  • Elasticsearch:      http://localhost:9200"
echo "  • Redis:              localhost:6379"
echo ""
echo "Next steps:"
echo "  1. In another terminal, run: npm run dev"
echo "  2. Open http://localhost:3000 in your browser"
echo "  3. Start crawling websites or searching"
echo ""
echo "To view logs:"
echo "  • All:                docker-compose logs -f"
echo "  • Backend only:       docker-compose logs -f backend"
echo "  • Elasticsearch:      docker-compose logs -f elasticsearch"
echo "  • Redis:              docker-compose logs -f redis"
echo ""
echo "To stop services:"
echo "  • docker-compose down"
echo ""
