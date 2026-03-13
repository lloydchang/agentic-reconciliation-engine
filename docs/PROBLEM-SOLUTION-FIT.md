# Problem-Solution Fit Assessment

## Purpose

This framework helps you determine whether the GitOps Infra Control Plane is the right solution
for your specific problem. The architecture exists to solve a specific class of problem — not every
infrastructure problem. Starting here prevents adopting a complex system for a problem that a
simpler tool solves better.

---

## Step 1: Define Your Problem

Before evaluating any solution, answer these questions honestly:

**Infrastructure complexity**
- How many cloud providers are you running in production today?
- How frequently does infrastructure drift cause production incidents or audit findings?
- How much engineering time is spent on manual drift remediation each week?
- How many Kubernetes clusters are you managing or planning to manage?

**Team and operational context**
- Does your team have existing Kubernetes operational depth — can they read controller logs,
  debug CRD status conditions, and diagnose a stuck reconcile loop?
- Is the hub cluster going to run on a managed Kubernetes control plane (EKS, AKS, GKE)?
- What is the realistic time available for the upfront adoption phase?

**Scale and cost**
- Is infrastructure drift already a recurring production cost, or is it a hypothetical concern?
- What is the cost of the hub cluster infrastructure plus per-spoke cloud vault instances?
- Does that cost justify the drift reduction benefit at your current scale?

---

## Step 2: Understand the Cost Model

This architecture reduces ongoing toil by replacing human drift remediation with controllers that
run 24/7. In steady state, Flux, Crossplane, and CAPI reconcile continuously with no human
involvement beyond incident response and planned upgrades — the same as any managed service.

**The cost is front-loaded, not ongoing:**

The upfront adoption phase — standing up the hub, authoring Crossplane Compositions for your
resource types, configuring CAPI providers, wiring per-spoke ESO workload identity, and building
the CI gate — requires focused engineering time. This is a one-time investment, not a permanent
staffing requirement.

The right question is: does the upfront adoption cost pay off against the ongoing cost of the
problem you are solving?

---

## Fit Scenarios

### Strong fit

**Multi-cloud with recurring drift incidents**

You are running workloads across 2+ cloud providers. Configuration drift (manual console changes,
out-of-band modifications, failed applies) is causing production incidents, failed compliance
audits, or regular manual remediation work. The ongoing cost of that toil justifies the upfront
adoption investment.

Assessment: **Strong fit** — this is the core use case the architecture was designed for.

---

**Brownfield consolidation from multiple IaC tools**

You are operating multiple Terraform workspaces, CDK stacks, CloudFormation stacks, and ARM
templates across teams, with no single source of truth. Coordinating changes is expensive.
You want a single declarative model with continuous enforcement.

Assessment: **Strong fit** — gradual migration mode lets you coexist with existing tools while
building confidence in the new system. See [Legacy IaC Migration Strategy](./LEGACY-IAC-MIGRATION-STRATEGY.md).

---

**Single-cloud with GitOps already established, expanding to multi-cloud**

You already use Flux or Argo CD for application delivery. You are adding a second cloud provider.
You want to extend the same GitOps model to infrastructure, not introduce a parallel tool.

Assessment: **Good fit** — disable providers for unused clouds; enable them as you expand.

---

**Local development + cloud production parity**

Development teams need local environments (Kind, k3s, LocalStack) that mirror cloud production
closely. You want the same declarative model and tooling from laptop to production.

Assessment: **Good fit** — Crossplane providers work against LocalStack and real cloud APIs
with the same manifest structure.

---

### Weak fit

**Single-cloud or single-region deployment**

GKE Enterprise, Azure Arc, and EKS Anywhere provide most of the continuous reconciliation and
GitOps capabilities of this architecture as a managed service, at lower adoption cost. If you
are single-cloud, evaluate these first.

Assessment: **Weak fit** — managed alternatives cover this at lower adoption cost.

---

**No existing Kubernetes operational depth**

The failure modes of this architecture — stuck Crossplane managed resources, failed CAPI
provisioning, Flux reconcile errors, ESO workload identity misconfiguration — are opaque without
the ability to read controller logs and CRD status conditions. If your team cannot currently
diagnose a Kubernetes controller issue, the adoption phase will take significantly longer than
estimated and incidents will be harder to resolve.

Assessment: **Weak fit until operational depth is established** — build Kubernetes operational
skills on simpler workloads first.

---

**Emergency migration without runway**

This architecture is a target state, not a migration tool. The upfront adoption phase requires
time to do correctly. Adopting under deadline pressure produces a partially-implemented system
that carries all the operational complexity with none of the drift correction benefits.

Assessment: **Weak fit** — use traditional IaC tools for the migration; adopt this as a target
state afterward.

---

**Infrastructure complexity doesn't yet exist at scale**

If configuration drift is not currently causing production incidents or audit findings, the
upfront adoption cost is hard to justify. The architecture is most valuable when it is replacing
a real ongoing operational cost, not preventing a hypothetical future one.

Assessment: **Moderate fit** — consider adopting Flux for application delivery first; revisit
this architecture when infrastructure drift becomes a real operational cost.

---

## Modular Adoption

You do not need to adopt all components at once. The architecture is modular:

| Component | Adopt when |
|---|---|
| Flux (hub) | Starting point — GitOps reconciliation for hub resources |
| Crossplane | First cloud resource needs continuous reconciliation |
| CAPI | Spoke cluster lifecycle needs to be managed declaratively |
| ESO per spoke | Spoke secret delivery needs to be independent of hub |
| Bootstrap cluster | Hub is running production workloads and needs a recovery anchor |
| CI gate | Before any production resources are managed by the system |

Start with Flux and the CI gate. Add Crossplane when the first Composition is ready. Add CAPI
when spoke lifecycle management is needed. Add ESO per spoke as spokes are provisioned.

---

## Decision Framework

```
Does infrastructure drift cause recurring production incidents or audit failures today?
│
├─ No → Is single-cloud? → Yes → Evaluate GKE Enterprise / Azure Arc / EKS Anywhere first
│                        → No  → Moderate fit; adopt Flux for apps first, revisit later
│
└─ Yes → Do you have Kubernetes operational depth?
         │
         ├─ No  → Build Kubernetes skills on simpler workloads first; weak fit now
         │
         └─ Yes → Is the hub on a managed control plane (EKS/AKS/GKE)?
                  │
                  ├─ No  → On-prem hub adds operational burden; evaluate carefully
                  │
                  └─ Yes → Does the upfront adoption cost justify the ongoing drift remediation savings?
                           │
                           ├─ Yes → Strong fit; proceed to implementation plan
                           └─ No  → Wait until scale justifies the investment
```

---

## Conclusion

The GitOps Infra Control Plane is the right choice when infrastructure drift is already a real
operational cost, when you have existing Kubernetes depth to absorb the upfront adoption phase,
and when the hub can run on a managed control plane. It is not the right choice for simple
deployments, teams without Kubernetes depth, or situations where a managed alternative covers
the problem at lower cost.

The best outcome is a system that runs itself in steady state, reducing the ongoing human cost
of infrastructure operations. That only happens if the upfront adoption is done correctly.

---

**Last updated**: see Git history  
**See also**: [Architecture](./ARCHITECTURE.md) · [Implementation Plan](./implementation_plan.md) · [Legacy IaC Migration Strategy](./LEGACY-IAC-MIGRATION-STRATEGY.md)
