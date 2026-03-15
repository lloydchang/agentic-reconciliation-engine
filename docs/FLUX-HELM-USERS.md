# Flux for Helm Users

## Welcome Helm Users

We think Flux's Helm Controller is a good way to do Helm according to GitOps principles, and we're dedicated to doing what we can to help you feel the same way.

## What Does Flux Add to Helm?

Helm 3 was designed with both a client and an SDK, but no running software agents. This architecture intended anything outside of the client scope to be addressed by other tools in the ecosystem, which could then make use of Helm's SDK.

Built on Kubernetes controller-runtime, Flux's Helm Controller is an example of a mature software agent that uses Helm's SDK to full effect.

Flux's biggest addition to Helm is a structured declaration layer for your releases that automatically gets reconciled to your cluster based on your configured rules:

- **While the Helm client commands let you imperatively do things**
- **Flux Helm Custom Resources let you declare what you want the Helm SDK to do automatically**

Additional benefits Flux adds to Helm include:

- Managing / structuring multiple environments
- A control loop, with configurable retry logic
- Automated drift detection between the desired and actual state of your operations
- Automated responses to that drift, including reconciliation, notifications, and unified logging

## Getting Started

The simplest way to explain is by example. Let's translate imperative Helm commands to Flux Helm Controller Custom Resources:

### Helm Client Commands

```bash
helm repo add traefik https://helm.traefik.io/traefik
helm install my-traefik traefik/traefik \
  --version 9.18.2 \
  --namespace traefik
```

### Flux Client Commands

```bash
flux create source helm traefik --url https://helm.traefik.io/traefik --namespace traefik
flux create helmrelease my-traefik --chart traefik \
  --source HelmRepository/traefik \
  --chart-version 9.18.2 \
  --namespace traefik
```

The main difference is that the Flux client will not imperatively create resources in the cluster. Instead, these commands create Custom Resource files, which are committed to version control as instructions only (note: you may use the `--export` flag to manage any file edits with finer grained control before pushing to version control). Separately, the Flux Helm Controller automatically reconciles these instructions with the running state of your cluster based on your configured rules.

Let's check out what the Custom Resource files look like:

### HelmRepository Resource

```yaml
# /flux/boot/traefik/helmrepo.yaml
apiVersion: source.toolkit.fluxcd.io/v1beta2
kind: HelmRepository
metadata:
  name: traefik
  namespace: traefik
spec:
  interval: 1m0s
  url: https://helm.traefik.io/traefik
```

### HelmRelease Resource

```yaml
# /flux/boot/traefik/helmrelease.yaml
apiVersion: helm.toolkit.fluxcd.io/v2beta1
kind: HelmRelease
metadata:
  name: my-traefik
  namespace: traefik
spec:
  chart:
    spec:
      chart: traefik
      sourceRef:
        kind: HelmRepository
        name: traefik
      version: 9.18.2
  interval: 1m0s
```

Once these are applied to your cluster, the Flux Helm Controller automatically uses the Helm SDK to do your bidding according to the rules you've set.

Why is this important? If you or your team has ever collaborated with multiple engineers on one or more apps, and/or in more than one namespace or cluster, you probably have a good idea of how declarative, automatic reconciliation can help solve common problems. If not, or either way, you may want to check out this short introduction to GitOps.

## Customizing Your Release

While Helm charts are usually installable using default configurations, users will often customize charts with their preferred configuration by overriding the default values. The Helm client allows this by imperatively specifying override values with `--set` on the command line, and in additional `--values` files. For example:

```bash
helm install my-traefik traefik/traefik --set service.type=ClusterIP
```

and

```bash
helm install my-traefik traefik/traefik --values ci/kind-values.yaml
```

where `ci/kind-values.yaml` contains:

```yaml
service:
  type: ClusterIP
```

Flux Helm Controller allows these same YAML values overrides on the HelmRelease CRD. These can be declared directly in `spec.values`:

```yaml
spec:
  values:
    service:
      type: ClusterIP
```

and defined in `spec.valuesFrom` as a list of ConfigMap and Secret resources from which to draw values, allowing reusability and/or greater security. See HelmRelease CRD values overrides documentation for the latest spec.

## Managing Secrets and ConfigMaps

You may manage these ConfigMap and Secret resources any way you wish, but there are several benefits to managing these with the Flux Kustomize Controller.

It is fairly straightforward to use Kustomize `configMapGenerator` to trigger a Helm release upgrade every time the encoded values change. This common use case currently solvable in Helm by adding specially crafted annotations to a chart. The Flux Kustomize Controller method allows you to accomplish this on any chart without additional templated annotations.

You may also use Kustomize Controller built-in Mozilla SOPS integration to securely manage your encrypted secrets stored in git. See the Flux SOPS guide for step-by-step instructions through various use cases.

## Automatic Release Upgrades

If you want Helm Controller to automatically upgrade your releases when a new chart version is available in the release's referenced HelmRepository, you may specify a SemVer range (i.e. `>=4.0.0 <5.0.0`) instead of a fixed version.

This is useful if your release should use a fixed MAJOR chart version, but want the latest MINOR or PATCH versions as they become available.

For full SemVer range syntax, see [Masterminds/semver](https://github.com/Masterminds/semver#basic-comparisons) Checking Version Constraints documentation.

## Automatic Uninstalls and Rollback

The Helm Controller offers an extensive set of configuration options to remediate when a Helm release fails, using `spec.install.remediation`, `spec.upgrade.remediation`, `spec.rollback` and `spec.uninstall`. Features include the option to remediate with an uninstall after an upgrade failure, and the option to keep a failed release for debugging purposes when it has run out of retries.

### Install Remediation Example

```yaml
apiVersion: helm.toolkit.fluxcd.io/v2beta1
kind: HelmRelease
metadata:
  name: my-release
  namespace: default
spec:
  # ...omitted for brevity
  install:
    # Remediation configuration for when the Helm install
    # (or sequent Helm test) action fails
    remediation:
      # Number of retries that should be attempted on failures before
      # bailing, a negative integer equals to unlimited retries
      retries: -1
  # Configuration options for the Helm uninstall action
  uninstall:
    timeout: 5m
    disableHooks: false
    keepHistory: false
```

### Upgrade Remediation and Rollback Example

```yaml
apiVersion: helm.toolkit.fluxcd.io/v2beta1
kind: HelmRelease
metadata:
  name: my-release
  namespace: default
spec:
  # ...omitted for brevity
  upgrade:
    # Remediation configuration for when an Helm upgrade action fails
    remediation:
      # Amount of retries to attempt after a failure,
      # setting this to 0 means no remediation will be
      # attempted
      retries: 5
  # Configuration options for the Helm rollback action
  rollback:
    timeout: 5m
    disableWait: false
    disableHooks: false
    recreate: false
    force: false
    cleanupOnFail: false
```

## Repository Integration

This Helm integration is designed to work seamlessly with the GitOps Infra Control Plane. The platform provides comprehensive Helm chart management capabilities.

### Integration with GitOps Control Plane

```yaml
# Example: Helm release management with Flux
apiVersion: source.toolkit.fluxcd.io/v1beta2
kind: HelmRepository
metadata:
  name: my-app
  namespace: flux-system
spec:
  interval: 1m0s
  url: https://charts.my-org.com
---
apiVersion: helm.toolkit.fluxcd.io/v2beta1
kind: HelmRelease
metadata:
  name: my-app
  namespace: default
spec:
  interval: 5m
  chart:
    spec:
      chart: my-app
      version: ">=1.0.0 <2.0.0"  # Automatic upgrades within major version
      sourceRef:
        kind: HelmRepository
        name: my-app
  values:
    image:
      tag: v1.0.0
    service:
      type: ClusterIP
  valuesFrom:
  - kind: ConfigMap
    name: my-app-config
    valuesKey: values.yaml
  - kind: Secret
    name: my-app-secrets
    valuesKey: secrets.yaml
```

## Benefits for Helm Users

### Declarative Management

- Define Helm releases as code in Git
- Automatic reconciliation and drift detection
- Version control for all Helm operations

### Multi-Environment Support

- Consistent Helm release management across environments
- Environment-specific value overrides
- Automated promotion workflows

### Enterprise Features

- Audit trails for all Helm operations
- Role-based access control integration
- Automated rollback and remediation

### GitOps Integration

- Helm releases as part of GitOps pipelines
- Automated testing and validation
- Compliance and governance controls

## Next Steps

- [Manage Helm Releases Guide](https://fluxcd.io/flux/guides/helmreleases/)
- [Helm Controller Documentation](https://fluxcd.io/flux/components/helm/)
- [Migrate to Helm Controller](https://fluxcd.io/flux/migration/helm/)

Last modified 2024-05-13: upgrade apis for helm GA (b3dba1e)
