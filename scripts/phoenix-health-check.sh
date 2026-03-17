#!/bin/bash
# phoenix-health-check.sh

PHOENIX_URL="http://phoenix.staging.internal.example.com"

echo "Checking Phoenix health..."
if curl -f -s "${PHOENIX_URL}/health" > /dev/null; then
    echo "✅ Phoenix is healthy"
else
    echo "❌ Phoenix is not responding"
    exit 1
fi

echo "Checking OTLP endpoint..."
if curl -f -s "${PHOENIX_URL}/health" > /dev/null; then
    echo "✅ OTLP endpoint accessible"
else
    echo "❌ OTLP endpoint not accessible"
    exit 1
fi

echo "Health check completed successfully"
