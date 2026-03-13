# Running Kubernetes Jobs with Flux

## Overview

Additional considerations have to be made when managing Kubernetes Jobs with Flux. By default, if you were to have Flux reconcile a Job resource, it would apply it once to the cluster, the Job would create a Pod that can either error or run to completion. Attempting to update the Job manifest after it has been applied to the cluster will not be allowed, as changes to the Job `spec.Completions`, `spec.Selector` and `spec.Template` are not permitted by the Kubernetes API. To be able to update a Kubernetes Job, the Job has to be recreated by first being removed and then reapplied to the cluster.

## Repository Structure

A typical use case for running Kubernetes Jobs with Flux is to implement pre-deployment tasks for e.g. database schema migration and post-deployment jobs (like cache refresh).

This requires separate Flux Kustomization resources that depend on each other: one for running the pre-deployment Jobs, one to deploy the application, and a 3rd one for running the post-deployment Jobs.

Example of an application configuration repository:

```
├── pre-deploy
│   └── migration.job.yaml
├── deploy
│   ├── deployment.yaml
│   ├── ingress.yaml
│   └── service.yaml
├── post-deploy
│   └── cache.job.yaml
└── flux
    ├── pre-deploy.yaml
    ├── deploy.yaml
    └── post-deploy.yaml
```

## Configure the Deployment Pipeline

### Pre-Deployment Job

Given a Job in the path `./pre-deploy/migration.job.yaml`:

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: db-migration
spec:
  template:
    spec:
      restartPolicy: Never
      containers:
      - name: migration
        image: ghcr.io/org/my-app:v1.0.0
        command:
          - sh
          - -c
          - echo "starting db migration"
```

And a Flux Kustomization that reconciles it at `./flux/pre-deploy.yaml`:

```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: app-pre-deploy
spec:
  sourceRef:
    kind: GitRepository
    name: my-app
  path: "./pre-deploy/"
  interval: 60m
  timeout: 5m
  prune: true
  wait: true
  force: true
```

Setting `spec.force` to `true` will make Flux recreate the Job when any immutable field is changed, forcing the Job to run every time the container image tag changes. Setting `spec.wait` to `true` makes Flux wait for the Job to complete before it is considered ready.

### Application Deployment

To deploy the application after the migration job, we define a Flux Kustomization that depends on the migration one.

Example of `./flux/deploy.yaml`:

```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: app-deploy
spec:
  dependsOn:
    - name: app-pre-deploy
  sourceRef:
    kind: GitRepository
    name: my-app
  path: "./deploy/"
  interval: 60m
  timeout: 5m
  prune: true
  wait: true
```

This means that the `app-deploy` Kustomization will wait until all the Jobs in `app-pre-deploy` run to completion. If the Job fails, the app changes will not be applied by the `app-deploy` Kustomization.

### Post-Deployment Job

And finally we can define a Flux Kustomization that depends on `app-deploy` to run Kubernetes Jobs after the application was upgraded.

Example of `./flux/post-deploy.yaml`:

```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: app-post-deploy
spec:
  dependsOn:
    - name: app-deploy
  sourceRef:
    kind: GitRepository
    name: my-app
  path: "./post-deploy/"
  interval: 60m
  timeout: 5m
  prune: true
  wait: true
  force: true
```

## How It Works

This configuration works best when the Jobs are using the same image and tag as the application being deployed. When a new version of the application is deployed, the image tags are updated. The update of the image tag will force a recreation of the Jobs. The application will be updated after the pre-deployment Jobs have run successfully, and the post-deployment Jobs will execute only if the app rolling update has completed.

## Key Configuration Options

### Force Recreation
- `spec.force: true` - Forces recreation of Jobs when immutable fields change
- Required for Jobs to run on every deployment

### Wait for Completion
- `spec.wait: true` - Makes Flux wait for Job completion before marking Kustomization as ready
- Ensures proper sequencing of deployment phases

### Dependencies
- `spec.dependsOn` - Creates dependency chains between Kustomizations
- Ensures pre-deploy runs before deploy, and deploy before post-deploy

## Repository Integration

This Job management pattern is designed to work seamlessly with the GitOps Infra Control Plane. The platform includes comprehensive job scheduling and dependency management capabilities.

### Integration with GitOps Control Plane

```yaml
# Example: Pre-deploy database migration job
apiVersion: batch/v1
kind: Job
metadata:
  name: db-migration
spec:
  template:
    spec:
      restartPolicy: Never
      containers:
      - name: migration
        image: my-app:v1.0.0
        env:
        - name: DB_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
---
# Flux Kustomization with dependency management
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: app-pre-deploy
spec:
  sourceRef:
    kind: GitRepository
    name: my-app
  path: "./pre-deploy/"
  wait: true
  force: true
  dependsOn: []
---
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: app-deploy
spec:
  dependsOn:
    - name: app-pre-deploy
  sourceRef:
    kind: GitRepository
    name: my-app
  path: "./deploy/"
  wait: true
```

## Use Cases

### Database Migrations
- Schema updates before application deployment
- Data transformations and seeding
- Backup operations

### Cache Management
- Cache warming after deployment
- Cache invalidation for stale data
- CDN purges

### Integration Testing
- API contract validation
- External service connectivity tests
- Performance baseline establishment

### Cleanup Operations
- Temporary file removal
- Log rotation
- Resource cleanup

## Best Practices

1. **Use Immutable Fields Wisely**: Leverage `spec.force: true` to ensure Jobs run on every deployment
2. **Proper Dependencies**: Use `dependsOn` to create clear deployment pipelines
3. **Resource Limits**: Set appropriate CPU/memory limits for Job containers
4. **Timeouts**: Configure reasonable `spec.timeout` values for Job completion
5. **Error Handling**: Design Jobs to fail fast on errors rather than hanging
6. **Logging**: Ensure Job logs are captured for debugging deployment issues

## Troubleshooting

### Common Issues

1. **Job Not Updating**: Ensure `spec.force: true` is set for Jobs that need to run on every deployment
2. **Dependency Deadlock**: Check that Kustomization dependencies don't create circular references
3. **Timeout Issues**: Adjust `spec.timeout` values based on expected Job runtime
4. **Resource Constraints**: Monitor cluster resources during Job execution

### Verification Commands

```bash
# Check Kustomization status
flux get kustomizations

# View Job execution
kubectl get jobs
kubectl get pods -l job-name=<job-name>

# Check Job logs
kubectl logs job/<job-name>
```

Last modified 2023-08-24: Fix API links (db9fb9a)
