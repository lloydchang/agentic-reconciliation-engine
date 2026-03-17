# AI Agents Security Guide

## Overview

This guide covers comprehensive security considerations for the Cloud AI Agents ecosystem, including authentication, authorization, data protection, network security, and compliance requirements.

## Security Architecture

### Security Layers
```yaml
Security Layers:
  Network Security:
    - Network Policies: Pod-to-pod communication control
    - Service Mesh: mTLS and traffic encryption
    - Ingress Security: TLS termination and authentication
    - Egress Filtering: Outbound traffic control

  Application Security:
    - Authentication: Service account and user authentication
    - Authorization: RBAC and ABAC policies
    - Input Validation: API request sanitization
    - Secure Coding: Memory safety and vulnerability prevention

  Data Security:
    - Encryption at Rest: PVC and secret encryption
    - Encryption in Transit: TLS for all communications
    - Data Classification: Sensitivity labeling and handling
    - Data Retention: Secure data lifecycle management

  Infrastructure Security:
    - Container Security: Image scanning and runtime protection
    - Node Security: Hardening and vulnerability management
    - Cluster Security: API server security and admission control
    - Supply Chain Security: Signed images and dependency verification
```

### Threat Model
```yaml
Threat Categories:
  External Threats:
    - Network attacks: DDoS, man-in-the-middle, packet injection
    - API attacks: Injection, authentication bypass, rate limiting
    - Supply chain attacks: Malicious images, dependency vulnerabilities
    - Social engineering: Phishing, credential theft

  Internal Threats:
    - Privilege escalation: Container breakout, namespace escape
    - Data exfiltration: Unauthorized data access and extraction
    - Resource abuse: Cryptomining, resource exhaustion
    - Misconfiguration: Accidental exposure, weak credentials

  AI-Specific Threats:
    - Model poisoning: Training data contamination
    - Prompt injection: Malicious input manipulation
    - Model extraction: Stealing proprietary AI models
    - Adversarial attacks: Input perturbation to cause misbehavior
```

## Authentication and Authorization

### Kubernetes RBAC

#### Service Account Configuration
```yaml
# service-account.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: ai-agents-sa
  namespace: ai-infrastructure
  annotations:
    iam.amazonaws.com/role: ai-agents-role
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: ai-infrastructure
  name: ai-agents-role
rules:
- apiGroups: [""]
  resources: ["pods", "services", "configmaps", "secrets"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["batch"]
  resources: ["jobs", "cronjobs"]
  verbs: ["get", "list", "watch", "create", "update", "patch"]
- apiGroups: ["ai.example.com"]
  resources: ["skills", "agents", "workflows"]
  verbs: ["*"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: ai-agents-binding
  namespace: ai-infrastructure
subjects:
- kind: ServiceAccount
  name: ai-agents-sa
  namespace: ai-infrastructure
roleRef:
  kind: Role
  name: ai-agents-role
  apiGroup: rbac.authorization.k8s.io
```

#### Cluster-Level Permissions
```yaml
# cluster-role.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: ai-agents-cluster-role
rules:
- apiGroups: [""]
  resources: ["nodes", "persistentvolumes", "storageclasses"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["networking.k8s.io"]
  resources: ["networkpolicies", "ingresses"]
  verbs: ["get", "list", "watch", "create", "update", "patch"]
- apiGroups: ["monitoring.coreos.com"]
  resources: ["prometheuses", "servicemonitors", "podmonitors"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: ai-agents-cluster-binding
subjects:
- kind: ServiceAccount
  name: ai-agents-sa
  namespace: ai-infrastructure
roleRef:
  kind: ClusterRole
  name: ai-agents-cluster-role
  apiGroup: rbac.authorization.k8s.io
```

### API Authentication

#### JWT Authentication Middleware
```go
// auth/jwt.go
package auth

import (
    "context"
    "fmt"
    "net/http"
    "strings"
    "time"
    
    "github.com/golang-jwt/jwt/v4"
    "github.com/prometheus/client_golang/prometheus"
)

var (
    authRequestsTotal = prometheus.NewCounterVec(
        prometheus.CounterOpts{
            Name: "auth_requests_total",
            Help: "Total number of authentication requests",
        },
        []string{"status"},
    )
    
    authDuration = prometheus.NewHistogram(
        prometheus.HistogramOpts{
            Name: "auth_duration_seconds",
            Help: "Authentication request duration",
        },
    )
)

type Claims struct {
    UserID      string   `json:"user_id"`
    Username    string   `json:"username"`
    Roles       []string `json:"roles"`
    Permissions []string `json:"permissions"`
    jwt.RegisteredClaims
}

type AuthMiddleware struct {
    secretKey     []byte
    issuer        string
    tokenDuration time.Duration
}

func NewAuthMiddleware(secretKey, issuer string, tokenDuration time.Duration) *AuthMiddleware {
    return &AuthMiddleware{
        secretKey:     []byte(secretKey),
        issuer:        issuer,
        tokenDuration: tokenDuration,
    }
}

func (am *AuthMiddleware) GenerateToken(userID, username string, roles, permissions []string) (string, error) {
    now := time.Now()
    claims := Claims{
        UserID:      userID,
        Username:    username,
        Roles:       roles,
        Permissions: permissions,
        RegisteredClaims: jwt.RegisteredClaims{
            ExpiresAt: jwt.NewNumericDate(now.Add(am.tokenDuration)),
            IssuedAt:  jwt.NewNumericDate(now),
            NotBefore: jwt.NewNumericDate(now),
            Issuer:    am.issuer,
            Subject:   userID,
        },
    }

    token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
    return token.SignedString(am.secretKey)
}

func (am *AuthMiddleware) ValidateToken(tokenString string) (*Claims, error) {
    token, err := jwt.ParseWithClaims(tokenString, &Claims{}, func(token *jwt.Token) (interface{}, error) {
        if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
            return nil, fmt.Errorf("unexpected signing method: %v", token.Header["alg"])
        }
        return am.secretKey, nil
    })

    if err != nil {
        return nil, err
    }

    if claims, ok := token.Claims.(*Claims); ok && token.Valid {
        return claims, nil
    }

    return nil, fmt.Errorf("invalid token")
}

func (am *AuthMiddleware) Middleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        start := time.Now()
        defer func() {
            authDuration.Observe(time.Since(start).Seconds())
        }()

        authHeader := r.Header.Get("Authorization")
        if authHeader == "" {
            authRequestsTotal.WithLabelValues("missing").Inc()
            http.Error(w, "Authorization header required", http.StatusUnauthorized)
            return
        }

        parts := strings.Split(authHeader, " ")
        if len(parts) != 2 || parts[0] != "Bearer" {
            authRequestsTotal.WithLabelValues("invalid_format").Inc()
            http.Error(w, "Invalid authorization header format", http.StatusUnauthorized)
            return
        }

        claims, err := am.ValidateToken(parts[1])
        if err != nil {
            authRequestsTotal.WithLabelValues("invalid").Inc()
            http.Error(w, "Invalid token", http.StatusUnauthorized)
            return
        }

        ctx := context.WithValue(r.Context(), "user", claims)
        next.ServeHTTP(w, r.WithContext(ctx))
        authRequestsTotal.WithLabelValues("success").Inc()
    })
}

func (am *AuthMiddleware) RequirePermission(permission string) func(http.Handler) http.Handler {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            user, ok := r.Context().Value("user").(*Claims)
            if !ok {
                http.Error(w, "User not authenticated", http.StatusUnauthorized)
                return
            }

            hasPermission := false
            for _, p := range user.Permissions {
                if p == permission {
                    hasPermission = true
                    break
                }
            }

            if !hasPermission {
                http.Error(w, "Insufficient permissions", http.StatusForbidden)
                return
            }

            next.ServeHTTP(w, r)
        })
    }
}
```

#### OAuth2 Integration
```go
// auth/oauth2.go
package auth

import (
    "context"
    "encoding/json"
    "net/http"
    "net/url"
    "time"
    
    "golang.org/x/oauth2"
)

type OAuth2Config struct {
    ClientID     string
    ClientSecret string
    RedirectURL  string
    Scopes       []string
    AuthURL      string
    TokenURL     string
    UserInfoURL  string
}

type OAuth2Provider struct {
    config *oauth2.Config
}

func NewOAuth2Provider(cfg OAuth2Config) *OAuth2Provider {
    return &OAuth2Provider{
        config: &oauth2.Config{
            ClientID:     cfg.ClientID,
            ClientSecret: cfg.ClientSecret,
            RedirectURL:  cfg.RedirectURL,
            Scopes:       cfg.Scopes,
            Endpoint: oauth2.Endpoint{
                AuthURL:  cfg.AuthURL,
                TokenURL: cfg.TokenURL,
            },
        },
    }
}

func (p *OAuth2Provider) GetAuthURL(state string) string {
    return p.config.AuthCodeURL(state, oauth2.AccessTypeOffline)
}

func (p *OAuth2Provider) ExchangeCode(ctx context.Context, code string) (*oauth2.Token, error) {
    return p.config.Exchange(ctx, code)
}

func (p *OAuth2Provider) GetUserInfo(ctx context.Context, token *oauth2.Token) (*UserInfo, error) {
    client := p.config.Client(ctx, token)
    resp, err := client.Get(p.config.UserInfoURL)
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()

    var userInfo UserInfo
    if err := json.NewDecoder(resp.Body).Decode(&userInfo); err != nil {
        return nil, err
    }

    return &userInfo, nil
}

type UserInfo struct {
    ID       string   `json:"id"`
    Username string   `json:"username"`
    Email    string   `json:"email"`
    Name     string   `json:"name"`
    Groups   []string `json:"groups"`
}
```

## Network Security

### Network Policies

#### Default Deny Policy
```yaml
# default-deny.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: ai-infrastructure
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
```

#### AI Agents Network Policy
```yaml
# ai-agents-netpol.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: ai-agents-netpol
  namespace: ai-infrastructure
spec:
  podSelector:
    matchLabels:
      component: memory-agent
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ai-infrastructure
    - podSelector:
        matchLabels:
          component: agent-dashboard
    ports:
    - protocol: TCP
      port: 8080
  - from:
    - podSelector:
        matchLabels:
          component: skills-orchestrator
    ports:
    - protocol: TCP
      port: 8080
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: ai-infrastructure
    - podSelector:
        matchLabels:
          component: temporal-frontend
    ports:
    - protocol: TCP
      port: 7233
  - to: []
    ports:
    - protocol: TCP
      port: 53
    - protocol: UDP
      port: 53
    - protocol: TCP
      port: 443
    - protocol: TCP
      port: 80
```

#### Database Network Policy
```yaml
# database-netpol.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: database-netpol
  namespace: ai-infrastructure
spec:
  podSelector:
    matchLabels:
      component: memory-agent
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          component: memory-agent
    ports:
    - protocol: TCP
      port: 5432
```

### Service Mesh Security

#### Istio Configuration
```yaml
# istio-auth-policy.yaml
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: ai-infrastructure
spec:
  mtls:
    mode: STRICT
---
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: ai-agents-authz
  namespace: ai-infrastructure
spec:
  selector:
    matchLabels:
      component: memory-agent
  rules:
  - from:
    - source:
        principals: ["cluster.local/ns/ai-core/resources/sa/ai-agents-sa"]
  - to:
    - operation:
        methods: ["GET", "POST", "PUT", "DELETE"]
---
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: ai-agents-destination
  namespace: ai-infrastructure
spec:
  host: "*.ai-infrastructure.svc.cluster.local"
  trafficPolicy:
    tls:
      mode: ISTIO_MUTUAL
    loadBalancer:
      simple: LEAST_CONN
    connectionPool:
      tcp:
        maxConnections: 100
      http:
        http1MaxPendingRequests: 50
        maxRequestsPerConnection: 10
    circuitBreaker:
      consecutiveErrors: 3
      interval: 30s
      baseEjectionTime: 30s
```

### Ingress Security

#### Secure Ingress Configuration
```yaml
# secure-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ai-agents-ingress
  namespace: ai-infrastructure
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
    nginx.ingress.kubernetes.io/limit-connections: "100"
    nginx.ingress.kubernetes.io/limit-rps: "50"
    nginx.ingress.kubernetes.io/rate-limit-connections: "10"
    nginx.ingress.kubernetes.io/rate-limit-requests-per-second: "20"
    nginx.ingress.kubernetes.io/enable-modsecurity: "true"
    nginx.ingress.kubernetes.io/modsecurity-snippet: |
      SecRuleEngine On
      SecRequestBodyAccess On
      SecResponseBodyAccess On
      SecRequestBodyLimit 13107200
      SecRequestBodyNoFilesLimit 131072
spec:
  tls:
  - hosts:
    - ai-agents.example.com
    secretName: ai-agents-tls
  rules:
  - host: ai-agents.example.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: dashboard-api-service
            port:
              number: 5000
      - path: /
        pathType: Prefix
        backend:
          service:
            name: agent-dashboard-service
            port:
              number: 80
```

## Data Security

### Encryption at Rest

#### Persistent Volume Encryption
```yaml
# encrypted-pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: memory-agent-pvc-encrypted
  namespace: ai-infrastructure
  annotations:
    volume.beta.kubernetes.io/storage-class: "encrypted-ssd"
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  storageClassName: encrypted-ssd
---
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: encrypted-ssd
provisioner: kubernetes.io/aws-ebs
parameters:
  type: gp3
  encrypted: "true"
  kmsKeyId: "arn:aws:kms:us-west-2:123456789012:key/12345678-1234-1234-1234-123456789012"
allowVolumeExpansion: true
```

#### Database Encryption
```go
// encryption/database.go
package encryption

import (
    "crypto/aes"
    "crypto/cipher"
    "crypto/rand"
    "database/sql"
    "encoding/base64"
    "fmt"
    "io"
    
    _ "github.com/mattn/go-sqlite3"
)

type DatabaseEncryption struct {
    gcm       cipher.AEAD
    key       []byte
    db        *sql.DB
}

func NewDatabaseEncryption(dbPath string, key []byte) (*DatabaseEncryption, error) {
    block, err := aes.NewCipher(key)
    if err != nil {
        return nil, err
    }

    gcm, err := cipher.NewGCM(block)
    if err != nil {
        return nil, err
    }

    db, err := sql.Open("sqlite3", dbPath)
    if err != nil {
        return nil, err
    }

    // Enable encryption pragmas
    _, err = db.Exec("PRAGMA key = '" + base64.StdEncoding.EncodeToString(key) + "'")
    if err != nil {
        return nil, err
    }

    _, err = db.Exec("PRAGMA cipher_page_size = 4096")
    if err != nil {
        return nil, err
    }

    return &DatabaseEncryption{
        gcm: gcm,
        key: key,
        db:  db,
    }, nil
}

func (de *DatabaseEncryption) EncryptData(data []byte) ([]byte, error) {
    nonce := make([]byte, de.gcm.NonceSize())
    if _, err := io.ReadFull(rand.Reader, nonce); err != nil {
        return nil, err
    }

    ciphertext := de.gcm.Seal(nonce, nonce, data, nil)
    return ciphertext, nil
}

func (de *DatabaseEncryption) DecryptData(ciphertext []byte) ([]byte, error) {
    nonceSize := de.gcm.NonceSize()
    if len(ciphertext) < nonceSize {
        return nil, fmt.Errorf("ciphertext too short")
    }

    nonce, ciphertext := ciphertext[:nonceSize], ciphertext[nonceSize:]
    plaintext, err := de.gcm.Open(nil, nonce, ciphertext, nil)
    if err != nil {
        return nil, err
    }

    return plaintext, nil
}

func (de *DatabaseEncryption) StoreEncryptedMemory(id string, data []byte) error {
    encrypted, err := de.EncryptData(data)
    if err != nil {
        return err
    }

    _, err = de.db.Exec(
        "INSERT INTO encrypted_memories (id, data, created_at) VALUES (?, ?, ?)",
        id, base64.StdEncoding.EncodeToString(encrypted), time.Now(),
    )
    return err
}

func (de *DatabaseEncryption) RetrieveEncryptedMemory(id string) ([]byte, error) {
    var encryptedStr string
    err := de.db.QueryRow("SELECT data FROM encrypted_memories WHERE id = ?", id).Scan(&encryptedStr)
    if err != nil {
        return nil, err
    }

    encrypted, err := base64.StdEncoding.DecodeString(encryptedStr)
    if err != nil {
        return nil, err
    }

    return de.DecryptData(encrypted)
}
```

### Secrets Management

#### Sealed Secrets Configuration
```yaml
# sealed-secret.yaml
apiVersion: bitnami.com/v1alpha1
kind: SealedSecret
metadata:
  name: ai-agents-secrets
  namespace: ai-infrastructure
spec:
  encryptedData:
    jwt-secret: AgBy3i4OJSWK+PiTySYZZA9rO43cGDEQAx...
    database-password: AgAKAoiQm7QDhii4CqCP6xvI4AxZcDtGV...
    api-key: AgAjkdlsaQWE+KdmQxvI4AxZcDtGVqCP6xvI...
  template:
    metadata:
      name: ai-agents-secrets
      namespace: ai-infrastructure
    type: Opaque
```

#### External Secrets Operator
```yaml
# external-secret.yaml
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: aws-secrets-manager
  namespace: ai-infrastructure
spec:
  provider:
    aws:
      service: SecretsManager
      region: us-west-2
      auth:
        jwt:
          serviceAccountRef:
            name: ai-agents-sa
---
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: ai-agents-credentials
  namespace: ai-infrastructure
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager
    kind: SecretStore
  target:
    name: ai-agents-secrets
    creationPolicy: Owner
  data:
  - secretKey: jwt-secret
    remoteRef:
      key: ai-core/ai/runtime/jwt-secret
  - secretKey: database-password
    remoteRef:
      key: ai-core/ai/runtime/database-password
```

## Container Security

### Image Security

#### Secure Base Image
```dockerfile
# Dockerfile.secure
FROM rust:1.75-slim as builder

# Create non-root user
RUN useradd -r -s /bin/false memoryagent

# Build application
WORKDIR /app
COPY . .
RUN cargo build --release

# Runtime stage
FROM debian:bookworm-slim

# Install security updates and minimal packages
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        curl && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean

# Create non-root user
RUN useradd -r -s /bin/false memoryagent

# Copy application
COPY --from=builder /app/target/release/memory-agent /usr/local/bin/

# Set permissions
RUN chmod +x /usr/local/bin/memory-agent && \
    chown memoryagent:memoryagent /usr/local/bin/memory-agent

# Switch to non-root user
USER memoryagent

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Expose port
EXPOSE 8080

# Run application
CMD ["memory-agent"]
```

#### Image Scanning Pipeline
```yaml
# image-scan-pipeline.yaml
apiVersion: tekton.dev/v1beta1
kind: Pipeline
metadata:
  name: security-scan-pipeline
spec:
  params:
  - name: image-url
    type: string
  workspaces:
  - name: shared-data
    description: Shared workspace for the pipeline
  tasks:
  - name: trivy-scan
    taskRef:
      name: trivy-scanner
    params:
    - name: image-url
      value: $(params.image-url)
    workspaces:
    - name: shared-data
      workspace: shared-data
  - name: grype-scan
    taskRef:
      name: grype-scanner
    params:
    - name: image-url
      value: $(params.image-url)
    workspaces:
    - name: shared-data
      workspace: shared-data
  - name: security-policy-check
    taskRef:
      name: policy-checker
    params:
    - name: image-url
      value: $(params.image-url)
    workspaces:
    - name: shared-data
      workspace: shared-data
```

### Runtime Security

#### Pod Security Policy
```yaml
# pod-security-policy.yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: ai-agents-psp
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
    - ALL
  volumes:
    - 'configMap'
    - 'emptyDir'
    - 'projected'
    - 'secret'
    - 'downwardAPI'
    - 'persistentVolumeClaim'
  runAsUser:
    rule: 'MustRunAsNonRoot'
  seLinux:
    rule: 'RunAsAny'
  fsGroup:
    rule: 'RunAsAny'
  readOnlyRootFilesystem: true
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    fsGroup: 1000
```

#### Falco Rules for AI Agents
```yaml
# falco-rules.yaml
- rule: Suspicious Memory Agent Process
  desc: Detect suspicious process execution in memory agent pods
  condition: >
    spawned_process and
    container.name contains "memory-agent" and
    proc.name in (nc, netcat, wget, curl, bash, sh)
  output: >
    Suspicious process spawned in memory agent pod
    (user=%user.name command=%proc.cmdline container=%container.name)
  priority: WARNING
  tags: [process, container, ai-agents]

- rule: Unauthorized Memory Agent Access
  desc: Detect unauthorized access to memory agent database
  condition: >
    open_read and
    container.name contains "memory-agent" and
    fd.name contains "/data/memory.db" and
    not proc.name in (memory-agent, sqlite3)
  output: >
    Unauthorized access to memory agent database
    (user=%user.name command=%proc.cmdline file=%fd.name container=%container.name)
  priority: HIGH
  tags: [file, container, ai-agents]

- rule: AI Agent Data Exfiltration
  desc: Detect potential data exfiltration from AI agents
  condition: >
    spawned_process and
    container.name contains "memory-agent" and
    proc.name in (curl, wget, nc, netcat) and
    proc.cmdline contains "http"
  output: >
    Potential data exfiltration from AI agent
    (user=%user.name command=%proc.cmdline container=%container.name)
  priority: CRITICAL
  tags: [network, container, ai-agents]
```

## Compliance and Auditing

### Audit Logging

#### Kubernetes Audit Policy
```yaml
# audit-policy.yaml
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
- level: Metadata
  namespaces: ["ai-infrastructure"]
  resources:
  - group: ""
    resources: ["secrets", "configmaps"]
  - group: "apps"
    resources: ["deployments", "replicasets"]
- level: Request
  namespaces: ["ai-infrastructure"]
  resources:
  - group: ""
    resources: ["pods"]
  verbs: ["create", "delete", "update", "patch"]
- level: RequestResponse
  namespaces: ["ai-infrastructure"]
  resources:
  - group: "ai.example.com"
    resources: ["skills", "agents"]
```

#### Application Audit Logging
```go
// audit/audit.go
package audit

import (
    "context"
    "encoding/json"
    "time"
    
    "github.com/sirupsen/logrus"
)

type AuditEvent struct {
    Timestamp   time.Time              `json:"timestamp"`
    EventType   string                 `json:"event_type"`
    UserID      string                 `json:"user_id"`
    AgentID     string                 `json:"agent_id"`
    Skill       string                 `json:"skill,omitempty"`
    Action      string                 `json:"action"`
    Resource    string                 `json:"resource"`
    Result      string                 `json:"result"`
    IPAddress   string                 `json:"ip_address"`
    UserAgent   string                 `json:"user_agent"`
    Metadata    map[string]interface{} `json:"metadata"`
}

type AuditLogger struct {
    logger *logrus.Logger
}

func NewAuditLogger() *AuditLogger {
    logger := logrus.New()
    logger.SetFormatter(&logrus.JSONFormatter{})
    logger.SetLevel(logrus.InfoLevel)
    
    return &AuditLogger{logger: logger}
}

func (al *AuditLogger) LogEvent(ctx context.Context, event AuditEvent) error {
    event.Timestamp = time.Now()
    
    // Add context metadata
    if requestID := ctx.Value("request_id"); requestID != nil {
        if event.Metadata == nil {
            event.Metadata = make(map[string]interface{})
        }
        event.Metadata["request_id"] = requestID
    }
    
    if traceID := ctx.Value("trace_id"); traceID != nil {
        if event.Metadata == nil {
            event.Metadata = make(map[string]interface{})
        }
        event.Metadata["trace_id"] = traceID
    }
    
    // Log the event
    al.logger.WithFields(logrus.Fields{
        "event_type": event.EventType,
        "user_id":    event.UserID,
        "agent_id":   event.AgentID,
        "skill":      event.Skill,
        "action":     event.Action,
        "resource":   event.Resource,
        "result":     event.Result,
        "ip_address": event.IPAddress,
        "user_agent": event.UserAgent,
        "metadata":   event.Metadata,
    }).Info("Audit event")
    
    return nil
}

func (al *AuditLogger) LogSkillExecution(ctx context.Context, userID, agentID, skill, action, result string, metadata map[string]interface{}) error {
    event := AuditEvent{
        EventType: "skill_execution",
        UserID:    userID,
        AgentID:   agentID,
        Skill:     skill,
        Action:    action,
        Resource:  "skill",
        Result:    result,
        Metadata:  metadata,
    }
    
    return al.LogEvent(ctx, event)
}

func (al *AuditLogger) LogDataAccess(ctx context.Context, userID, agentID, resource, action string, metadata map[string]interface{}) error {
    event := AuditEvent{
        EventType: "data_access",
        UserID:    userID,
        AgentID:   agentID,
        Action:    action,
        Resource:  resource,
        Result:    "accessed",
        Metadata:  metadata,
    }
    
    return al.LogEvent(ctx, event)
}
```

### Compliance Frameworks

#### GDPR Compliance
```go
// gdpr/gdpr.go
package gdpr

import (
    "context"
    "crypto/rand"
    "encoding/hex"
    "time"
    
    "github.com/google/uuid"
)

type GDPRManager struct {
    dataRetentionPeriod time.Duration
    consentManager     *ConsentManager
    dataProcessor      *DataProcessor
}

type ConsentManager struct {
    consents map[string]*Consent
}

type Consent struct {
    ID          string    `json:"id"`
    UserID      string    `json:"user_id"`
    Purpose     string    `json:"purpose"`
    Granted     bool      `json:"granted"`
    Timestamp   time.Time `json:"timestamp"`
    IPAddress   string    `json:"ip_address"`
    UserAgent   string    `json:"user_agent"`
}

type DataProcessor struct {
    encryptionKey []byte
}

func NewGDPRManager(retentionPeriod time.Duration) *GDPRManager {
    return &GDPRManager{
        dataRetentionPeriod: retentionPeriod,
        consentManager:     NewConsentManager(),
        dataProcessor:      NewDataProcessor(),
    }
}

func (gm *GDPRManager) ProcessPersonalData(ctx context.Context, userID string, data interface{}, purpose string) error {
    // Check consent
    consent, err := gm.consentManager.GetConsent(userID, purpose)
    if err != nil {
        return err
    }
    
    if !consent.Granted {
        return ErrConsentNotGranted
    }
    
    // Process data
    processedData, err := gm.dataProcessor.ProcessData(data)
    if err != nil {
        return err
    }
    
    // Log processing
    gm.logDataProcessing(userID, purpose, processedData)
    
    return nil
}

func (gm *GDPRManager) DeletePersonalData(ctx context.Context, userID string) error {
    // Delete all personal data for user
    return gm.dataProcessor.DeleteUserData(userID)
}

func (gm *GDPRManager) ExportPersonalData(ctx context.Context, userID string) (interface{}, error) {
    return gm.dataProcessor.ExportUserData(userID)
}

func (gm *GDPRManager) AnonymizeData(ctx context.Context, data interface{}) (interface{}, error) {
    return gm.dataProcessor.AnonymizeData(data)
}

func (cm *ConsentManager) RecordConsent(userID, purpose, ipAddress, userAgent string, granted bool) (*Consent, error) {
    consent := &Consent{
        ID:        uuid.New().String(),
        UserID:    userID,
        Purpose:   purpose,
        Granted:   granted,
        Timestamp: time.Now(),
        IPAddress: ipAddress,
        UserAgent: userAgent,
    }
    
    cm.consents[consent.ID] = consent
    return consent, nil
}

func (cm *ConsentManager) GetConsent(userID, purpose string) (*Consent, error) {
    for _, consent := range cm.consents {
        if consent.UserID == userID && consent.Purpose == purpose {
            return consent, nil
        }
    }
    return nil, ErrConsentNotFound
}

func (dp *DataProcessor) ProcessData(data interface{}) (interface{}, error) {
    // Encrypt sensitive data
    encrypted, err := dp.encryptData(data)
    if err != nil {
        return nil, err
    }
    
    return encrypted, nil
}

func (dp *DataProcessor) DeleteUserData(userID string) error {
    // Implement data deletion logic
    return nil
}

func (dp *DataProcessor) ExportUserData(userID string) (interface{}, error) {
    // Implement data export logic
    return nil, nil
}

func (dp *DataProcessor) AnonymizeData(data interface{}) (interface{}, error) {
    // Implement data anonymization logic
    return nil, nil
}

func (dp *DataProcessor) encryptData(data interface{}) (interface{}, error) {
    // Implement encryption logic
    return data, nil
}
```

## Security Monitoring

### Security Metrics

#### Security Monitoring Metrics
```go
// security/metrics.go
package security

import (
    "github.com/prometheus/client_golang/prometheus"
    "github.com/prometheus/client_golang/prometheus/promauto"
)

var (
    securityEventsTotal = promauto.NewCounterVec(
        prometheus.CounterOpts{
            Name: "security_events_total",
            Help: "Total number of security events",
        },
        []string{"event_type", "severity"},
    )
    
    authenticationAttemptsTotal = promauto.NewCounterVec(
        prometheus.CounterOpts{
            Name: "authentication_attempts_total",
            Help: "Total number of authentication attempts",
        },
        []string{"status", "method"},
    )
    
    authorizationFailuresTotal = promauto.NewCounterVec(
        prometheus.CounterOpts{
            Name: "authorization_failures_total",
            Help: "Total number of authorization failures",
        },
        []string{"resource", "action"},
    )
    
    dataAccessTotal = promauto.NewCounterVec(
        prometheus.CounterOpts{
            Name: "data_access_total",
            Help: "Total number of data access events",
        },
        []string{"user_id", "resource", "action"},
    )
    
    encryptionOperationsTotal = promauto.NewCounterVec(
        prometheus.CounterOpts{
            Name: "encryption_operations_total",
            Help: "Total number of encryption operations",
        },
        []string{"operation", "status"},
    )
)

func RecordSecurityEvent(eventType, severity string) {
    securityEventsTotal.WithLabelValues(eventType, severity).Inc()
}

func RecordAuthenticationAttempt(status, method string) {
    authenticationAttemptsTotal.WithLabelValues(status, method).Inc()
}

func RecordAuthorizationFailure(resource, action string) {
    authorizationFailuresTotal.WithLabelValues(resource, action).Inc()
}

func RecordDataAccess(userID, resource, action string) {
    dataAccessTotal.WithLabelValues(userID, resource, action).Inc()
}

func RecordEncryptionOperation(operation, status string) {
    encryptionOperationsTotal.WithLabelValues(operation, status).Inc()
}
```

### Security Alerts

#### Falco Integration
```yaml
# falco-alerts.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: falco-rules
  namespace: falco
data:
  ai_agents_rules.yaml: |
    - rule: Unauthorized AI Agent Access
      desc: Detect unauthorized access to AI agent resources
      condition: >
        spawned_process and
        container.name contains "memory-agent" and
        proc.name in (bash, sh, nc, netcat, curl, wget)
      output: >
        Unauthorized process in AI agent container
        (user=%user.name command=%proc.cmdline container=%container.name)
      priority: WARNING
      tags: [container, ai-agents, security]
      
    - rule: AI Agent Data Exfiltration
      desc: Detect potential data exfiltration from AI agents
      condition: >
        spawned_process and
        container.name contains "memory-agent" and
        proc.cmdline contains "http" and
        proc.name in (curl, wget, nc)
      output: >
        Potential data exfiltration from AI agent
        (user=%user.name command=%proc.cmdline container=%container.name)
      priority: CRITICAL
      tags: [network, container, ai-agents, security]
```

## Incident Response

### Security Incident Response Plan

#### Incident Classification
```yaml
Security Incident Levels:
  CRITICAL:
    - Data breach with sensitive AI model data
    - Complete system compromise
    - Ransomware attack on AI infrastructure
    - Unauthorized access to production AI models
    
  HIGH:
    - Partial system compromise
    - Privilege escalation incidents
    - Suspicious data access patterns
    - DDoS attacks affecting AI services
    
  MEDIUM:
    - Single container compromise
    - Suspicious authentication attempts
    - Configuration security issues
    - Minor data access violations
    
  LOW:
    - Security policy violations
    - Failed authentication attempts
    - Minor configuration issues
    - Informational security events
```

#### Response Procedures
```bash
#!/bin/bash
# security-incident-response.sh

INCIDENT_TYPE=$1
SEVERITY=$2

case $INCIDENT_TYPE in
    "data_breach")
        echo "Initiating data breach response..."
        # 1. Isolate affected systems
        kubectl scale deployment --replicas=0 -l component=memory-agent -n ai-infrastructure
        
        # 2. Preserve evidence
        kubectl get pods -n ai-infrastructure -o yaml > incident/pods-$(date +%Y%m%d-%H%M%S).yaml
        kubectl get events -n ai-infrastructure > incident/events-$(date +%Y%m%d-%H%M%S).log
        
        # 3. Enable enhanced logging
        kubectl apply -f security/enhanced-audit-policy.yaml
        
        # 4. Notify security team
        curl -X POST https://security-team.example.com/alerts \
          -H "Content-Type: application/json" \
          -d "{\"type\": \"data_breach\", \"severity\": \"$SEVERITY\", \"timestamp\": \"$(date -Iseconds)\"}"
        ;;
        
    "unauthorized_access")
        echo "Initiating unauthorized access response..."
        # 1. Revoke compromised credentials
        kubectl delete secrets ai-agents-secrets -n ai-infrastructure
        
        # 2. Rotate service account tokens
        kubectl delete serviceaccount ai-agents-sa -n ai-infrastructure
        kubectl apply -f security/new-service-account.yaml
        
        # 3. Enable MFA requirements
        kubectl apply -f security/mfa-requirements.yaml
        ;;
        
    "malware_detected")
        echo "Initiating malware response..."
        # 1. Isolate affected pods
        kubectl cordon $(kubectl get nodes -o jsonpath='{.items[*].metadata.name}')
        
        # 2. Scan all images
        kubectl get pods -n ai-infrastructure -o jsonpath='{.items[*].spec.containers[*].image}' | \
          xargs -I {} trivy image {}
        
        # 3. Rebuild and redeploy
        kubectl delete pods -n ai-infrastructure --all
        kubectl apply -f core/resources/
        ;;
        
    *)
        echo "Unknown incident type: $INCIDENT_TYPE"
        exit 1
        ;;
esac

echo "Security incident response initiated for $INCIDENT_TYPE ($SEVERITY)"
```

## Conclusion

This security guide provides a comprehensive framework for securing the AI Agents ecosystem. By implementing these security measures, organizations can ensure the confidentiality, integrity, and availability of their AI infrastructure while maintaining compliance with regulatory requirements.

Regular security assessments, monitoring, and incident response drills are essential to maintain a strong security posture and protect against evolving threats in the AI landscape.
