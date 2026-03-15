--- 
name: manifest-generator 
description: Generate Kubernetes manifests from natural language requests. Triggers: user asks to create Kubernetes YAML for deployments, services, configmaps, etc. 
tools: 
  - bash 
  - computer 
--- 

# Manifest Generator Skill 

Generate Kubernetes Deployment, Service, ConfigMap, and other manifests from natural language descriptions. 

## Inputs 
Natural language description of the desired Kubernetes resource. 

## Process 
1. Parse the natural language request 
2. Identify the resource type (Deployment, Service, etc.) 
3. Generate appropriate YAML manifest 
4. Validate the YAML syntax 

## Outputs 
Valid Kubernetes YAML manifest. 

## Examples 
- "Create a deployment with 3 replicas of nginx, expose port 80, and set memory limit to 512Mi" 
- "Generate a LoadBalancer service for my web app on port 80" 
- "Create a ConfigMap with environment variables for my app" 

## Output Format 
```yaml 
apiVersion: apps/v1 
kind: Deployment 
metadata: 
  name: nginx-deployment 
spec: 
  replicas: 3 
  selector: 
    matchLabels: 
      app: nginx 
  template: 
    metadata: 
      labels: 
        app: nginx 
    spec: 
      containers: 
      - name: nginx 
        image: nginx:latest 
        ports: 
        - containerPort: 80 
        resources: 
          limits: 
            memory: 512Mi 
--- 
apiVersion: v1 
kind: Service 
metadata: 
  name: nginx-service 
spec: 
  selector: 
    app: nginx 
  ports: 
    - protocol: TCP 
      port: 80 
      targetPort: 80 
  type: LoadBalancer 
``` 

