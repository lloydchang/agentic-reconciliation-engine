# Git Outage Disaster Recovery Procedures

## Overview

This document provides comprehensive disaster recovery procedures specifically for Git repository outages in the GitOps Infra Control Plane. These procedures ensure continued operations and rapid recovery when Git repositories become unavailable.

## Table of Contents

1. [Outage Classification](#outage-classification)
2. [Immediate Response Procedures](#immediate-response-procedures)
3. [Automated Recovery Procedures](#automated-recovery-procedures)
4. [Manual Recovery Procedures](#manual-recovery-procedures)
5. [Communication Procedures](#communication-procedures)
6. [Post-Recovery Validation](#post-recovery-validation)
7. [Preventive Measures](#preventive-measures)
8. [Testing and Drills](#testing-and-drills)

## Outage Classification

### Severity Levels

#### Level 1 - Critical (Total Outage)
- All Git repositories unavailable
- No repository access for > 30 minutes
- Impact: Complete loss of GitOps functionality
- Response: Immediate activation of offline mode

#### Level 2 - Major (Partial Outage)
- Primary repository unavailable
- Backup repositories accessible
- Impact: Degraded GitOps functionality
- Response: Automatic failover to backup repositories

#### Level 3 - Minor (Performance Degradation)
- Slow repository response times
- Intermittent connectivity issues
- Impact: Slower reconciliation times
- Response: Monitor and optimize

### Outage Types

#### Provider Outage
- GitHub/GitLab/Gitea platform-wide issues
- Network connectivity to provider
- Provider API rate limiting

#### Repository-Specific Issues
- Repository corruption
- Authentication failures
- Repository deletion

#### Network Issues
- DNS resolution failures
- Firewall/proxy issues
- Network connectivity problems

## Immediate Response Procedures

### Step 1: Assess the Situation (0-5 minutes)

```bash
# Check repository health status
kubectl get gitrepositories -n flux-system -L gitrepo.fluxcd.io/healthy

# Check for active alerts
kubectl get events -n flux-system --field-selector type=Warning

# Check current failover status
kubectl get kustomizations -n flux-system -L fluxcd.io/offline-mode

# Check Git cache health
kubectl get service git-cache-service -n flux-system -L cache.fluxcd.io/healthy
```

### Step 2: Activate Response Plan (5-15 minutes)

#### For Level 1 Outages:
```bash
# Enable offline mode immediately
kubectl annotate kustomization infrastructure fluxcd.io/offline-mode=true --overwrite -n flux-system

# Verify offline mode is active
kubectl get kustomizations -n flux-system -l fluxcd.io/offline-mode=true

# Check that critical resources are still running
kubectl get all --all-namespaces
```

#### For Level 2 Outages:
```bash
# Check if automatic failover has occurred
kubectl get kustomizations -n flux-system -o yaml | grep sourceRef

# Manual failover if needed
kubectl patch kustomization infrastructure -n flux-system -p '{"spec":{"sourceRef":{"name":"gitops-infra-secondary"}}}' --type=merge
```

### Step 3: Notify Stakeholders (15-30 minutes)

```bash
# Create outage event
kubectl create event --namespace=flux-system \
  --type="Warning" \
  --reason="GitOutageDeclared" \
  --message="Git outage declared - activating disaster recovery procedures" \
  --source-component="disaster-recovery" \
  --involved-object-kind="Namespace" \
  --involved-object-name="flux-system"
```

## Automated Recovery Procedures

### Automatic Failover System

The system includes automated failover that activates when:

1. Primary repository fails for 3 consecutive health checks
2. Secondary repository is available
3. Tertiary repository is available as last resort

### Offline Mode Activation

Automatic offline mode activates when:

1. All repositories are unhealthy
2. Git cache is available
3. Critical infrastructure resources are present

### State Recovery

Automatic state recovery triggers when:

1. Offline mode is active
2. Critical resources are missing
3. Valid backup is available

## Manual Recovery Procedures

### Scenario 1: Complete Git Provider Outage

#### Pre-requisites:
- Git cache is available
- State backups exist
- Critical infrastructure resources are running

#### Recovery Steps:

1. **Verify Current State**
```bash
# Check what's currently running
kubectl get all --all-namespaces

# Check Git cache status
kubectl get pods -n flux-system -l app=git-cache-manager

# Check available backups
kubectl get configmaps -n flux-system -l backup.fluxcd.io/type=infrastructure-state
```

2. **Enable Offline Mode**
```bash
# Force offline mode
kubectl annotate kustomization infrastructure fluxcd.io/offline-mode=true --overwrite -n flux-system

# Switch to cached repository
kubectl patch gitrepository gitops-infra-primary -n flux-system -p '{"spec":{"url":"http://git-cache-service.flux-system.svc.cluster.local:8080/gitops-infra-control-plane"}}' --type=merge
```

3. **Restore State if Needed**
```bash
# Get latest backup
LATEST_BACKUP=$(kubectl get configmaps -n flux-system -l backup.fluxcd.io/type=infrastructure-state --sort-by=.metadata.creationTimestamp -o jsonpath='{.items[-1].metadata.labels.backup\.fluxcd\.io/timestamp}')

# Restore from backup
kubectl create job --from=cronjob/state-recovery-controller manual-recovery -n flux-system -- \
  --from-literal=BACKUP_TIMESTAMP="$LATEST_BACKUP"
```

4. **Validate Operations**
```bash
# Check Flux reconciliation
kubectl get kustomizations -n flux-system

# Check resource status
kubectl get infrastructure-resources --all-namespaces

# Monitor for errors
kubectl logs -n flux-system deployment/kustomize-controller --tail=50
```

### Scenario 2: Primary Repository Failure

#### Recovery Steps:

1. **Verify Backup Repositories**
```bash
# Check secondary repository health
kubectl get gitrepository gitops-infra-secondary -n flux-system -L gitrepo.fluxcd.io/healthy

# Check tertiary repository health
kubectl get gitrepository gitops-infra-tertiary -n flux-system -L gitrepo.fluxcd.io/healthy
```

2. **Manual Failover**
```bash
# Switch to secondary repository
kubectl patch kustomization infrastructure -n flux-system -p '{"spec":{"sourceRef":{"name":"gitops-infra-secondary"}}}' --type=merge

# Verify failover
kubectl get kustomizations -n flux-system -o yaml | grep sourceRef
```

3. **Monitor Recovery**
```bash
# Watch reconciliation progress
kubectl get kustomizations -n flux-system -w

# Check for any errors
kubectl get events -n flux-system --field-selector type=Warning
```

### Scenario 3: Git Cache Failure

#### Recovery Steps:

1. **Restart Cache Service**
```bash
# Restart cache deployment
kubectl rollout restart deployment/git-cache-manager -n flux-system

# Wait for ready state
kubectl wait --for=condition=available deployment/git-cache-manager -n flux-system --timeout=300s
```

2. **Rebuild Cache**
```bash
# Trigger cache rebuild
kubectl exec -n flux-system deployment/git-cache-manager -- git fetch --all

# Verify cache content
kubectl exec -n flux-system deployment/git-cache-manager -- ls -la /data/git-cache/
```

## Communication Procedures

### Internal Communication

#### Immediate Notifications (0-15 minutes)
- Engineering team via Slack/Teams
- Operations team via email
- Management team via incident management system

#### Status Updates (Every 30 minutes)
- Current outage status
- Recovery actions in progress
- Estimated recovery time
- Business impact assessment

### External Communication

#### Customer Notifications (If applicable)
- Service status page updates
- Customer email notifications
- Social media updates

#### Vendor Communication
- Contact Git provider support
- Report outage details
- Request ETA for resolution

## Post-Recovery Validation

### Technical Validation

1. **Repository Connectivity**
```bash
# Test all repositories
git ls-remote https://github.com/antigravity/gitops-infra-control-plane.git
git ls-remote https://gitlab.com/antigravity/gitops-infra-control-plane.git
git ls-remote https://gitea.internal/antigravity/gitops-infra-control-plane.git
```

2. **Flux Operations**
```bash
# Check reconciliation status
kubectl get kustomizations -n flux-system

# Verify latest commits are applied
kubectl get kustomizations -n flux-system -o yaml | grep lastAppliedRevision

# Test new commit application
git commit --allow-empty -m "Test commit after recovery"
git push origin main
```

3. **Infrastructure State**
```bash
# Verify all resources are present
kubectl get all --all-namespaces

# Check for configuration drift
kubectl get infrastructure-resources --all-namespaces

# Validate resource health
kubectl get pods --all-namespaces -o wide
```

### Business Validation

1. **Application Functionality**
- Verify all applications are running
- Test critical user workflows
- Check monitoring dashboards

2. **Performance Validation**
- Verify response times are normal
- Check error rates are acceptable
- Validate resource utilization

## Preventive Measures

### Architecture Improvements

1. **Multi-Repository Strategy**
- Primary: GitHub
- Secondary: GitLab
- Tertiary: Self-hosted Gitea

2. **Local Git Cache**
- In-cluster repository cache
- Automatic synchronization
- Offline operation capability

3. **State Persistence**
- Regular state backups
- Multiple backup locations
- Automated recovery procedures

### Monitoring Improvements

1. **Health Monitoring**
- Repository health checks
- Performance monitoring
- Automated alerting

2. **Capacity Planning**
- Resource utilization monitoring
- Scalability testing
- Performance optimization

### Process Improvements

1. **Regular Testing**
- Monthly outage drills
- Quarterly full recovery tests
- Annual disaster recovery exercises

2. **Documentation Updates**
- Regular procedure reviews
- Contact list updates
- Escalation path validation

## Testing and Drills

### Monthly Outage Drills

#### Scenario 1: Primary Repository Outage
1. Simulate primary repository failure
2. Verify automatic failover to secondary
3. Test manual recovery procedures
4. Validate business continuity

#### Scenario 2: Complete Git Outage
1. Simulate all repository failures
2. Activate offline mode
3. Test state recovery procedures
4. Validate cache operations

### Quarterly Full Recovery Tests

#### Test Objectives
- Validate all recovery procedures
- Test communication protocols
- Verify team readiness
- Identify improvement opportunities

#### Test Scenarios
- Extended outage (4+ hours)
- Multiple concurrent failures
- Network connectivity issues
- Authentication failures

### Annual Disaster Recovery Exercises

#### Comprehensive Testing
- Full system outage simulation
- Cross-team coordination
- External vendor interaction
- Customer communication testing

## Emergency Contacts

### Internal Contacts
- **Technical Lead**: [Contact Information]
- **Engineering Manager**: [Contact Information]
- **Incident Commander**: [Contact Information]

### External Contacts
- **GitHub Support**: [Contact Information]
- **GitLab Support**: [Contact Information]
- **Cloud Provider Support**: [Contact Information]

### Escalation Matrix
| Severity | Response Time | Escalation Path |
|----------|---------------|-----------------|
| Critical | 15 minutes | Technical Lead → Engineering Manager → Director |
| Major | 1 hour | Technical Lead → Engineering Manager |
| Minor | 4 hours | Engineering Team |

## Runbooks

### Quick Reference Commands

```bash
# Check repository health
kubectl get gitrepositories -n flux-system -L gitrepo.fluxcd.io/healthy

# Enable offline mode
kubectl annotate kustomization infrastructure fluxcd.io/offline-mode=true --overwrite -n flux-system

# Manual failover to secondary
kubectl patch kustomization infrastructure -n flux-system -p '{"spec":{"sourceRef":{"name":"gitops-infra-secondary"}}}' --type=merge

# Restore from backup
kubectl create job --from=cronjob/state-recovery-controller manual-recovery -n flux-system

# Check health dashboard
kubectl port-forward -n flux-system service/git-health-dashboard 8080:8080
```

### Decision Trees

#### Repository Unavailable Decision Tree
```
Is primary repository healthy?
├── No → Is secondary repository healthy?
│   ├── No → Is tertiary repository healthy?
│   │   ├── No → Enable offline mode
│   │   └── Yes → Failover to tertiary
│   └── Yes → Failover to secondary
└── Yes → Continue normal operations
```

#### Recovery Decision Tree
```
Git repository recovered?
├── Yes → Is offline mode active?
│   ├── No → Continue normal operations
│   └── Yes → Disable offline mode, switch back to primary
└── No → Continue in current mode, monitor for recovery
```

## Conclusion

This disaster recovery plan provides comprehensive procedures for handling Git repository outages in the GitOps Infra Control Plane. Regular testing and updates to these procedures ensure the system remains resilient and can quickly recover from Git-related disruptions.

The combination of automated failover, offline mode capabilities, state persistence, and comprehensive monitoring provides multiple layers of protection against Git repository failures, ensuring continuous operations even during extended outages.
