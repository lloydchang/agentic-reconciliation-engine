#!/bin/bash
set -e
# Start Temporal server & Backstage dev server
docker-compose -f backend/docker-compose.yml up -d

echo "Waiting for Temporal server to initialize..."
sleep 5

echo "Starting Go backend..."
export GOCACHE=/tmp/go-cache
export GOTMPDIR=/tmp/go-tmp
mkdir -p $GOCACHE $GOTMPDIR
(cd backend && go run main.go) &
BACKEND_PID=$!

echo "Waiting for backend to bind to :8081..."
until curl -sf http://localhost:8081/api/skills > /dev/null 2>&1 || [ "$((RETRIES++))" -ge 30 ]; do sleep 2; done

cd frontend
export YARN_CACHE_FOLDER=/tmp/yarn-cache
mkdir -p $YARN_CACHE_FOLDER
yarn start
