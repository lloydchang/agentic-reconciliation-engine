# Local Testing Configuration
# This directory contains local cloud emulators for development/testing

## AWS - LocalStack
- **Services**: EC2, EKS, IAM (core infrastructure services)
- **Usage**: Modify ACK controller config to point to LocalStack endpoint
- **Limitations**: Not all AWS services supported, no real AWS costs

## Azure - Azurite  
- **Services**: Storage (Blob, Queue, Table)
- **Usage**: Basic storage testing only
- **Limitations**: Limited to storage services, no full Azure resource management

## GCP - Bigtable Emulator
- **Services**: Bigtable only
- **Usage**: Specific service testing
- **Limitations**: Very limited, most GCP services require real GCP

## How to Enable Local Testing

1. **Deploy emulators**:
   ```bash
   kubectl apply -f infrastructure/tenants/aws/localstack/
   kubectl apply -f infrastructure/tenants/azure/localstack/
   kubectl apply -f infrastructure/tenants/gcp/localstack/
   ```

2. **Modify controller configs** to point to local endpoints instead of cloud APIs

3. **Update CRDs** with test-specific parameters (smaller instances, etc.)

## Important Notes
- Local emulators provide **basic testing only**
- **Not suitable for production** - use real cloud providers
- **Limited service coverage** - many cloud features unavailable locally
- **Performance differs** from real cloud services
- **Cost-free** but may have different behavior than production

For comprehensive testing, use real cloud accounts with test environments.
