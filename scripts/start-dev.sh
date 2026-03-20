#!/bin/bash

# Start development environment with all services

echo "🚀 Starting Distributed Search Engine..."
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose not found. Please install Docker Compose first."
    exit 1
fi

# Start services
echo "📦 Starting Docker services (Redis, Elasticsearch, Backend)..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 5

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    echo "✅ Services started successfully!"
    echo ""
    echo "🔗 Service URLs:"
    echo "   Backend API: http://localhost:8000"
    echo "   Elasticsearch: http://localhost:9200"
    echo "   Redis: localhost:6379"
    echo ""
    echo "📚 API Docs: http://localhost:8000/docs"
    echo ""
    echo "📊 Run frontend with: npm run dev"
    echo ""
    echo "To stop services: docker-compose down"
else
    echo "❌ Failed to start services"
    exit 1
fi
