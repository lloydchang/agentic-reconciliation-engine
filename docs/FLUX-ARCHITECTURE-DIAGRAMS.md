# Flux Architecture Diagrams

This document contains architectural diagrams and visual representations of Flux CD components and data flows for the GitOps Infra Control Plane.

## System Architecture Overview

```mermaid
graph TB
    subgraph "External Systems"
        GH[GitHub Repository]
        REG[Container Registry]
        SLACK[Slack/Teams]
    end
    
    subgraph "Kubernetes Cluster"
        subgraph "flux-system Namespace"
            SC[Source Controller]
            KC[Kustomize Controller]
            HC[Helm Controller]
            NC[Notification Controller]
            IRC[Image Reflector Controller]
            IAC[Image Automation Controller]
        end
        
        subgraph "Application Namespaces"
            NET[Network Resources]
            CLUST[Cluster Resources]
            WORK[Workloads]
        end
        
        subgraph "Kubernetes API"
            API[Kubernetes API Server]
        end
    end
    
    %% Data Flow
    GH -->|Webhook| NC
    GH -->|Git Pull| SC
    REG -->|Image Scan| IRC
    SC -->|Artifacts| KC
    SC -->|Charts| HC
    KC -->|Manifests| API
    HC -->|Helm Releases| API
    API -->|Deploy| NET
    API -->|Deploy| CLUST
    API -->|Deploy| WORK
    NC -->|Notifications| SLACK
    IRC -->|Image Metadata| IAC
    IAC -->|Git Updates| GH
    
    %% Styling
    classDef controller fill:#e1f5fe
    classDef external fill:#f3e5f5
    classDef k8s fill:#e8f5e8
    class SC,KC,HC,NC,IRC,IAC controller
    class GH,REG,SLACK external
    class NET,CLUST,WORK,API k8s
```

## Component Interaction Flow

```mermaid
sequenceDiagram
    participant Dev as Developer
    participant Git as Git Repository
    participant Rec as Flux Receiver
    participant SC as Source Controller
    participant KC as Kustomize Controller
    participant HC as Helm Controller
    participant API as K8s API
    participant NC as Notification Controller
    participant Slack as Slack
    
    Dev->>Git: git push
    Git->>Rec: Webhook Event
    Rec->>SC: Trigger Reconciliation
    SC->>Git: Fetch Latest Commit
    Git-->>SC: Source Content
    SC->>SC: Create Artifact (.tar.gz)
    SC->>KC: Artifact Ready
    SC->>HC: Chart Ready
    
    par Kustomize Flow
        KC->>KC: Build Manifests
        KC->>KC: Decrypt Secrets
        KC->>KC: Validate Resources
        KC->>API: Server-Side Apply
    and Helm Flow
        HC->>HC: Render Chart
        HC->>HC: Apply Values
        HC->>API: Helm Install/Upgrade
    end
    
    API->>API: Deploy Resources
    API-->>KC: Deployment Status
    API-->>HC: Release Status
    KC->>NC: Emit Events
    HC->>NC: Emit Events
    NC->>Slack: Send Notifications
    NC->>Git: Update Commit Status
```

## Source Controller Architecture

```mermaid
graph TB
    subgraph "Source Controller"
        subgraph "Input Sources"
            GR[GitRepository]
            BR[Bucket]
            HR[HelmRepository]
            OR[OCIRepository]
        end
        
        subgraph "Processing Layer"
            AUTH[Authentication]
            VERIFY[Signature Verification]
            FILTER[Content Filtering]
            COMPRESS[Artifact Creation]
        end
        
        subgraph "Storage Layer"
            CACHE[Local Cache]
            ART[Artifact Storage]
        end
        
        subgraph "Output Services"
            SVC[Artifact Service]
            WEB[Webhook Handler]
        end
    end
    
    GR --> AUTH
    BR --> AUTH
    HR --> AUTH
    OR --> AUTH
    
    AUTH --> VERIFY
    VERIFY --> FILTER
    FILTER --> COMPRESS
    COMPRESS --> CACHE
    CACHE --> ART
    ART --> SVC
    
    WEB -->|Trigger| AUTH
    
    %% Styling
    classDef source fill:#fff3e0
    classDef process fill:#e8f5e8
    classDef storage fill:#f3e5f5
    classDef output fill:#e1f5fe
    class GR,BR,HR,OR source
    class AUTH,VERIFY,FILTER,COMPRESS process
    class CACHE,ART storage
    class SVC,WEB output
```

## Kustomize Controller Workflow

```mermaid
flowchart TD
    START([Start]) --> EVENT[Reconciliation Trigger]
    EVENT --> FETCH[Fetch Artifact]
    FETCH --> BUILD[Build Kustomize]
    BUILD --> DECRYPT{Secrets to Decrypt?}
    DECRYPT -->|Yes| DECRYPT_PROC[Decrypt with SOPS]
    DECRYPT -->|No| VALIDATE
    DECRYPT_PROC --> VALIDATE[Validate Resources]
    VALIDATE --> DEPENDS{Dependencies Ready?}
    DEPENDS -->|No| WAIT_DEPS[Wait for Dependencies]
    DEPENDS -->|Yes| APPLY
    WAIT_DEPS --> DEPENDS
    APPLY --> SERVER_APPLY[Server-Side Apply]
    SERVER_APPLY --> HEALTH{Health Checks Enabled?}
    HEALTH -->|Yes| WAIT_HEALTH[Wait for Readiness]
    HEALTH -->|No| PRUNE_CHECK
    WAIT_HEALTH --> PRUNE_CHECK{Prune Enabled?}
    PRUNE_CHECK -->|Yes| PRUNE[Garbage Collection]
    PRUNE_CHECK -->|No| SUCCESS[Reconciliation Success]
    PRUNE --> SUCCESS
    SUCCESS --> EVENT
    
    %% Styling
    classDef process fill:#e8f5e8
    classDef decision fill:#fff3e0
    classDef success fill:#e8f5e8
    class BUILD,DECRYPT_PROC,VALIDATE,SERVER_APPLY,PRUNE process
    class DECRYPT,DEPENDS,HEALTH,PRUNE_CHECK decision
    class SUCCESS success
```

## Helm Controller Architecture

```mermaid
graph TB
    subgraph "Helm Controller"
        subgraph "Input Sources"
            HR[HelmRepository]
            GR[GitRepository]
            OR[OCIRepository]
        end
        
        subgraph "Chart Processing"
            CHART[Chart Acquisition]
            VALUES[Values Processing]
            RENDER[Template Rendering]
            POST[Post-Rendering]
        end
        
        subgraph "Helm Operations"
            INSTALL[Helm Install]
            UPGRADE[Helm Upgrade]
            ROLLBACK[Helm Rollback]
            TEST[Helm Test]
            UNINSTALL[Helm Uninstall]
        end
        
        subgraph "Lifecycle Management"
            HOOKS[Chart Hooks]
            HEALTH[Health Assessment]
            STATUS[Status Reporting]
        end
    end
    
    HR --> CHART
    GR --> CHART
    OR --> CHART
    
    CHART --> VALUES
    VALUES --> RENDER
    RENDER --> POST
    POST --> INSTALL
    POST --> UPGRADE
    
    INSTALL --> HOOKS
    UPGRADE --> HOOKS
    
    HOOKS --> HEALTH
    HEALTH --> STATUS
    
    %% Error handling
    INSTALL -->|Failure| ROLLBACK
    UPGRADE -->|Failure| ROLLBACK
    
    %% Testing
    INSTALL --> TEST
    UPGRADE --> TEST
    
    %% Styling
    classDef source fill:#fff3e0
    classDef process fill:#e8f5e8
    classDef operation fill:#e1f5fe
    classDef lifecycle fill:#f3e5f5
    class HR,GR,OR source
    class CHART,VALUES,RENDER,POST process
    class INSTALL,UPGRADE,ROLLBACK,TEST,UNINSTALL operation
    class HOOKS,HEALTH,STATUS lifecycle
```

## Image Automation Flow

```mermaid
sequenceDiagram
    participant REG as Container Registry
    participant IRC as Image Reflector
    participant IP as Image Policy
    participant IAC as Image Automation
    participant GIT as Git Repository
    participant SC as Source Controller
    participant KC as Kustomize Controller
    participant K8s as Kubernetes
    
    REG->>IRC: New Image Pushed
    IRC->>IRC: Scan Repository Tags
    IRC->>IP: Update Image Metadata
    IP->>IP: Apply Policy Rules
    IP->>IAC: Policy Match Found
    IAC->>GIT: Clone Repository
    IAC->>IAC: Update Manifests
    IAC->>GIT: Commit Changes
    GIT->>SC: Webhook Trigger
    SC->>GIT: Fetch Updated Content
    SC->>KC: New Artifact Ready
    KC->>KC: Build Updated Manifests
    KC->>K8s: Apply New Image
    K8s->>K8s: Rolling Update
```

## Network Security Architecture

```mermaid
graph TB
    subgraph "flux-system Namespace"
        subgraph "Controllers"
            SC[Source Controller]
            KC[Kustomize Controller]
            HC[Helm Controller]
            NC[Notification Controller]
            IRC[Image Reflector]
            IAC[Image Automation]
        end
        
        subgraph "Network Policies"
            NP1[allow-scraping]
            NP2[allow-webhooks] 
            NP3[allow-egress]
            NP4[deny-ingress]
        end
        
        subgraph "Services"
            SVC1[Source Service:8080]
            SVC2[Webhook Service:9292]
            SVC3[Metrics Services]
        end
    end
    
    subgraph "External"
        EXT[External Systems]
        PROM[Prometheus]
        WEBHOOK[Webhook Sources]
    end
    
    subgraph "Other Namespaces"
        OTHER[Other Workloads]
    end
    
    %% Network Flows
    NP1 -.->|Allow Metrics| PROM
    NP2 -.->|Allow Webhooks| WEBHOOK
    NP3 -.->|Allow Egress| EXT
    NP4 -.->|Deny Ingress| OTHER
    
    SVC1 --> NP1
    SVC2 --> NP2
    SC --> NP3
    KC --> NP3
    HC --> NP3
    
    %% Styling
    classDef controller fill:#e1f5fe
    classDef policy fill:#fff3e0
    classDef service fill:#e8f5e8
    classDef external fill:#f3e5f5
    class SC,KC,HC,NC,IRC,IAC controller
    class NP1,NP2,NP3,NP4 policy
    class SVC1,SVC2,SVC3 service
    class EXT,PROM,WEBHOOK,OTHER external
```

## Multi-Cluster Architecture

```mermaid
graph TB
    subgraph "Git Repository"
        GIT[Git Source]
        MANIFESTS[Cluster Manifests]
    end
    
    subgraph "Hub Cluster"
        MGMT_FLUX[Flux Controllers]
        MGMT_KUBE[Kubernetes API]
    end
    
    subgraph "Production Cluster"
        PROD_KUBE[Production K8s API]
        PROD_WORKLOADS[Production Workloads]
    end
    
    subgraph "Staging Cluster"
        STAGE_KUBE[Staging K8s API]
        STAGE_WORKLOADS[Staging Workloads]
    end
    
    subgraph "Development Cluster"
        DEV_KUBE[Dev K8s API]
        DEV_WORKLOADS[Dev Workloads]
    end
    
    GIT --> MGMT_FLUX
    MGMT_FLUX --> MANIFESTS
    MANIFESTS --> MGMT_KUBE
    
    MGMT_FLUX -->|Remote Apply| PROD_KUBE
    MGMT_FLUX -->|Remote Apply| STAGE_KUBE
    MGMT_FLUX -->|Remote Apply| DEV_KUBE
    
    PROD_KUBE --> PROD_WORKLOADS
    STAGE_KUBE --> STAGE_WORKLOADS
    DEV_KUBE --> DEV_WORKLOADS
    
    %% Styling
    classDef git fill:#f3e5f5
    classDef mgmt fill:#e1f5fe
    classDef cluster fill:#e8f5e8
    classDef workload fill:#fff3e0
    class GIT,MANIFESTS git
    class MGMT_FLUX,MGMT_KUBE mgmt
    class PROD_KUBE,STAGE_KUBE,DEV_KUBE cluster
    class PROD_WORKLOADS,STAGE_WORKLOADS,DEV_WORKLOADS workload
```

## Event Flow Architecture

```mermaid
flowchart LR
    subgraph "Event Sources"
        GIT_WEBHOOK[Git Webhook]
        REG_WEBHOOK[Registry Webhook]
        MANUAL[Manual Trigger]
        SCHEDULE[Scheduled Reconcile]
    end
    
    subgraph "Event Processing"
        REC[Flux Receiver]
        QUEUE[Event Queue]
        ROUTER[Event Router]
    end
    
    subgraph "Event Handlers"
        SC[Source Controller]
        KC[Kustomize Controller]
        HC[Helm Controller]
        IRC[Image Reflector]
        IAC[Image Automation]
    end
    
    subgraph "Event Outputs"
        K8S_EVENTS[Kubernetes Events]
        NOTIFICATIONS[External Notifications]
        STATUS_UPDATES[Status Updates]
        METRICS[Prometheus Metrics]
    end
    
    GIT_WEBHOOK --> REC
    REG_WEBHOOK --> REC
    MANUAL --> QUEUE
    SCHEDULE --> QUEUE
    
    REC --> QUEUE
    QUEUE --> ROUTER
    
    ROUTER --> SC
    ROUTER --> KC
    ROUTER --> HC
    ROUTER --> IRC
    ROUTER --> IAC
    
    SC --> K8S_EVENTS
    KC --> K8S_EVENTS
    HC --> K8S_EVENTS
    IRC --> K8S_EVENTS
    IAC --> K8S_EVENTS
    
    K8S_EVENTS --> NOTIFICATIONS
    K8S_EVENTS --> STATUS_UPDATES
    K8S_EVENTS --> METRICS
    
    %% Styling
    classDef source fill:#fff3e0
    classDef process fill:#e8f5e8
    classDef handler fill:#e1f5fe
    classDef output fill:#f3e5f5
    class GIT_WEBHOOK,REG_WEBHOOK,MANUAL,SCHEDULE source
    class REC,QUEUE,ROUTER process
    class SC,KC,HC,IRC,IAC handler
    class K8S_EVENTS,NOTIFICATIONS,STATUS_UPDATES,METRICS output
```

## Security and Trust Flow

```mermaid
sequenceDiagram
    participant Dev as Developer
    participant Git as Git Repository
    participant SC as Source Controller
    participant KC as Kustomize Controller
    participant K8s as Kubernetes
    participant Monitor as Security Monitor
    
    Dev->>Git: Push Signed Commit
    Git->>SC: Provide Signed Content
    SC->>SC: Verify PGP Signature
    SC->>KC: Verified Artifact
    KC->>KC: Decrypt SOPS Secrets
    KC->>KC: Validate Resources
    KC->>K8s: Apply Validated Resources
    K8s->>Monitor: Security Events
    Monitor->>Monitor: Audit & Alert
    
    Note over Dev,Monitor: All steps are logged and audited
```

## Performance Optimization Architecture

```mermaid
graph TB
    subgraph "Optimization Layers"
        subgraph "Source Optimization"
            IGNORE[.sourceignore]
            CACHE[Artifact Cache]
            WEBHOOK[Webhook Triggers]
        end
        
        subgraph "Controller Optimization"
            PARALLEL[Parallel Reconciliation]
            DEPS[Dependency Ordering]
            BATCH[Batch Processing]
        end
        
        subgraph "Cluster Optimization"
            SSA[Server-Side Apply]
            HEALTH[Health Checks]
            PRUNE[Garbage Collection]
        end
        
        subgraph "Resource Optimization"
            LIMITS[Resource Limits]
            HPA[Horizontal Scaling]
            METRICS[Performance Metrics]
        end
    end
    
    IGNORE --> CACHE
    CACHE --> WEBHOOK
    
    WEBHOOK --> PARALLEL
    PARALLEL --> DEPS
    DEPS --> BATCH
    
    BATCH --> SSA
    SSA --> HEALTH
    HEALTH --> PRUNE
    
    PRUNE --> LIMITS
    LIMITS --> HPA
    HPA --> METRICS
    
    %% Styling
    classDef source fill:#fff3e0
    classDef controller fill:#e8f5e8
    classDef cluster fill:#e1f5fe
    classDef resource fill:#f3e5f5
    class IGNORE,CACHE,WEBHOOK source
    class PARALLEL,DEPS,BATCH controller
    class SSA,HEALTH,PRUNE cluster
    class LIMITS,HPA,METRICS resource
```

## Troubleshooting Flow Diagram

```mermaid
flowchart TD
    ISSUE[Issue Detected] --> CHECK{Type of Issue}
    
    CHECK -->|Source| SOURCE_CHECK[Check GitRepository]
    CHECK -->|Kustomization| KUST_CHECK[Check Kustomization]
    CHECK -->|Helm| HELM_CHECK[Check HelmRelease]
    CHECK -->|Image| IMG_CHECK[Check Image Automation]
    
    SOURCE_CHECK --> GIT_STATUS[Git Repository Status]
    GIT_STATUS --> GIT_AUTH{Authentication OK?}
    GIT_AUTH -->|No| GIT_CREDS[Check Credentials]
    GIT_AUTH -->|Yes| GIT_ACCESS{Repository Accessible?}
    GIT_ACCESS -->|No| GIT_NET[Check Network]
    GIT_ACCESS -->|Yes| GIT_ARTIFACT[Check Artifact]
    
    KUST_CHECK --> KUST_STATUS[Kustomization Status]
    KUST_STATUS --> KUST_BUILD{Build Successful?}
    KUST_BUILD -->|No| KUST_SYNTAX[Check Syntax]
    KUST_BUILD -->|Yes| KUST_DEPS{Dependencies Ready?}
    KUST_DEPS -->|No| KUST_WAIT[Wait for Dependencies]
    KUST_DEPS -->|Yes| KUST_APPLY[Check Apply Status]
    
    HELM_CHECK --> HELM_STATUS[HelmRelease Status]
    HELM_STATUS --> HELM_CHART{Chart Available?}
    HELM_CHART -->|No| HELM_REPO[Check Repository]
    HELM_CHART -->|Yes| HELM_VALUES[Validate Values]
    HELM_VALUES --> HELM_DEPLOY[Check Deployment]
    
    IMG_CHECK --> IMG_STATUS[Image Automation Status]
    IMG_STATUS --> IMG_POLICY{Policy Match?}
    IMG_POLICY -->|No| IMG_RULES[Check Policy Rules]
    IMG_POLICY -->|Yes| IMG_GIT[Git Operations]
    
    GIT_CREDS --> RESOLVED[Issue Resolved]
    GIT_NET --> RESOLVED
    GIT_ARTIFACT --> RESOLVED
    KUST_SYNTAX --> RESOLVED
    KUST_WAIT --> RESOLVED
    KUST_APPLY --> RESOLVED
    HELM_REPO --> RESOLVED
    HELM_VALUES --> RESOLVED
    HELM_DEPLOY --> RESOLVED
    IMG_RULES --> RESOLVED
    IMG_GIT --> RESOLVED
    
    %% Styling
    classDef issue fill:#ffebee
    classDef check fill:#fff3e0
    classDef status fill:#e8f5e8
    classDef decision fill:#e1f5fe
    classDef success fill:#e8f5e8
    class ISSUE issue
    class CHECK,SOURCE_CHECK,KUST_CHECK,HELM_CHECK,IMG_CHECK check
    class GIT_STATUS,KUST_STATUS,HELM_STATUS,IMG_STATUS status
    class GIT_AUTH,GIT_ACCESS,KUST_BUILD,HELM_CHART,IMG_POLICY decision
    class RESOLVED success
```

These diagrams provide comprehensive visual representations of Flux CD architecture, data flows, and operational patterns for the GitOps Infra Control Plane. They can be used for documentation, training, and troubleshooting purposes.
