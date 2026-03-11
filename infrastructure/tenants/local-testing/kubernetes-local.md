# Local Kubernetes Testing Setup
# Use Minikube, Kind, or Docker Desktop to test workload cluster deployments locally

## Option 1: Minikube (Recommended for single-node testing)
```bash
# Install Minikube
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube

# Start Minikube with required addons
minikube start --addons=ingress,metrics-server

# Enable ingress and LoadBalancer services
minikube addons enable ingress
minikube tunnel  # For LoadBalancer services
```

## Option 2: Kind (Kubernetes in Docker)
```bash
# Install Kind
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
chmod +x ./kind && sudo mv ./kind /usr/local/bin/

# Create kind cluster with ingress
kind create cluster --config - <<EOF
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: InitConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        node-labels: "ingress-ready=true"
  extraPortMappings:
  - containerPort: 80
    hostPort: 80
    protocol: TCP
  - containerPort: 443
    hostPort: 443
    protocol: TCP
EOF

# Install ingress-nginx
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/kind/deploy.yaml
```

## Option 3: Docker Desktop Kubernetes
```bash
# Enable Kubernetes in Docker Desktop
# Settings -> Kubernetes -> Enable Kubernetes

# Verify it's working
kubectl cluster-info

# Use the automated setup script
export CLUSTER_TYPE=docker-desktop
./setup-local-management.sh
```

## Automated Setup Script
```bash
# Choose your cluster type
export CLUSTER_TYPE=docker-desktop  # kind, minikube, or docker-desktop
./setup-local-management.sh
```

## Testing Workload Deployments Locally

1. **Deploy Flux locally**:
   ```bash
   flux install --components=source-controller,kustomize-controller,helm-controller
   ```

2. **Apply workload manifests**:
   ```bash
   kubectl apply -k infrastructure/tenants/3-workloads/
   ```

3. **Test database connections**:
   ```bash
   # Port forward MySQL
   kubectl port-forward svc/mysql-sample 3306:3306

   # Connect locally
   mysql -h 127.0.0.1 -u user -p sampledb
   ```

4. **Test application access**:
   ```bash
   # Port forward services or use ingress
   kubectl port-forward svc/nginx-sample 8080:80
   curl http://localhost:8080
   ```

## Cluster Type Comparison

| Feature | Kind | Minikube | Docker Desktop |
|---------|------|----------|----------------|
| Setup Complexity | Medium | Easy | Easiest |
| Resource Usage | Low | Medium | High |
| Multi-node | Yes | Limited | No |
| Ingress | Manual | Addons | Built-in |
| LoadBalancer | Port forward | Tunnel | Built-in |
| Persistence | HostPath | HostPath | HostPath |

## Limitations
- **No cloud services**: Can't test ACK/ASO/KCC controllers locally
- **Storage differences**: Local storage vs cloud persistent volumes
- **Networking**: Local ingress vs cloud load balancers
- **Performance**: Local resources vs cloud scale

## Best Practices
- Use for **workload testing only** (apps, DBs, monitoring)
- Test **infrastructure provisioning** in real cloud environments
- Combine with **cloud emulators** for hybrid testing
- Use **GitHub Actions** with Kind for CI/CD testing

This setup allows testing of application deployments and configurations without cloud costs.
