# CI Policy Gate

The CI policy gate sits between Git and the hub reconciliation loop. It provides the closest
available equivalent to `terraform plan` in a GitOps workflow. It does not diff current cloud
state, but it blocks the most dangerous classes of change before they can be merged.

Every pull request must pass all CI checks before merge.

---

## What the Gate Does and Does Not Do

**Does:**
- Block deletion of stateful XRDs without explicit human approval (deletion guard)
- Validate manifests against Crossplane XRD schemas and Kubernetes API schemas
- Enforce naming conventions, required labels, and cost guardrails via OPA/Conftest policies
- Run Flux dry-run against the hub API server (read-only) to catch apply failures

**Does not:**
- Diff current cloud state (no equivalent to `terraform plan`)
- Predict runtime cost with precision
- Catch semantic errors inside Crossplane Compositions
- Replace human review for high-risk changes

---

## Deletion Guard

Prevents accidental deletion of stateful cloud resources. The most critical policy in the gate.

### How it works

When a PR removes a stateful XRD claim (XDatabase, XVolume, XQueue, XCluster) or changes
`deletionPolicy` from `Orphan` to `Delete`, CI checks for:

```yaml
annotations:
  platform.example.com/allow-deletion: "true"
  platform.example.com/deletion-approved-by: "platform-team"
```

If absent, CI fails and the PR cannot be merged.

### Conftest policy

```rego
# control-plane/ci/policies/deletion-guard.rego
package main

import future.keywords.if
import future.keywords.in

stateful_kinds := {
  "Database", "XDatabase",
  "Volume",   "XVolume",
  "Queue",    "XQueue",
}

deny[msg] if {
  input.kind in stateful_kinds
  input.spec.deletionPolicy == "Delete"
  not input.metadata.annotations["platform.example.com/allow-deletion"] == "true"
  msg := sprintf(
    "Changing deletionPolicy to Delete on %s/%s requires annotation platform.example.com/allow-deletion: 'true'",
    [input.kind, input.metadata.name],
  )
}
```

### CI script: detect deleted stateful resources

```bash
#!/bin/bash
# control-plane/ci/scripts/check-deletions.sh
set -euo pipefail

STATEFUL_KINDS="Database|XDatabase|Volume|XVolume|Queue|XQueue|XCluster"

DELETED_FILES=$(git diff --name-only --diff-filter=D origin/main...HEAD \
  -- 'infrastructure/tenants/**/*.yaml')

for file in $DELETED_FILES; do
  KIND=$(git show origin/main:$file | grep '^kind:' | awk '{print $2}')
  if echo "$KIND" | grep -qE "^($STATEFUL_KINDS)$"; then
    echo "ERROR: $file contains stateful kind=$KIND deleted without approval"
    echo "  Add: platform.example.com/allow-deletion: 'true'"
    exit 1
  fi
done

CHANGED_FILES=$(git diff --name-only --diff-filter=M origin/main...HEAD \
  -- 'infrastructure/tenants/**/*.yaml')

for file in $CHANGED_FILES; do
  if git diff origin/main...HEAD -- $file | grep -q '+  deletionPolicy: Delete'; then
    conftest test $file --policy control-plane/ci/policies/deletion-guard.rego
  fi
done

echo "Deletion guard passed"
```

---

## Schema Validation

Validates all manifests against current CRD schemas. Catches typos, wrong types, and unknown
fields before they reach the reconciliation loop.

```bash
# control-plane/ci/scripts/validate-schemas.sh
set -euo pipefail

SCHEMA_LOCATION='https://raw.githubusercontent.com/datreeio/CRDs-catalog/main/{{.Group}}/{{.ResourceKind}}_{{.ResourceAPIVersion}}.json'

kubeconform \
  -strict \
  -ignore-missing-schemas \
  -schema-location default \
  -schema-location "$SCHEMA_LOCATION" \
  -summary \
  infrastructure/ control-plane/

echo "Schema validation passed"
```

### Flux dry-run

```bash
# Read-only diff against hub API server; no changes applied
flux diff kustomization flux-system \
  --path ./control-plane/flux \
  --kustomization-file ./control-plane/flux/kustomization.yaml
```

---

## OPA / Conftest Policies

### Naming conventions

```rego
# control-plane/ci/policies/naming.rego
package main

import future.keywords.if

deny[msg] if {
  name := input.metadata.name
  not regex.match(`^[a-z][a-z0-9-]*[a-z0-9]$`, name)
  msg := sprintf("Resource name '%s' must be lowercase kebab-case", [name])
}
```

### Required labels

All infrastructure XRD claims must carry labels for cost allocation and ownership:

```rego
# control-plane/ci/policies/required-labels.rego
package main

import future.keywords.if
import future.keywords.in

infra_kinds := {"Database","XDatabase","Volume","XVolume","Queue","XQueue","XCluster","XNetwork"}

required := {"team", "env", "cost-center"}

deny[msg] if {
  input.kind in infra_kinds
  label := required[_]
  not input.metadata.labels[label]
  msg := sprintf("Resource %s/%s is missing required label: %s", [input.kind, input.metadata.name, label])
}
```

### Cost guardrail

```rego
# control-plane/ci/policies/cost-guardrail.rego
package main

import future.keywords.if
import future.keywords.in

# Flag large instance sizes for platform team review
large_sizes := {"xlarge", "2xlarge", "4xlarge", "8xlarge", "r6g.4xlarge", "Standard_E32s_v3"}

warn[msg] if {
  input.kind in {"Database","XDatabase"}
  input.spec.size in large_sizes
  msg := sprintf(
    "Resource %s/%s uses size '%s' — platform team review required (add platform.example.com/cost-approved: 'true' to suppress)",
    [input.kind, input.metadata.name, input.spec.size],
  )
}
```

Warnings do not fail CI. They emit a visible notice in the PR check output and require
`platform.example.com/cost-approved: "true"` on the resource to suppress.

---

## Running the Gate Locally

Before opening a PR, run the full gate locally:

```bash
# Install tools
brew install kubeconform conftest

# Run all checks
./control-plane/ci/scripts/check-deletions.sh
./control-plane/ci/scripts/validate-schemas.sh
conftest test infrastructure/ --policy control-plane/ci/policies/

echo "All local checks passed"
```

---

## GitHub Actions Workflow

```yaml
# .github/workflows/ci-policy-gate.yaml
name: CI Policy Gate

on:
  pull_request:
    paths:
      - 'infrastructure/**'
      - 'control-plane/**'

jobs:
  deletion-guard:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Deletion guard
        run: ./control-plane/ci/scripts/check-deletions.sh

  schema-validation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install kubeconform
        run: |
          curl -sL https://github.com/yannh/kubeconform/releases/latest/download/kubeconform-linux-amd64.tar.gz \
            | tar xz && sudo mv kubeconform /usr/local/bin/
      - name: Validate schemas
        run: ./control-plane/ci/scripts/validate-schemas.sh

  opa-policies:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install conftest
        run: |
          curl -sL https://github.com/open-policy-agent/conftest/releases/latest/download/conftest_Linux_x86_64.tar.gz \
            | tar xz && sudo mv conftest /usr/local/bin/
      - name: OPA policy checks
        run: conftest test infrastructure/ --policy control-plane/ci/policies/

  flux-dry-run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install flux
        uses: fluxcd/flux2/action@main
      - name: Flux diff
        env:
          KUBECONFIG: ${{ secrets.HUB_KUBECONFIG }}
        run: |
          flux diff kustomization flux-system \
            --path ./control-plane/flux \
            --kustomization-file ./control-plane/flux/kustomization.yaml
```

---

## Adding a New Policy

1. Write the Rego policy in `control-plane/ci/policies/`
2. Add a `test_` file alongside it: `control-plane/ci/policies/my-policy_test.rego`
3. Test locally: `conftest verify --policy control-plane/ci/policies/my-policy.rego`
4. Add to the GitHub Actions `opa-policies` job (no change needed if it is in the policies directory)
5. Document the policy in this file under the appropriate section

All policies are automatically picked up by `conftest test ... --policy control-plane/ci/policies/`.
