#!/bin/bash
# validate-arize-phoenix-tracing.sh

echo "🔍 Validating Arize Phoenix Tracing Setup"
echo "========================================="

# Check if Phoenix is running
echo "1. Checking Phoenix deployment status..."
kubectl get pods -n staging -l app=arize-phoenix

if [ $? -ne 0 ]; then
    echo "❌ Phoenix deployment not found"
    exit 1
fi

# Check if OTEL collector is running
echo "2. Checking OpenTelemetry collector status..."
kubectl get pods -n staging -l app=otel-collector

if [ $? -ne 0 ]; then
    echo "❌ OpenTelemetry collector not found"
    exit 1
fi

# Check Phoenix health endpoint
echo "3. Testing Phoenix health endpoint..."
PHOENIX_POD=$(kubectl get pods -n staging -l app=arize-phoenix -o jsonpath='{.items[0].metadata.name}')
kubectl exec -n staging $PHOENIX_POD -- curl -f http://localhost:6006/health

if [ $? -ne 0 ]; then
    echo "❌ Phoenix health check failed"
    exit 1
fi

# Check OTLP endpoint accessibility
echo "4. Testing OTLP endpoint..."
kubectl exec -n staging $PHOENIX_POD -- curl -f http://localhost:4317/

if [ $? -ne 0 ]; then
    echo "❌ OTLP endpoint not accessible"
    exit 1
fi

# Generate test trace
echo "5. Generating test trace..."
kubectl run test-trace --image=curlimages/curl --rm -i --restart=Never -- \
  curl -X POST http://arize-phoenix.staging.svc.cluster.local:4318/v1/traces \
  -H "Content-Type: application/json" \
  -d '{
    "resourceSpans": [{
      "resource": {
        "attributes": [{"key": "service.name", "value": {"stringValue": "test-agent"}}]
      },
      "scopeSpans": [{
        "spans": [{
          "traceId": "12345678901234567890123456789012",
          "spanId": "1234567890123456",
          "name": "test-span",
          "kind": 1,
          "startTimeUnixNano": "'$(date +%s%N)'",
          "endTimeUnixNano": "'$(date +%s%N)'",
          "attributes": [{"key": "test.attribute", "value": {"stringValue": "validation"}}]
        }]
      }]
    }]
  }'

if [ $? -eq 0 ]; then
    echo "✅ Test trace sent successfully"
else
    echo "❌ Failed to send test trace"
    exit 1
fi

# Check Temporal worker logs for tracing
echo "6. Checking Temporal worker tracing configuration..."
TEMPORAL_PODS=$(kubectl get pods -n temporal -l app=temporal-worker -o jsonpath='{.items[*].metadata.name}')

for POD in $TEMPORAL_PODS; do
    echo "Checking pod: $POD"
    kubectl logs -n temporal $POD --tail=50 | grep -i "opentelemetry\|trace\|arize"
done

echo ""
echo "🎉 Validation complete!"
echo "Next steps:"
echo "1. Access Phoenix UI at: http://phoenix.staging.internal.example.com"
echo "2. Check for test traces in the UI"
echo "3. Monitor Temporal workflows for trace generation"
