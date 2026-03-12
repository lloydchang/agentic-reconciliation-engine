# AGPL-3.0 Licensing Guide for Building Proprietary Layers

This guide explains how to legally build proprietary software layers on top of the AGPL-3.0 licensed Continuous Reconciliation Engine (CRE).

## Dual Licensing Structure

This repository uses a **dual licensing approach** to support both open-source development and commercial usage:

### AGPL-3.0 Core Components
- **What**: The Continuous Reconciliation Engine (CRE) core
- **Files**: All infrastructure manifests, Flux configurations, scripts, and core logic
- **License**: GNU Affero General Public License v3.0 (AGPL-3.0)
- **Requirements**: Derivative works must be AGPL-licensed

### Apache 2.0 Documentation & Examples
- **What**: Integration examples, tutorials, and documentation
- **Files**: All `.md` documentation files, code examples, and sample implementations
- **License**: Apache License 2.0 (permissive)
- **Requirements**: Commercial use allowed, no copyleft restrictions

### Why This Works
- **Clean Separation**: Documentation/examples don't modify or link to AGPL core
- **Network Communication**: Examples demonstrate safe integration via APIs/network
- **Educational Purpose**: Examples show integration patterns, not core modifications
- **Commercial Enablement**: Allows users to build proprietary software using examples

## AGPL-3.0 Key Concepts

**AGPL-3.0** is a copyleft license that requires derivative works to be licensed under the same terms. However, it contains provisions that allow building proprietary software on top.

### Section 13: Remote Network Interaction

"The Corresponding Source also includes any remote interactive user interfaces that the Program implements or uses, but only to the extent that the interface's functionality is limited to what is necessary for the interface to communicate with the Program."

**Translation**: If your proprietary software communicates with the CRE via network protocols (APIs, webhooks, GitOps), it does NOT need to be AGPL-licensed.

### Network Communication is Allowed

- ✅ REST APIs
- ✅ Webhooks
- ✅ GitOps (Git commits)
- ✅ Message queues
- ✅ Database interactions (if the AGPL code doesn't link to your code)

## Safe Integration Patterns

### Pattern 1: API Communication Only
```
Your Proprietary Code ←→ REST API ←→ CRE (AGPL)
```
**Safe**: No code linking, communication via network only.

### Pattern 2: GitOps Integration
```
Your UI → Git Commit → Flux → CRE (AGPL)
```
**Safe**: Infrastructure changes via Git, no direct code integration.

### Pattern 3: Webhook Callbacks
```
CRE (AGPL) → Webhook → Your Proprietary Service
```
**Safe**: Event-driven communication.

## Dangerous Patterns (AVOID)

### ❌ Direct Code Linking
```
Your Code (Proprietary) → Imports/Links → CRE (AGPL)
```
**Illegal**: Creates a derivative work requiring AGPL license.

### ❌ Plugin Architecture
```
CRE (AGPL) ←→ Plugin Interface ←→ Your Code (Proprietary)
```
**Risky**: May be considered derivative if tightly coupled.

## Real-World Examples

### GitLab (Proprietary) + GitLab CE (MIT)
- Proprietary features built on open-source core
- Clear API boundaries
- Different licensing for different components

### MongoDB (Proprietary) + MongoDB Community (SSPL)
- Commercial offerings on open-source database
- Network communication only

## Implementation Guidelines

### 1. Maintain Clear Boundaries
- Deploy CRE as separate service/container
- Use APIs, not shared libraries
- Document architectural separation

### 2. License Your Proprietary Code
- Use proprietary license (e.g., commercial, MIT for open-source parts)
- Clearly mark proprietary components
- Include licensing headers

### 3. Deployment Separation
- CRE runs in its own Kubernetes namespace/cluster
- Your proprietary code runs separately
- Network communication via load balancers/APIs

### 4. Audit Your Architecture
- Consult legal counsel for AGPL compliance
- Document integration points
- Maintain separation of concerns

## Compliance Checklist

- [ ] No direct code imports of AGPL components
- [ ] All communication via network protocols
- [ ] Clear architectural documentation
- [ ] Separate deployment units
- [ ] Legal review completed
- [ ] License headers on proprietary code

## Additional Resources

- [AGPL-3.0 Full Text](https://www.gnu.org/licenses/agpl-3.0.en.html)
- [GNU AGPL FAQ](https://www.gnu.org/licenses/gpl-faq.en.html)
- [Software Freedom Conservancy AGPL Guide](https://sfconservancy.org/copyleft-compliance/agpl-compliance-case-studies.html)
