# Karmada + Flux

## Disclaimer

Note that this guide is not for doing GitOps, but for managing Helm releases for applications among multiple clusters.

Also note that this guide needs review in consideration of Flux v2.0.0, and likely needs to be refreshed.

Expect this doc to either be archived soon, or to receive some overhaul.

## Background

Karmada is a Kubernetes management system that enables you to run your cloud-native applications across multiple Kubernetes clusters and clouds, with no changes to your applications. By speaking Kubernetes-native APIs and providing advanced scheduling capabilities, Karmada enables truly open, multi-cloud Kubernetes. With Karmada's centralized multi-cloud management, users can easily distribute and manage Helm releases in multiple clusters based on powerful Flux APIs.

## Karmada Setup

Steps described in this document have been tested on Karmada 1.0, 1.1 and 1.2. To start up Karmada, you can refer to [here](https://karmada.io/docs/installation/). If you just want to try Karmada, we recommend building a development environment by `hack/local-up-karmada.sh`.

```bash
git clone https://github.com/karmada-io/karmada
cd karmada
hack/local-up-karmada.sh
```

After that, you will start a Kubernetes cluster by kind to run the Karmada control plane and create member clusters managed by Karmada.

```bash
kubectl get clusters --kubeconfig ~/.kube/karmada.config
```

You can use the command above to check registered clusters, and you will get similar output as follows:

```
NAME      VERSION   MODE   READY   AGE
member1   v1.23.4   Push   True    7m38s
member2   v1.23.4   Push   True    7m35s
member3   v1.23.4   Pull   True    7m27s
```

## Flux Installation

In Karmada control plane, you need to install Flux crds but do not need controllers to reconcile them. They are treated as resource templates, not specific resource instances. Based on work API here, they will be encapsulated as a work object delivered to member clusters and reconciled by Flux controllers in member clusters finally.

```bash
kubectl apply -k github.com/fluxcd/flux2/manifests/crds?ref=main --kubeconfig ~/.kube/karmada.config
```

For testing purposes, we'll install Flux on member clusters without storing its manifests in a Git repository:

```bash
flux install --kubeconfig ~/.kube/members.config --context member1
flux install --kubeconfig ~/.kube/members.config --context member2
```

Please refer to the documentations [here](https://fluxcd.io/flux/installation/) for more ways to set up Flux in details.

**Tip**: If you want to manage Helm releases across your fleet of clusters, Flux must be installed on each cluster.

## Helm release propagation

If you want to propagate Helm releases for your apps to member clusters, you can refer to the guide below.

### Define Flux Resources

Define a Flux HelmRepository and a HelmRelease manifest in Karmada Control plane. They will serve as resource templates.

```yaml
apiVersion: source.toolkit.fluxcd.io/v1beta2
kind: HelmRepository
metadata:
  name: podinfo
spec:
  interval: 1m
  url: https://stefanprodan.github.io/podinfo
---
apiVersion: helm.toolkit.fluxcd.io/v2beta1
kind: HelmRelease
metadata:
  name: podinfo
spec:
  interval: 5m
  chart:
    spec:
      chart: podinfo
      version: 5.0.3
      sourceRef:
        kind: HelmRepository
        name: podinfo
```

### Define Propagation Policies

Define a Karmada PropagationPolicy that will propagate them to member clusters:

```yaml
apiVersion: policy.karmada.io/v1alpha1
kind: PropagationPolicy
metadata:
  name: helm-repo
spec:
  resourceSelectors:
    - apiVersion: source.toolkit.fluxcd.io/v1beta2
      kind: HelmRepository
      name: podinfo
  placement:
    clusterAffinity:
      clusterNames:
        - member1
        - member2
---
apiVersion: policy.karmada.io/v1alpha1
kind: PropagationPolicy
metadata:
  name: helm-release
spec:
  resourceSelectors:
    - apiVersion: helm.toolkit.fluxcd.io/v2beta1
      kind: HelmRelease
      name: podinfo
  placement:
    clusterAffinity:
      clusterNames:
        - member1
        - member2
```

The above configuration is for propagating the Flux objects to member1 and member2 clusters.

### Apply Manifests

Apply those manifests to the Karmada-apiserver:

```bash
kubectl apply -f ../helm/ --kubeconfig ~/.kube/karmada.config
```

The output is similar to:

```
helmrelease.helm.toolkit.fluxcd.io/podinfo created
helmrepository.source.toolkit.fluxcd.io/podinfo created
propagationpolicy.policy.karmada.io/helm-release created
propagationpolicy.policy.karmada.io/helm-repo created
```

### Verify Deployment

Switch to the distributed cluster and verify:

```bash
helm --kubeconfig ~/.kube/members.config --kube-context member1 list
```

The output is similar to:

```
NAME   	NAMESPACE	REVISION	UPDATED                               	STATUS  	CHART        	APP VERSION
podinfo	default  	1       	2022-05-27 01:44:35.24229175 +0000 UTC	deployed	podinfo-5.0.3	5.0.3
```

Based on Karmada's propagation policy, you can schedule Helm releases to your desired cluster flexibly, just like Kubernetes scheduling Pods to the desired node.

## Customize the Helm release for specific clusters

The example above shows how to distribute the same Helm release to multiple clusters in Karmada. Besides, you can use Karmada's OverridePolicy to customize applications for specific clusters. For example, if you just want to change replicas in member1, you can refer to the overridePolicy below.

### Define Override Policy

Define a Karmada OverridePolicy:

```yaml
apiVersion: policy.karmada.io/v1alpha1
kind: OverridePolicy
metadata:
  name: example-override
  namespace: default
spec:
  resourceSelectors:
  - apiVersion: helm.toolkit.fluxcd.io/v2beta1
    kind: HelmRelease
    name: podinfo
  overrideRules:
  - targetCluster:
      clusterNames:
        - member1
    overriders:
      plaintext:
        - path: "/spec/values"
          operator: add
          value:
            replicaCount: 2
```

### Apply Override Policy

Apply the manifests to the Karmada-apiserver:

```bash
kubectl apply -f example-override.yaml --kubeconfig ~/.kube/karmada.config
```

The output is similar to:

```
overridepolicy.policy.karmada.io/example-override configured
```

After applying the above policy in Karmada control plane, you will find that replicas in member1 has changed to 2, but those in member2 keep the same.

```bash
kubectl --kubeconfig ~/.kube/members.config --context member1 get po
```

The output is similar to:

```
NAME                       READY   STATUS    RESTARTS   AGE
podinfo-68979685bc-6wz6s   1/1     Running   0          6m28s
podinfo-68979685bc-dz9f6   1/1     Running   0          7m42s
```

## Repository Integration

This Karmada + Flux integration is designed to work seamlessly with the GitOps Infra Control Plane. The combination enables:

1. **Multi-Cluster Management**: Centralized control of Flux resources across multiple Kubernetes clusters
2. **GitOps at Scale**: GitOps principles applied to multi-cluster deployments
3. **Flexible Scheduling**: Karmada's advanced scheduling capabilities for Flux Helm releases
4. **Cluster-Specific Customization**: Override policies for cluster-specific configurations

### Integration with GitOps Control Plane

```yaml
# Example: Multi-cluster Flux + Karmada setup
apiVersion: source.toolkit.fluxcd.io/v1beta2
kind: HelmRepository
metadata:
  name: podinfo
  namespace: flux-system
spec:
  interval: 1m
  url: https://stefanprodan.github.io/podinfo
---
apiVersion: helm.toolkit.fluxcd.io/v2beta1
kind: HelmRelease
metadata:
  name: podinfo
  namespace: flux-system
spec:
  interval: 5m
  chart:
    spec:
      chart: podinfo
      version: 5.0.3
      sourceRef:
        kind: HelmRepository
        name: podinfo
---
# Karmada PropagationPolicy for multi-cluster deployment
apiVersion: policy.karmada.io/v1alpha1
kind: PropagationPolicy
metadata:
  name: podinfo-multi-cluster
spec:
  resourceSelectors:
    - apiVersion: source.toolkit.fluxcd.io/v1beta2
      kind: HelmRepository
      name: podinfo
    - apiVersion: helm.toolkit.fluxcd.io/v2beta1
      kind: HelmRelease
      name: podinfo
  placement:
    clusterAffinity:
      clusterNames:
        - member1
        - member2
        - member3
```

## Benefits

- **Centralized Management**: Manage Flux resources across multiple clusters from a single control plane
- **GitOps at Scale**: Apply GitOps principles to multi-cluster deployments
- **Flexible Scheduling**: Use Karmada's advanced scheduling for workload placement
- **Cluster Customization**: Override configurations per cluster using Karmada policies
- **Kubernetes Native**: Works with existing Kubernetes and Flux APIs

Last modified 2024-05-13: upgrade apis for helm GA (b3dba1e)
