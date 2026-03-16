#!/bin/bash

# Controller Configuration Generator Script
# Generates standardized controller configurations for all cloud providers

set -euo pipefail
cd $(dirname $0)

# Default values
CLOUD_PROVIDER="${1:-aws}"
SERVICE="${2:-ec2}"
REGION="${3:-us-west-2}"
NAMESPACE="${4:-flux-system}"
REPLICAS="${5:-2}"
LOG_LEVEL="${6:-info}"
RECONCILE_INTERVAL="${7:-5m}"

# Configuration directory
CONFIG_DIR="control-plane/controllers/generated-configs"
TEMPLATES_DIR="control-plane/controllers/templates"

echo "🔧 Generating controller configuration for $CLOUD_PROVIDER/$SERVICE"

# Create directories
mkdir -p "$CONFIG_DIR"
mkdir -p "$TEMPLATES_DIR"

# Function to generate AWS controller config
generate_aws_config() {
    local service=$1
    local config_file="$CONFIG_DIR/aws-${service}-controller.yaml"
    
    cat > "$config_file" << EOF
# AWS ${service} Controller Configuration
apiVersion: apps/v1
kind: Deployment
metadata:
  name: aws-${service}-controller
  namespace: $NAMESPACE
  labels:
    app.kubernetes.io/name: aws-${service}-controller
    app.kubernetes.io/component: gitops-infra-control-plane
    cloud: aws
    service: $service
    managed-by: unified-installer
spec:
  replicas: $REPLICAS
  selector:
    matchLabels:
      app.kubernetes.io/name: aws-${service}-controller
  template:
    metadata:
      labels:
        app.kubernetes.io/name: aws-${service}-controller
        cloud: aws
        service: $service
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8080"
        prometheus.io/path: "/metrics"
        gitops-infra-control-plane.io/correlation-id: "\$(cat /proc/sys/kernel/random/uuid)"
    spec:
      serviceAccountName: aws-${service}-controller
      securityContext:
        runAsNonRoot: true
        runAsUser: 65532
        fsGroup: 65532
      containers:
      - name: controller
        image: public.ecr.aws/aws-controllers-k8s/${service}-controller:v1.0.0
        args:
        - --v=$LOG_LEVEL
        - --metrics-bind-address=:8080
        - --health-probe-bind-address=:8081
        - --reconcile-interval=$RECONCILE_INTERVAL
        env:
        - name: AWS_REGION
          value: "$REGION"
        - name: RECONCILE_INTERVAL
          value: "$RECONCILE_INTERVAL"
        - name: CORRELATION_ID
          valueFrom:
            fieldRef:
              fieldPath: metadata.annotations['gitops-infra-control-plane.io/correlation-id']
        - name: LOG_LEVEL
          value: "$LOG_LEVEL"
        - name: ENABLE_TRACING
          value: "true"
        - name: JAEGER_ENDPOINT
          value: "http://jaeger-collector.observability.svc.cluster.local:14268/api/traces"
        resources:
          requests:
            cpu: 100m
            memory: 256Mi
          limits:
            cpu: 500m
            memory: 512Mi
        ports:
        - containerPort: 8080
          name: metrics
          protocol: TCP
        - containerPort: 8081
          name: health
          protocol: TCP
        livenessProbe:
          httpGet:
            path: /healthz
            port: health
          initialDelaySeconds: 15
          periodSeconds: 20
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /readyz
            port: health
          initialDelaySeconds: 5
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL
        volumeMounts:
        - name: tmp
          mountPath: /tmp
      volumes:
      - name: tmp
        emptyDir: {}
---
# Service Account for AWS ${service} Controller
apiVersion: v1
kind: ServiceAccount
metadata:
  name: aws-${service}-controller
  namespace: $NAMESPACE
  labels:
    app.kubernetes.io/name: aws-${service}-controller
    cloud: aws
    service: $service
  annotations:
    iam.amazonaws.com/role: "arn:aws:iam::\$(aws sts get-caller-identity --query Account --output text):role/gitops-${service}-controller"
---
# Service for Metrics
apiVersion: v1
kind: Service
metadata:
  name: aws-${service}-controller-metrics
  namespace: $NAMESPACE
  labels:
    app.kubernetes.io/name: aws-${service}-controller
    cloud: aws
    service: $service
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "8080"
    prometheus.io/path: "/metrics"
spec:
  selector:
    app.kubernetes.io/name: aws-${service}-controller
  ports:
  - name: metrics
    port: 8080
    targetPort: 8080
    protocol: TCP
---
# Service Monitor for Prometheus
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: aws-${service}-controller
  namespace: $NAMESPACE
  labels:
    app.kubernetes.io/name: aws-${service}-controller
    cloud: aws
    service: $service
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: aws-${service}-controller
  endpoints:
  - port: metrics
    path: /metrics
    interval: 30s
    scrapeTimeout: 10s
EOF

    echo "✅ AWS $service controller configuration generated: $config_file"
}

# Function to generate Azure controller config
generate_azure_config() {
    local service=$1
    local config_file="$CONFIG_DIR/azure-${service}-controller.yaml"
    
    cat > "$config_file" << EOF
# Azure ${service} Controller Configuration
apiVersion: apps/v1
kind: Deployment
metadata:
  name: azure-${service}-controller
  namespace: $NAMESPACE
  labels:
    app.kubernetes.io/name: azure-${service}-controller
    app.kubernetes.io/component: gitops-infra-control-plane
    cloud: azure
    service: $service
    managed-by: unified-installer
spec:
  replicas: $REPLICAS
  selector:
    matchLabels:
      app.kubernetes.io/name: azure-${service}-controller
  template:
    metadata:
      labels:
        app.kubernetes.io/name: azure-${service}-controller
        cloud: azure
        service: $service
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8080"
        prometheus.io/path: "/metrics"
        gitops-infra-control-plane.io/correlation-id: "\$(cat /proc/sys/kernel/random/uuid)"
    spec:
      serviceAccountName: azure-${service}-controller
      containers:
      - name: controller
        image: mcr.microsoft.com/azure-service-operator/${service}-controller:v1.0.0
        args:
        - --v=$LOG_LEVEL
        - --metrics-bind-address=:8080
        - --health-probe-bind-address=:8081
        env:
        - name: AZURE_SUBSCRIPTION_ID
          valueFrom:
            secretKeyRef:
              name: azure-credentials
              key: subscription-id
        - name: AZURE_TENANT_ID
          valueFrom:
            secretKeyRef:
              name: azure-credentials
              key: tenant-id
        - name: AZURE_CLIENT_ID
          valueFrom:
            secretKeyRef:
              name: azure-credentials
              key: client-id
        - name: RECONCILE_INTERVAL
          value: "$RECONCILE_INTERVAL"
        - name: CORRELATION_ID
          valueFrom:
            fieldRef:
              fieldPath: metadata.annotations['gitops-infra-control-plane.io/correlation-id']
        - name: LOG_LEVEL
          value: "$LOG_LEVEL"
        resources:
          requests:
            cpu: 100m
            memory: 256Mi
          limits:
            cpu: 500m
            memory: 512Mi
        ports:
        - containerPort: 8080
          name: metrics
        - containerPort: 8081
          name: health
        livenessProbe:
          httpGet:
            path: /healthz
            port: health
          initialDelaySeconds: 15
          periodSeconds: 20
        readinessProbe:
          httpGet:
            path: /readyz
            port: health
          initialDelaySeconds: 5
          periodSeconds: 10
---
# Service Account for Azure ${service} Controller
apiVersion: v1
kind: ServiceAccount
metadata:
  name: azure-${service}-controller
  namespace: $NAMESPACE
  labels:
    app.kubernetes.io/name: azure-${service}-controller
    cloud: azure
    service: $service
  annotations:
    azure.workload.identity/client-id: "CLIENT_ID"
EOF

    echo "✅ Azure $service controller configuration generated: $config_file"
}

# Function to generate GCP controller config
generate_gcp_config() {
    local service=$1
    local config_file="$CONFIG_DIR/gcp-${service}-controller.yaml"
    
    cat > "$config_file" << EOF
# GCP ${service} Controller Configuration
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gcp-${service}-controller
  namespace: $NAMESPACE
  labels:
    app.kubernetes.io/name: gcp-${service}-controller
    app.kubernetes.io/component: gitops-infra-control-plane
    cloud: gcp
    service: $service
    managed-by: unified-installer
spec:
  replicas: $REPLICAS
  selector:
    matchLabels:
      app.kubernetes.io/name: gcp-${service}-controller
  template:
    metadata:
      labels:
        app.kubernetes.io/name: gcp-${service}-controller
        cloud: gcp
        service: $service
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8080"
        prometheus.io/path: "/metrics"
        gitops-infra-control-plane.io/correlation-id: "\$(cat /proc/sys/kernel/random/uuid)"
    spec:
      serviceAccountName: gcp-${service}-controller
      containers:
      - name: controller
        image: gcr.io/gke-config/${service}-controller:v1.0.0
        args:
        - --v=$LOG_LEVEL
        - --metrics-bind-address=:8080
        - --health-probe-bind-address=:8081
        env:
        - name: GOOGLE_PROJECT
          valueFrom:
            secretKeyRef:
              name: gcp-credentials
              key: project-id
        - name: GOOGLE_REGION
          value: "$REGION"
        - name: RECONCILE_INTERVAL
          value: "$RECONCILE_INTERVAL"
        - name: CORRELATION_ID
          valueFrom:
            fieldRef:
              fieldPath: metadata.annotations['gitops-infra-control-plane.io/correlation-id']
        - name: LOG_LEVEL
          value: "$LOG_LEVEL"
        resources:
          requests:
            cpu: 100m
            memory: 256Mi
          limits:
            cpu: 500m
            memory: 512Mi
        ports:
        - containerPort: 8080
          name: metrics
        - containerPort: 8081
          name: health
        livenessProbe:
          httpGet:
            path: /healthz
            port: health
          initialDelaySeconds: 15
          periodSeconds: 20
        readinessProbe:
          httpGet:
            path: /readyz
            port: health
          initialDelaySeconds: 5
          periodSeconds: 10
---
# Service Account for GCP ${service} Controller
apiVersion: v1
kind: ServiceAccount
metadata:
  name: gcp-${service}-controller
  namespace: $NAMESPACE
  labels:
    app.kubernetes.io/name: gcp-${service}-controller
    cloud: gcp
    service: $service
  annotations:
    iam.gke.io/gcp-service-account: "gitops-${service}-controller@PROJECT_ID.iam.gserviceaccount.com"
EOF

    echo "✅ GCP $service controller configuration generated: $config_file"
}

# Function to generate all controllers for a cloud provider
generate_all_controllers() {
    local cloud=$1
    
    case $cloud in
        aws)
            local services=("ec2" "eks" "vpc" "iam")
            for service in "${services[@]}"; do
                generate_aws_config "$service"
            done
            ;;
        azure)
            local services=("aks" "network" "resource-group")
            for service in "${services[@]}"; do
                generate_azure_config "$service"
            done
            ;;
        gcp)
            local services=("gke" "compute" "network")
            for service in "${services[@]}"; do
                generate_gcp_config "$service"
            done
            ;;
        *)
            echo "❌ Unsupported cloud provider: $cloud"
            echo "Supported providers: aws, azure, gcp"
            exit 1
            ;;
    esac
}

# Function to generate kustomization for all controllers
generate_kustomization() {
    local kustomization_file="$CONFIG_DIR/kustomization.yaml"
    
    cat > "$kustomization_file" << EOF
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
metadata:
  name: cloud-controllers
  namespace: $NAMESPACE
resources:
$(find "$CONFIG_DIR" -name "*.yaml" -not -name "kustomization.yaml" | sed 's/^/  - /')
commonLabels:
  managed-by: unified-installer
  component: cloud-controllers
  platform: gitops-infra-control-plane
commonAnnotations:
    gitops-infra-control-plane.io/generated-by: "controller-config-generator"
    gitops-infra-control-plane.io/generated-at: "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
patchesStrategicMerge:
  - resource-requests-patch.yaml
EOF

    echo "✅ Kustomization generated: $kustomization_file"
}

# Function to generate resource requests patch
generate_resource_patch() {
    local patch_file="$CONFIG_DIR/resource-requests-patch.yaml"
    
    cat > "$patch_file" << EOF
# Resource Requests Patch for All Controllers
apiVersion: apps/v1
kind: Deployment
metadata:
  name: aws-ec2-controller
spec:
  template:
    spec:
      containers:
      - name: controller
        resources:
          requests:
            cpu: 200m
            memory: 512Mi
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: aws-eks-controller
spec:
  template:
    spec:
      containers:
      - name: controller
        resources:
          requests:
            cpu: 500m
            memory: 1Gi
EOF

    echo "✅ Resource patch generated: $patch_file"
}

# Main execution
main() {
    echo "🚀 Controller Configuration Generator"
    echo "Provider: $CLOUD_PROVIDER"
    echo "Service: $SERVICE"
    echo "Region: $REGION"
    echo "Namespace: $NAMESPACE"
    echo "Replicas: $REPLICAS"
    echo "Log Level: $LOG_LEVEL"
    echo "Reconcile Interval: $RECONCILE_INTERVAL"
    echo ""
    
    # Generate specific controller or all controllers
    if [ "$SERVICE" = "all" ]; then
        generate_all_controllers "$CLOUD_PROVIDER"
    else
        case $CLOUD_PROVIDER in
            aws)
                generate_aws_config "$SERVICE"
                ;;
            azure)
                generate_azure_config "$SERVICE"
                ;;
            gcp)
                generate_gcp_config "$SERVICE"
                ;;
            *)
                echo "❌ Unsupported cloud provider: $CLOUD_PROVIDER"
                exit 1
                ;;
        esac
    fi
    
    # Generate kustomization and patches
    generate_kustomization
    generate_resource_patch
    
    echo ""
    echo "🎉 Controller configuration generation completed!"
    echo "📁 Generated files in: $CONFIG_DIR"
    echo "📋 To apply: kubectl apply -k $CONFIG_DIR"
}

# Run main function
main "$@"
