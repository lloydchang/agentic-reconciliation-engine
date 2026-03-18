#!/bin/bash

# Setup K8sGPT with Qwen LLM Integration
# This script configures K8sGPT to use Qwen as the LLM backend

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="gitops-infra"
QWEN_MODEL="qwen2.5-7b-instruct"
QWEN_BASE_URL="http://qwen-server:8000"
K8SGPT_IMAGE="k8sgpt/k8sgpt:latest"

# Functions
print_header() {
    echo -e "${BLUE}================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

check_prerequisites() {
    print_header "Checking Prerequisites"
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl is not installed or not in PATH"
        exit 1
    fi
    print_success "kubectl found"
    
    # Check cluster access
    if ! kubectl cluster-info &> /dev/null; then
        print_error "Cannot access Kubernetes cluster"
        exit 1
    fi
    print_success "Kubernetes cluster accessible"
    
    # Check if namespace exists
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        print_info "Creating namespace: $NAMESPACE"
        kubectl create namespace "$NAMESPACE"
    fi
    print_success "Namespace ready: $NAMESPACE"
}

setup_qwen_config() {
    print_header "Setting up Qwen Configuration"
    
    # Create Qwen configuration
    print_info "Creating Qwen configuration"
    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: qwen-config
  namespace: $NAMESPACE
data:
  model: "$QWEN_MODEL"
  base_url: "$QWEN_BASE_URL"
  temperature: "0.7"
  max_tokens: "4096"
  top_p: "0.9"
  frequency_penalty: "0.0"
  presence_penalty: "0.0"
  timeout: "300"
  retry_attempts: "3"
EOF
    
    print_success "Qwen configuration created"
}

create_qwen_secret() {
    print_header "Creating Qwen API Secret"
    
    # Check if secret already exists
    if kubectl get secret qwen-secret -n "$NAMESPACE" &> /dev/null; then
        print_warning "Qwen secret already exists"
        read -p "Do you want to update it? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "Keeping existing secret"
            return
        fi
        kubectl delete secret qwen-secret -n "$NAMESPACE"
    fi
    
    # Prompt for API key
    echo -e "${YELLOW}Please enter your Qwen API key:${NC}"
    read -s -p "API Key: " api_key
    echo
    
    if [ -z "$api_key" ]; then
        print_warning "No API key provided. Using placeholder (please update later)"
        api_key="your-qwen-api-key-here"
    fi
    
    # Create secret
    kubectl create secret generic qwen-secret \
        --from-literal=api-key="$api_key" \
        --namespace="$NAMESPACE"
    
    print_success "Qwen API secret created"
}

deploy_k8sgpt() {
    print_header "Deploying K8sGPT Analyzer"
    
    # Create K8sGPT configuration
    print_info "Creating K8sGPT configuration"
    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: k8sgpt-config
  namespace: $NAMESPACE
data:
  config.yaml: |
    backend: localai
    model: $QWEN_MODEL
    baseurl: $QWEN_BASE_URL/v1
    api_key: ""  # Will be loaded from secret
    max_tokens: 4096
    temperature: 0.7
    namespace: default
    output_format: json
    timeout: 300
    retry_attempts: 3
    log_level: info
    cache_enabled: true
    cache_ttl: 300
EOF
    
    # Create RBAC
    print_info "Creating RBAC for K8sGPT"
    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ServiceAccount
metadata:
  name: k8sgpt-analyzer
  namespace: $NAMESPACE
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: k8sgpt-analyzer
rules:
- apiGroups: [""]
  resources: ["pods", "services", "deployments", "configmaps", "secrets", "events"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets", "statefulsets", "daemonsets"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["batch"]
  resources: ["jobs", "cronjobs"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["argoproj.io"]
  resources: ["rollouts", "rollouts/status", "analysistemplates", "analysisruns"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["extensions"]
  resources: ["ingresses"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["networking.k8s.io"]
  resources: ["ingresses", "networkpolicies"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: k8sgpt-analyzer
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: k8sgpt-analyzer
subjects:
- kind: ServiceAccount
  name: k8sgpt-analyzer
  namespace: $NAMESPACE
EOF
    
    # Create deployment
    print_info "Creating K8sGPT deployment"
    cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: k8sgpt-analyzer
  namespace: $NAMESPACE
  labels:
    app: k8sgpt-analyzer
spec:
  replicas: 2
  selector:
    matchLabels:
      app: k8sgpt-analyzer
  template:
    metadata:
      labels:
        app: k8sgpt-analyzer
    spec:
      serviceAccountName: k8sgpt-analyzer
      containers:
      - name: k8sgpt
        image: $K8SGPT_IMAGE
        command: ["/bin/sh"]
        args: ["-c", "while true; do sleep 3600; done"]
        env:
        - name: QWEN_API_KEY
          valueFrom:
            secretKeyRef:
              name: qwen-secret
              key: api-key
        - name: QWEN_BASE_URL
          valueFrom:
            configMapKeyRef:
              name: qwen-config
              key: base_url
        - name: QWEN_MODEL
          valueFrom:
            configMapKeyRef:
              name: qwen-config
              key: model
        volumeMounts:
        - name: k8sgpt-config
          mountPath: /root/.k8sgpt
        resources:
          requests:
            cpu: 100m
            memory: 256Mi
          limits:
            cpu: 500m
            memory: 512Mi
        livenessProbe:
          exec:
            command:
            - /bin/sh
            - -c
            - "k8sgpt version"
          initialDelaySeconds: 30
          periodSeconds: 60
        readinessProbe:
          exec:
            command:
            - /bin/sh
            - -c
            - "k8sgpt version"
          initialDelaySeconds: 10
          periodSeconds: 30
      volumes:
      - name: k8sgpt-config
        configMap:
          name: k8sgpt-config
EOF
    
    # Create service
    print_info "Creating K8sGPT service"
    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Service
metadata:
  name: k8sgpt-analyzer
  namespace: $NAMESPACE
  labels:
    app: k8sgpt-analyzer
spec:
  selector:
    app: k8sgpt-analyzer
  ports:
  - name: http
    port: 8080
    targetPort: 8080
  type: ClusterIP
EOF
    
    # Wait for deployment to be ready
    print_info "Waiting for K8sGPT deployment to be ready"
    kubectl wait --for=condition=available deployment/k8sgpt-analyzer -n "$NAMESPACE" --timeout=300s
    
    print_success "K8sGPT analyzer deployed"
}

setup_analysis_scripts() {
    print_header "Setting up Analysis Scripts"
    
    # Create analysis scripts for Argo Rollouts integration
    print_info "Creating analysis scripts"
    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: k8sgpt-analysis-scripts
  namespace: $NAMESPACE
data:
  calculate-health-score.py: |
    #!/usr/bin/env python3
    import sys
    import json
    import os
    
    def calculate_health_score(analysis_file):
        try:
            with open(analysis_file, 'r') as f:
                analysis = json.load(f)
            
            # Calculate health score based on K8sGPT analysis
            problems = analysis.get('problems', [])
            total_resources = analysis.get('total_resources', 1)
            
            # Base score starts at 1.0
            score = 1.0
            
            # Deduct points for problems
            for problem in problems:
                severity = problem.get('severity', 'medium')
                if severity == 'critical':
                    score -= 0.3
                elif severity == 'high':
                    score -= 0.2
                elif severity == 'medium':
                    score -= 0.1
                elif severity == 'low':
                    score -= 0.05
            
            # Ensure score doesn't go below 0
            score = max(0.0, score)
            
            print(score)
            return 0
        except Exception as e:
            print(f"Error: {e}")
            return 1
    
    if __name__ == "__main__":
        sys.exit(calculate_health_score(sys.argv[1]))
  
  analyze-rollout.py: |
    #!/usr/bin/env python3
    import sys
    import json
    import subprocess
    import os
    
    def analyze_rollout(rollout_name, namespace):
        try:
            # Get rollout status
            result = subprocess.run([
                'kubectl', 'get', 'rollout', rollout_name, 
                '-n', namespace, '-o', 'json'
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"Error getting rollout: {result.stderr}")
                return 1
            
            rollout = json.loads(result.stdout)
            
            # Get K8sGPT analysis
            k8sgpt_result = subprocess.run([
                'k8sgpt', 'analyze', '--namespace', namespace, 
                '--output', 'json'
            ], capture_output=True, text=True)
            
            if k8sgpt_result.returncode != 0:
                print(f"Error running K8sGPT: {k8sgpt_result.stderr}")
                return 1
            
            analysis = json.loads(k8sgpt_result.stdout)
            
            # Analyze rollout health
            rollout_status = rollout.get('status', {})
            strategy = rollout.get('spec', {}).get('strategy', {})
            
            # Prepare analysis for Qwen
            rollout_info = {
                'name': rollout_name,
                'namespace': namespace,
                'status': rollout_status,
                'strategy': strategy,
                'cluster_analysis': analysis
            }
            
            # Get Qwen analysis if available
            qwen_analysis = get_qwen_analysis(rollout_info)
            
            print(json.dumps({
                'rollout': rollout_info,
                'qwen_analysis': qwen_analysis,
                'recommendation': generate_recommendation(rollout_info, qwen_analysis)
            }, indent=2))
            
            return 0
        except Exception as e:
            print(f"Error: {e}")
            return 1
    
    def get_qwen_analysis(rollout_info):
        """Get analysis from Qwen if available"""
        try:
            import requests
            
            qwen_url = os.environ.get('QWEN_BASE_URL', 'http://qwen-server:8000')
            api_key = os.environ.get('QWEN_API_KEY')
            
            if not api_key:
                return {"error": "Qwen API key not available"}
            
            prompt = f"""
            Analyze this Kubernetes rollout and provide insights:
            
            Rollout: {json.dumps(rollout_info, indent=2)}
            
            Please provide:
            1. Health assessment (0-1 score)
            2. Risk assessment (low/medium/high)
            3. Recommendations
            4. Potential issues
            
            Respond with JSON format.
            """
            
            response = requests.post(
                f"{qwen_url}/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}"
                },
                json={
                    "model": os.environ.get('QWEN_MODEL', 'qwen2.5-7b-instruct'),
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return json.loads(result['choices'][0]['message']['content'])
            else:
                return {"error": f"Qwen API error: {response.status_code}"}
                
        except Exception as e:
            return {"error": f"Qwen analysis failed: {e}"}
    
    def generate_recommendation(rollout_info, qwen_analysis):
        """Generate rollout recommendations"""
        status = rollout_info.get('status', {})
        phase = status.get('phase', 'Unknown')
        
        if phase == 'Healthy':
            return 'Rollout is healthy. Continue monitoring.'
        elif phase == 'Progressing':
            return 'Rollout is in progress. Monitor closely for any issues.'
        elif phase == 'Paused':
            return 'Rollout is paused. Review analysis before proceeding.'
        elif phase == 'Degraded':
            return 'Rollout is degraded. Immediate attention required.'
        else:
            return 'Review rollout status and cluster analysis.'
    
    if __name__ == "__main__":
        if len(sys.argv) != 3:
            print("Usage: python3 analyze-rollout.py <rollout-name> <namespace>")
            sys.exit(1)
        
        sys.exit(analyze_rollout(sys.argv[1], sys.argv[2]))
EOF
    
    print_success "Analysis scripts created"
}

setup_monitoring() {
    print_header "Setting up Monitoring"
    
    # Create ServiceMonitor for K8sGPT
    print_info "Creating ServiceMonitor for K8sGPT"
    cat <<EOF | kubectl apply -f -
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: k8sgpt-analyzer
  namespace: $NAMESPACE
  labels:
    app: k8sgpt-analyzer
spec:
  selector:
    matchLabels:
      app: k8sgpt-analyzer
  endpoints:
  - port: http
    interval: 30s
    path: /metrics
EOF
    
    # Create PrometheusRule for K8sGPT alerting
    print_info "Creating alerting rules for K8sGPT"
    cat <<EOF | kubectl apply -f -
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: k8sgpt-analyzer-alerts
  namespace: $NAMESPACE
spec:
  groups:
  - name: k8sgpt-analyzer
    rules:
    - alert: K8sGPTAnalyzerDown
      expr: up{job="k8sgpt-analyzer"} == 0
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "K8sGPT analyzer is down"
        description: "K8sGPT analyzer has been down for more than 5 minutes."
    
    - alert: K8sGPTHighErrorRate
      expr: rate(k8sgpt_errors_total[5m]) > 0.1
      for: 2m
      labels:
        severity: warning
      annotations:
        summary: "K8sGPT analyzer has high error rate"
        description: "K8sGPT analyzer error rate is {{ \$value }} errors per second."
EOF
    
    print_success "Monitoring setup completed"
}

test_integration() {
    print_header "Testing Integration"
    
    # Test K8sGPT basic functionality
    print_info "Testing K8sGPT basic functionality"
    
    # Wait for pods to be ready
    kubectl wait --for=condition=ready pod -l app=k8sgpt-analyzer -n "$NAMESPACE" --timeout=300s
    
    # Test K8sGPT version
    if kubectl exec -n "$NAMESPACE" deployment/k8sgpt-analyzer -- k8sgpt version &> /dev/null; then
        print_success "K8sGPT is working"
    else
        print_error "K8sGPT is not working properly"
        return 1
    fi
    
    # Test basic analysis
    print_info "Testing basic cluster analysis"
    if kubectl exec -n "$NAMESPACE" deployment/k8sgpt-analyzer -- k8sgpt analyze --namespace default --output json &> /dev/null; then
        print_success "K8sGPT analysis working"
    else
        print_warning "K8sGPT analysis failed (may need Qwen server)"
    fi
    
    # Test analysis scripts
    print_info "Testing analysis scripts"
    if kubectl exec -n "$NAMESPACE" deployment/k8sgpt-analyzer -- python3 /scripts/calculate-health-score.py /tmp/test.json; then
        print_success "Analysis scripts working"
    else
        print_warning "Analysis scripts test failed"
    fi
    
    print_success "Integration tests completed"
}

show_next_steps() {
    print_header "Setup Complete"
    
    echo -e "${GREEN}K8sGPT with Qwen LLM integration is now set up!${NC}"
    echo
    echo -e "${YELLOW}Next Steps:${NC}"
    echo
    echo -e "${BLUE}1. Configure Qwen Server:${NC}"
    echo -e "   Make sure your Qwen server is running at: $QWEN_BASE_URL"
    echo -e "   Update the configuration if needed:"
    echo -e "   kubectl edit configmap qwen-config -n $NAMESPACE"
    echo
    echo -e "${BLUE}2. Update API Key:${NC}"
    echo -e "   Set your actual Qwen API key:"
    echo -e "   kubectl edit secret qwen-secret -n $NAMESPACE"
    echo
    echo -e "${BLUE}3. Test Analysis:${NC}"
    echo -e "   kubectl exec -n $NAMESPACE deployment/k8sgpt-analyzer -- k8sgpt analyze --namespace default --explain"
    echo
    echo -e "${BLUE}4. Monitor Health:${NC}"
    echo -e "   kubectl get pods -n $NAMESPACE -l app=k8sgpt-analyzer"
    echo -e "   kubectl logs -n $NAMESPACE deployment/k8sgpt-analyzer"
    echo
    echo -e "${BLUE}5. Use with Argo Rollouts:${NC}"
    echo -e "   See docs/ARGO-ROLLOUTS-COMPREHENSIVE-GUIDE.md for integration examples"
    echo
    echo -e "${YELLOW}Configuration Files:${NC}"
    echo -e "   • K8sGPT Config: kubectl get configmap k8sgpt-config -n $NAMESPACE -o yaml"
    echo -e "   • Qwen Config: kubectl get configmap qwen-config -n $NAMESPACE -o yaml"
    echo -e "   • Analysis Scripts: kubectl get configmap k8sgpt-analysis-scripts -n $NAMESPACE -o yaml"
    echo
    echo -e "${GREEN}Happy AI-powered analysis! 🤖${NC}"
}

# Main execution
main() {
    print_header "K8sGPT with Qwen LLM Integration Setup"
    
    check_prerequisites
    setup_qwen_config
    create_qwen_secret
    deploy_k8sgpt
    setup_analysis_scripts
    setup_monitoring
    test_integration
    show_next_steps
}

# Handle script interruption
trap 'print_error "Script interrupted"; exit 1' INT TERM

# Run main function
main "$@"
