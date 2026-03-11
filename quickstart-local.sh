#!/bin/bash
# Quickstart: Local Management Cluster with Cloud Emulators

# 1. Make script executable and run
chmod +x setup-local-management.sh
./setup-local-management.sh

# 2. Verify setup
kubectl config get-contexts

# 3. Test management cluster
kubectl config use-context kind-gitops-management-local
kubectl get pods -n flux-system

# 4. Test workload cluster
kubectl config use-context kind-gitops-workload-local
kubectl get pods -A

# 5. Test emulators
curl http://localhost:4566/_localstack/health  # LocalStack
curl http://localhost:9023/storage/v1/b  # GCS Emulator
