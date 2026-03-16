# Flux Status Page User Management and RBAC

This guide covers user management, role-based access control (RBAC), and permissions for the Flux Status Page.

## Overview

The Flux Status Page supports multiple authentication methods and provides granular access control through RBAC. Users can be assigned different roles with specific permissions based on their responsibilities.

## User Roles

### 1. Admin

**Description**: Full administrative access to all Flux resources and operations.

**Permissions**:
- Read, write, delete all Flux resources
- Reconcile Flux resources
- Manage user permissions
- Access all dashboards and features

**Resources**:
- FluxInstances
- ResourceSets
- Kustomizations
- HelmReleases
- GitRepositories
- OCIRepositories
- Buckets
- ImageRepositories
- ImagePolicies
- ImageUpdateAutomations

**Use Cases**:
- Platform administrators
- DevOps engineers
- Infrastructure leads

### 2. Operator

**Description**: Operational access with reconciliation capabilities.

**Permissions**:
- Read all Flux resources
- Update and patch Flux resources
- Trigger reconciliation
- Access operational dashboards

**Resources**:
- FluxInstances
- ResourceSets
- Kustomizations
- HelmReleases
- GitRepositories
- OCIRepositories
- Buckets

**Use Cases**:
- Site reliability engineers
- Operations teams
- Support engineers

### 3. Viewer

**Description**: Read-only access to monitor and inspect resources.

**Permissions**:
- Read all resources
- View dashboards and reports
- Export data
- No modification capabilities

**Resources**:
- All Flux and Kubernetes resources

**Use Cases**:
- Developers
- QA engineers
- Business stakeholders
- Auditors

## User Management

### Static User Configuration

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: flux-ui-users
  namespace: flux-system
data:
  users.yaml: |
    users:
      - email: "admin@example.com"
        username: "admin"
        displayName: "Administrator"
        roles: ["admin"]
        groups: ["flux-admins"]
        enabled: true
      - email: "operator@example.com"
        username: "operator"
        displayName: "Operator"
        roles: ["operator"]
        groups: ["flux-operators"]
        enabled: true
      - email: "viewer@example.com"
        username: "viewer"
        displayName: "Viewer"
        roles: ["viewer"]
        groups: ["flux-viewers"]
        enabled: true
```

### Group-Based Management

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: flux-ui-groups
  namespace: flux-system
data:
  groups.yaml: |
    groups:
      flux-admins:
        description: "Flux administrators"
        members:
          - "admin@example.com"
          - "platform-lead@example.com"
        roles: ["admin"]
        permissions:
          - "full_access"
      
      flux-operators:
        description: "Flux operators"
        members:
          - "operator@example.com"
          - "sre@example.com"
        roles: ["operator"]
        permissions:
          - "operational_access"
      
      flux-viewers:
        description: "Flux viewers"
        members:
          - "viewer@example.com"
          - "developer@example.com"
          - "qa@example.com"
        roles: ["viewer"]
        permissions:
          - "read_only"
      
      flux-developers:
        description: "Flux developers"
        members:
          - "developer@example.com"
          - "frontend-dev@example.com"
        roles: ["viewer"]
        permissions:
          - "read_only"
          - "export_data"
```

### Team-Based Management

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: flux-ui-teams
  namespace: flux-system
data:
  teams.yaml: |
    teams:
      platform-team:
        description: "Platform engineering team"
        members:
          - "admin@example.com"
          - "platform-lead@example.com"
        roles: ["admin"]
        resources:
          namespaces: ["*"]
          clusters: ["*"]
        permissions:
          - "full_management"
      
      devops-team:
        description: "DevOps team"
        members:
          - "operator@example.com"
          - "sre@example.com"
        roles: ["operator"]
        resources:
          namespaces: ["flux-system", "production", "staging"]
          clusters: ["main"]
        permissions:
          - "operational_management"
      
      frontend-team:
        description: "Frontend development team"
        members:
          - "frontend-dev@example.com"
        roles: ["viewer"]
        resources:
          namespaces: ["frontend", "frontend-staging"]
        permissions:
          - "read_only"
          - "view_deployments"
      
      backend-team:
        description: "Backend development team"
        members:
          - "backend-dev@example.com"
        roles: ["viewer"]
        resources:
          namespaces: ["backend", "backend-staging"]
        permissions:
          - "read_only"
          - "view_deployments"
```

## RBAC Configuration

### Cluster Roles

#### Admin Role

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: flux-ui-admin
  labels:
    app.kubernetes.io/name: flux-operator
    app.kubernetes.io/component: ui
    app.kubernetes.io/part-of: gitops-infra-control-plane
rules:
# Flux resources
- apiGroups: ["fluxcd.controlplane.io"]
  resources: ["*"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
- apiGroups: ["source.toolkit.fluxcd.io"]
  resources: ["*"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
- apiGroups: ["kustomize.toolkit.fluxcd.io"]
  resources: ["*"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
- apiGroups: ["helm.toolkit.fluxcd.io"]
  resources: ["*"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
- apiGroups: ["image.toolkit.fluxcd.io"]
  resources: ["*"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
# Kubernetes resources
- apiGroups: [""]
  resources: ["pods", "services", "configmaps", "secrets", "events"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets", "daemonsets", "statefulsets"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
- apiGroups: ["batch"]
  resources: ["jobs", "cronjobs"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
# RBAC
- apiGroups: ["rbac.authorization.k8s.io"]
  resources: ["roles", "rolebindings", "clusterroles", "clusterrolebindings"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
```

#### Operator Role

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: flux-ui-operator
  labels:
    app.kubernetes.io/name: flux-operator
    app.kubernetes.io/component: ui
    app.kubernetes.io/part-of: gitops-infra-control-plane
rules:
# Flux resources
- apiGroups: ["fluxcd.controlplane.io"]
  resources: ["*"]
  verbs: ["get", "list", "watch", "update", "patch"]
- apiGroups: ["source.toolkit.fluxcd.io"]
  resources: ["*"]
  verbs: ["get", "list", "watch", "update", "patch"]
- apiGroups: ["kustomize.toolkit.fluxcd.io"]
  resources: ["*"]
  verbs: ["get", "list", "watch", "update", "patch"]
- apiGroups: ["helm.toolkit.fluxcd.io"]
  resources: ["*"]
  verbs: ["get", "list", "watch", "update", "patch"]
- apiGroups: ["image.toolkit.fluxcd.io"]
  resources: ["*"]
  verbs: ["get", "list", "watch", "update", "patch"]
# Kubernetes resources
- apiGroups: [""]
  resources: ["pods", "services", "configmaps", "secrets", "events"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets", "daemonsets", "statefulsets"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["batch"]
  resources: ["jobs", "cronjobs"]
  verbs: ["get", "list", "watch"]
```

#### Viewer Role

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: flux-ui-viewer
  labels:
    app.kubernetes.io/name: flux-operator
    app.kubernetes.io/component: ui
    app.kubernetes.io/part-of: gitops-infra-control-plane
rules:
# Flux resources
- apiGroups: ["fluxcd.controlplane.io"]
  resources: ["*"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["source.toolkit.fluxcd.io"]
  resources: ["*"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["kustomize.toolkit.fluxcd.io"]
  resources: ["*"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["helm.toolkit.fluxcd.io"]
  resources: ["*"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["image.toolkit.fluxcd.io"]
  resources: ["*"]
  verbs: ["get", "list", "watch"]
# Kubernetes resources
- apiGroups: [""]
  resources: ["pods", "services", "configmaps", "secrets", "events"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets", "daemonsets", "statefulsets"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["batch"]
  resources: ["jobs", "cronjobs"]
  verbs: ["get", "list", "watch"]
```

### Role Bindings

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: flux-ui-admin-binding
  labels:
    app.kubernetes.io/name: flux-operator
    app.kubernetes.io/component: ui
    app.kubernetes.io/part-of: gitops-infra-control-plane
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: flux-ui-admin
subjects:
- kind: ServiceAccount
  name: flux-ui
  namespace: flux-system
- kind: User
  name: admin@example.com
  apiGroup: rbac.authorization.k8s.io
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: flux-ui-operator-binding
  labels:
    app.kubernetes.io/name: flux-operator
    app.kubernetes.io/component: ui
    app.kubernetes.io/part-of: gitops-infra-control-plane
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: flux-ui-operator
subjects:
- kind: ServiceAccount
  name: flux-ui
  namespace: flux-system
- kind: User
  name: operator@example.com
  apiGroup: rbac.authorization.k8s.io
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: flux-ui-viewer-binding
  labels:
    app.kubernetes.io/name: flux-operator
    app.kubernetes.io/component: ui
    app.kubernetes.io/part-of: gitops-infra-control-plane
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: flux-ui-viewer
subjects:
- kind: ServiceAccount
  name: flux-ui
  namespace: flux-system
- kind: User
  name: viewer@example.com
  apiGroup: rbac.authorization.k8s.io
```

## Namespace-Specific Roles

### Production Namespace

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: flux-ui-production-admin
  namespace: production
  labels:
    app.kubernetes.io/name: flux-operator
    app.kubernetes.io/component: ui
    app.kubernetes.io/part-of: gitops-infra-control-plane
rules:
- apiGroups: ["*"]
  resources: ["*"]
  verbs: ["*"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: flux-ui-production-admin-binding
  namespace: production
  labels:
    app.kubernetes.io/name: flux-operator
    app.kubernetes.io/component: ui
    app.kubernetes.io/part-of: gitops-infra-control-plane
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: flux-ui-production-admin
subjects:
- kind: User
  name: admin@example.com
  apiGroup: rbac.authorization.k8s.io
```

### Staging Namespace

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: flux-ui-staging-operator
  namespace: staging
  labels:
    app.kubernetes.io/name: flux-operator
    app.kubernetes.io/component: ui
    app.kubernetes.io/part-of: gitops-infra-control-plane
rules:
- apiGroups: ["*"]
  resources: ["*"]
  verbs: ["get", "list", "watch", "update", "patch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: flux-ui-staging-operator-binding
  namespace: staging
  labels:
    app.kubernetes.io/name: flux-operator
    app.kubernetes.io/component: ui
    app.kubernetes.io/part-of: gitops-infra-control-plane
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: flux-ui-staging-operator
subjects:
- kind: User
  name: operator@example.com
  apiGroup: rbac.authorization.k8s.io
```

## Authentication Integration

### OIDC Group Mapping

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: flux-ui-oidc-mapping
  namespace: flux-system
data:
  oidc-mapping.yaml: |
    # OIDC group to role mapping
    groupMapping:
      # Admin groups
      "flux-admins":
        roles: ["admin"]
        permissions: ["full_access"]
      
      "platform-admins":
        roles: ["admin"]
        permissions: ["full_access"]
      
      # Operator groups
      "flux-operators":
        roles: ["operator"]
        permissions: ["operational_access"]
      
      "devops-team":
        roles: ["operator"]
        permissions: ["operational_access"]
      
      "sre-team":
        roles: ["operator"]
        permissions: ["operational_access"]
      
      # Viewer groups
      "flux-viewers":
        roles: ["viewer"]
        permissions: ["read_only"]
      
      "developers":
        roles: ["viewer"]
        permissions: ["read_only"]
      
      "qa-team":
        roles: ["viewer"]
        permissions: ["read_only"]
      
      "product-managers":
        roles: ["viewer"]
        permissions: ["read_only"]
    
    # User-specific overrides
    userOverrides:
      "super-admin@example.com":
        roles: ["admin"]
        permissions: ["full_access", "user_management"]
      
      "auditor@example.com":
        roles: ["viewer"]
        permissions: ["read_only", "audit_access"]
```

### GitHub Teams Integration

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: flux-ui-github-mapping
  namespace: flux-system
data:
  github-mapping.yaml: |
    # GitHub team to role mapping
    teamMapping:
      # Admin teams
      "your-org/platform-team":
        roles: ["admin"]
        permissions: ["full_access"]
      
      "your-org/devops-team":
        roles: ["operator"]
        permissions: ["operational_access"]
      
      # Developer teams
      "your-org/frontend-team":
        roles: ["viewer"]
        permissions: ["read_only"]
        namespaces: ["frontend", "frontend-staging"]
      
      "your-org/backend-team":
        roles: ["viewer"]
        permissions: ["read_only"]
        namespaces: ["backend", "backend-staging"]
      
      "your-org/qa-team":
        roles: ["viewer"]
        permissions: ["read_only"]
        namespaces: ["staging", "qa"]
    
    # Repository-based access
    repositoryMapping:
      "gitops-infra-control-plane":
        teams:
          "your-org/platform-team": "admin"
          "your-org/devops-team": "operator"
          "your-org/developers": "viewer"
      
      "application-repo":
        teams:
          "your-org/frontend-team": "operator"
          "your-org/backend-team": "operator"
          "your-org/qa-team": "viewer"
```

## Permission Management

### Permission Matrix

| Resource | Admin | Operator | Viewer |
|----------|-------|----------|--------|
| FluxInstances | CRUD | CRUD | R |
| ResourceSets | CRUD | CRUD | R |
| Kustomizations | CRUD | CRUD | R |
| HelmReleases | CRUD | CRUD | R |
| GitRepositories | CRUD | CRUD | R |
| OCIRepositories | CRUD | CRUD | R |
| Buckets | CRUD | CRUD | R |
| ImageRepositories | CRUD | CRUD | R |
| ImagePolicies | CRUD | CRUD | R |
| ImageUpdateAutomations | CRUD | CRUD | R |
| Deployments | CRUD | R | R |
| Services | CRUD | R | R |
| ConfigMaps | CRUD | R | R |
| Secrets | CRUD | R | R |
| Events | CRUD | R | R |
| RBAC | CRUD | R | R |

### Custom Permissions

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: flux-ui-custom-permissions
  namespace: flux-system
data:
  custom-permissions.yaml: |
    # Custom permission definitions
    permissions:
      # Resource-specific permissions
      "reconcile_flux":
        description: "Trigger Flux reconciliation"
        resources: ["fluxinstances", "kustomizations", "helmreleases"]
        roles: ["admin", "operator"]
      
      "suspend_flux":
        description: "Suspend Flux reconciliation"
        resources: ["fluxinstances", "kustomizations", "helmreleases"]
        roles: ["admin", "operator"]
      
      "export_data":
        description: "Export Flux data and configurations"
        resources: ["*"]
        roles: ["admin", "operator", "viewer"]
      
      "view_logs":
        description: "View Flux controller logs"
        resources: ["pods"]
        roles: ["admin", "operator"]
      
      "manage_favorites":
        description: "Manage favorite resources"
        resources: ["*"]
        roles: ["admin", "operator", "viewer"]
      
      "access_graph":
        description: "Access GitOps dependency graph"
        resources: ["*"]
        roles: ["admin", "operator", "viewer"]
      
      "view_history":
        description: "View reconciliation history"
        resources: ["*"]
        roles: ["admin", "operator", "viewer"]
      
      "manage_notifications":
        description: "Manage notification settings"
        resources: ["*"]
        roles: ["admin", "operator"]
      
      "audit_access":
        description: "Access audit logs and compliance data"
        resources: ["*"]
        roles: ["admin"]
      
      "user_management":
        description: "Manage user permissions and roles"
        resources: ["users", "roles"]
        roles: ["admin"]
```

## User Provisioning

### Automated User Provisioning

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: flux-ui-user-provisioning
  namespace: flux-system
  labels:
    app.kubernetes.io/name: flux-operator
    app.kubernetes.io/component: ui
    app.kubernetes.io/part-of: gitops-infra-control-plane
spec:
  template:
    spec:
      containers:
      - name: user-provisioning
        image: python:3.11-slim
        command:
        - /bin/sh
        - -c
        - |
          # Install required packages
          pip install kubernetes pyyaml requests
          
          # User provisioning script
          python3 << 'EOF'
          import yaml
          import os
          from kubernetes import client, config
          
          # Load user configuration
          with open('/config/users.yaml', 'r') as f:
              users_config = yaml.safe_load(f)
          
          # Initialize Kubernetes client
          config.load_incluster_config()
          rbac_v1 = client.RbacAuthorizationV1Api()
          
          # Process each user
          for user in users_config.get('users', []):
              if user.get('enabled', True):
                  # Create role binding for user
                  role_name = f"flux-ui-{user['roles'][0]}-binding"
                  
                  binding = client.V1ClusterRoleBinding(
                      metadata=client.V1ObjectMeta(
                          name=role_name,
                          labels={
                              'app.kubernetes.io/name': 'flux-operator',
                              'app.kubernetes.io/component': 'ui',
                              'app.kubernetes.io/part-of': 'gitops-infra-control-plane',
                              'managed-by': 'user-provisioning'
                          }
                      ),
                      role_ref=client.V1RoleRef(
                          api_group='rbac.authorization.k8s.io',
                          kind='ClusterRole',
                          name=f"flux-ui-{user['roles'][0]}"
                      ),
                      subjects=[
                          client.V1Subject(
                              kind='User',
                              name=user['email'],
                              api_group='rbac.authorization.k8s.io'
                          )
                      ]
                  )
                  
                  try:
                      rbac_v1.create_cluster_role_binding(body=binding)
                      print(f"Created role binding for {user['email']}")
                  except Exception as e:
                      if 'already exists' in str(e):
                          print(f"Role binding for {user['email']} already exists")
                      else:
                          print(f"Error creating role binding for {user['email']}: {e}")
          EOF
        volumeMounts:
        - name: config
          mountPath: /config
      volumes:
      - name: config
        configMap:
          name: flux-ui-users
      restartPolicy: OnFailure
  backoffLimit: 3
```

### User Management API

```yaml
apiVersion: v1
kind: Service
metadata:
  name: flux-ui-user-api
  namespace: flux-system
  labels:
    app.kubernetes.io/name: flux-operator
    app.kubernetes.io/component: ui
    app.kubernetes.io/part-of: gitops-infra-control-plane
spec:
  selector:
    app.kubernetes.io/name: flux-operator
    app.kubernetes.io/component: ui
  ports:
  - name: api
    port: 8080
    targetPort: 8080
    protocol: TCP
  type: ClusterIP
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: flux-ui-user-api
  namespace: flux-system
  labels:
    app.kubernetes.io/name: flux-operator
    app.kubernetes.io/component: ui
    app.kubernetes.io/part-of: gitops-infra-control-plane
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - flux-api.example.com
    secretName: flux-api-tls
  rules:
  - host: flux-api.example.com
    http:
      paths:
      - path: /api/users
        pathType: Prefix
        backend:
          service:
            name: flux-ui-user-api
            port:
              number: 8080
```

## Monitoring and Auditing

### User Activity Monitoring

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: flux-ui-user-activity
  namespace: flux-system
  labels:
    app.kubernetes.io/name: flux-operator
    app.kubernetes.io/component: ui
    app.kubernetes.io/part-of: gitops-infra-control-plane
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: flux-operator
      app.kubernetes.io/component: ui
  endpoints:
  - port: metrics
    path: /metrics
    interval: 30s
    scrapeTimeout: 10s
---
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: flux-ui-user-activity-alerts
  namespace: flux-system
  labels:
    app.kubernetes.io/name: flux-operator
    app.kubernetes.io/component: ui
    app.kubernetes.io/part-of: gitops-infra-control-plane
spec:
  groups:
  - name: user-activity
    rules:
    - alert: HighFailedLoginAttempts
      expr: rate(flux_ui_login_failed_total[5m]) > 0.1
      for: 2m
      labels:
        severity: warning
        app: flux-ui
      annotations:
        summary: "High failed login attempts"
        description: "Failed login rate is {{ $value }} attempts per second"
    - alert: UnauthorizedAccessAttempts
      expr: rate(flux_ui_unauthorized_access_total[5m]) > 0.05
      for: 5m
      labels:
        severity: warning
        app: flux-ui
      annotations:
        summary: "Unauthorized access attempts"
        description: "Unauthorized access rate is {{ $value }} attempts per second"
```

### Audit Logging

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: flux-ui-audit-config
  namespace: flux-system
data:
  audit-config.yaml: |
    # Audit logging configuration
    audit:
      enabled: true
      level: "info"
      format: "json"
      
      # Events to log
      events:
        - "user_login"
        - "user_logout"
        - "user_access_denied"
        - "resource_created"
        - "resource_updated"
        - "resource_deleted"
        - "reconciliation_triggered"
        - "suspicious_activity"
      
      # Retention policy
      retention:
        days: 90
        maxSize: "1GB"
      
      # Export destinations
      export:
        - type: "file"
          path: "/var/log/flux-ui/audit.log"
        - type: "syslog"
          facility: "auth"
        - type: "elasticsearch"
          endpoint: "https://elasticsearch.monitoring.svc.cluster.local:9200"
          index: "flux-ui-audit"
      
      # Sensitive data filtering
      filters:
        - "password"
        - "token"
        - "secret"
        - "credential"
```

## Best Practices

### 1. Principle of Least Privilege

- Assign users the minimum permissions required for their role
- Use namespace-scoped roles when possible
- Regularly review and audit user permissions

### 2. Role-Based Access Control

- Define clear role hierarchies
- Use groups for team-based access
- Implement role inheritance where appropriate

### 3. Regular Auditing

- Monitor user access patterns
- Review permission assignments regularly
- Audit privileged operations

### 4. Secure Authentication

- Use SSO with strong authentication
- Implement MFA where possible
- Use short-lived tokens

### 5. Documentation

- Maintain clear documentation of roles and permissions
- Document approval processes for access requests
- Keep user management procedures up to date

## Troubleshooting

### Common Issues

#### 1. Permission Denied

```bash
# Check user permissions
kubectl auth can-i get fluxinstances --as=user@example.com

# Check role bindings
kubectl get clusterrolebinding | grep user@example.com

# Verify role definitions
kubectl describe clusterrole flux-ui-admin
```

#### 2. Group Mapping Issues

```bash
# Check OIDC groups
kubectl get configmap flux-ui-oidc-mapping -o yaml

# Verify group membership
kubectl logs -n oauth2-proxy deployment/oauth2-proxy | grep -i group

# Test group mapping
curl -H "Authorization: Bearer <token>" https://flux-ui.example.com/api/user/info
```

#### 3. SSO Authentication Issues

```bash
# Check Dex configuration
kubectl get configmap dex-config -n dex -o yaml

# Verify OAuth2 Proxy
kubectl logs -n oauth2-proxy deployment/oauth2-proxy

# Test OIDC flow
curl -v https://dex.example.com/.well-known/openid-configuration
```

### Debug Commands

```bash
# Check user roles
kubectl get clusterrolebinding | grep flux-ui

# Verify permissions
kubectl auth can-i --list --as=user@example.com

# Check group mappings
kubectl get configmap flux-ui-oidc-mapping -o yaml | grep -A 10 groupMapping

# Test authentication
kubectl port-forward -n oauth2-proxy svc/oauth2-proxy 4180:4180
curl -v http://localhost:4180/oauth2/auth
```

---

This comprehensive user management and RBAC configuration provides secure, granular access control for the Flux Status Page while maintaining flexibility for different organizational structures and requirements.
