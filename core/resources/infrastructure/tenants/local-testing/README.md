# Local Testing Configuration
# This directory contains comprehensive local cloud emulators for development/testing

## AWS - LocalStack (Extended)
- **Core Services**: EC2, EKS, IAM (infrastructure)
- **Additional Services**: S3, Lambda, DynamoDB, SQS, SNS, RDS, CloudFormation
- **Usage**: Modify ACK controller config to point to LocalStack endpoint
- **Deployment**: Use `extended-services.yaml` for broader testing

## Azure - Comprehensive Emulators
- **Azurite**: Storage (Blob, Queue, Table) services
- **Cosmos DB Emulator**: NoSQL database testing
- **Service Bus Emulator**: Message queuing and topics
- **Event Hubs Emulator**: Event streaming with Kafka protocol support
- **LocalStack Azure**: Unified Azure services via LocalStack

## GCP - Comprehensive Emulators
- **Bigtable Emulator**: NoSQL Big Data database
- **Cloud Storage Emulator**: Object storage (GCS)
- **Pub/Sub Emulator**: Message queuing
- **Firestore Emulator**: Document database
- **Cloud Spanner Emulator**: Relational database
- **Usage**: Individual service testing with gcloud SDK
- **Limitations**: Most services require real GCP, emulators are service-specific

## Additional Local Testing Options

### AWS Alternatives
- **Moto**: Python library for AWS service mocking (unit tests)
- **DynamoDB Local**: Standalone DynamoDB instance
- **SQS/DynamoDB via LocalStack**: Already included

### Azure Alternatives
- **Azure SDK Emulators**: Limited, mostly for development
- **Service Bus Emulator**: For messaging services
- **Cosmos DB Emulator**: Full emulator for Windows/Linux

### GCP Alternatives
- **Datastore Emulator**: For App Engine datastore
- **Spanner Emulator**: For relational database testing
- **Functions Framework**: For Cloud Functions testing

### Cross-Platform
- **TestContainers**: JVM-based containers for testing
- **LocalStack Pro**: Commercial version with more services
- **Minio**: S3-compatible object storage
- **RabbitMQ**: Message queue alternative

## Testing Strategies

### 1. Service-Level Testing
```bash
# Test individual services locally
kubectl port-forward svc/gcs-emulator 9023:9023
# Use GCP SDK to connect to localhost:9023
```

### 2. Integration Testing
```bash
# Deploy multiple emulators together
kubectl apply -f core/resources/tenants/aws/localstack/
kubectl apply -f core/resources/tenants/gcp/localstack/
# Test cross-service interactions
```

### 3. Workload Testing
```bash
# Use local K8s + emulators for full stack testing
minikube start
kubectl apply -k core/resources/tenants/local-testing/workloads-local/
# Applications connect to emulator services
```

## Configuration Examples

### AWS LocalStack
```yaml
# In application config
aws:
  endpoint: http://localstack.localstack.svc.cluster.local:4566
  region: us-east-1
  access_key_id: test
  secret_access_key: test
```

### GCP Emulators
```bash
# Set environment variables
export STORAGE_EMULATOR_HOST=http://gcs-emulator.default.svc.cluster.local:9023
export PUBSUB_EMULATOR_HOST=http://pubsub-emulator.default.svc.cluster.local:8085
export FIRESTORE_EMULATOR_HOST=http://firestore-emulator.default.svc.cluster.local:8080
```

### Azure Emulators
```bash
# Azurite connection string
export AZURITE_CONNECTION_STRING="DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=devstoreaccount1key;BlobEndpoint=http://azurite.default.svc.cluster.local:10000;QueueEndpoint=http://azurite.default.svc.cluster.local:10001;TableEndpoint=http://azurite.default.svc.cluster.local:10002"
```

## Important Notes
- **Cost-Free**: All emulators run locally with no cloud charges
- **Performance**: Local resources vs cloud scale - expect differences
- **Feature Parity**: Emulators may not support all cloud features
- **Production**: Never use emulators for production deployments
- **Updates**: Keep emulator images updated for latest features

## Recommended Testing Flow
1. **Unit Tests**: Use SDK emulators (Moto, Azure SDK)
2. **Integration Tests**: LocalStack + GCP emulators
3. **Workload Tests**: Minikube/Kind + emulators
4. **Production Tests**: Real cloud with test accounts
