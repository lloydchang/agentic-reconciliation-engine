# GitHub Actions Auto Pull Request

## Overview

This guide shows how to configure GitHub Actions to open a pull request whenever a selected branch is pushed.

From the Image Update Guide we saw that Flux can set `.spec.git.push.branch` to push updates to a different branch than the one used for checkout.

## Configure ImageUpdateAutomation

Configure an ImageUpdateAutomation resource to push to a target branch, where we can imagine some policy dictates that updates must be staged and approved for production before they can be deployed.

```yaml
apiVersion: image.toolkit.fluxcd.io/v1beta2
kind: ImageUpdateAutomation
metadata:
  name: flux-system
spec:
  git:
    checkout:
      ref:
        branch: main
    push:
      branch: staging
```

We can show that the automation generates a change in the staging branch which, once the change is approved and merged, gets deployed into production. The image automation is meant to be gated behind a pull request approval workflow, according to policy you may have in place for your repository.

## Auto Pull Request Workflow

To create the pull request whenever automation creates a new branch, in your manifest repository, add a GitHub Action workflow as below. This workflow watches for the creation of the staging branch and opens a pull request with any desired labels, title text, or pull request body content that you configure.

```yaml
# ./.github/workflows/staging-auto-pr.yaml
name: Staging Auto-PR
on:
  create:

jobs:
  pull-request:
    runs-on: ubuntu-latest
    if: |
      github.event.ref_type == 'branch' &&
      github.event.ref == 'staging'
    permissions:
      pull-requests: write
    steps:
    - name: Checkout
      uses: actions/checkout@v4
      with:
        fetch-depth: 0
    - name: Create Pull Request
      env:
        GH_TOKEN: ${{ secrets.GITHUB_TOKEN }} # used implicitly by the gh CLI to authenticate with GitHub
        GITHUB_REPO: ${{ github.repository }}
        GITHUB_REF: ${{ github.ref }}
      run: |
        gh pr create \
          --repo=${GITHUB_REPO} \
          --head=staging \
          --base=main \
          --title="Pulling ${GITHUB_REF} into main" \
          --body=":crown: *An automated PR*" \
          --reviewer=kingdonb \
          --draft
```

In the example above, `--head` is the source branch and `--base` is the destination branch.

You can use the workflow above to automatically open a pull request against a destination branch. When staging is merged into the main branch, changes are deployed in production. Be sure to delete the branch after merging so that the workflow runs the next time that the image automation finds something to change, for that you can go to your repository settings and enable the **Automatically delete head branches** option.

## Additional Options

The `gh pr create` CLI command used in the workflow above has more useful options, like `--fill-first`, `--label` and `--assignee`, that setting will help make this workflow more usable. You can assign reviewers, labels, (use markdown emojis in the `--body`, make variable substitutions in the title, etc.)

This way you can automatically push changes to a staging branch and require review with manual approval of any automatic image updates, before they are applied on your production clusters.

## Repository Integration

This auto PR workflow is designed to work seamlessly with the GitOps Infra Control Plane. The platform includes comprehensive image update automation and policy-based deployment controls.

### Integration with GitOps Control Plane

```yaml
# Example: Image update automation with PR gating
apiVersion: image.toolkit.fluxcd.io/v1beta2
kind: ImageUpdateAutomation
metadata:
  name: app-updates
  namespace: flux-system
spec:
  interval: 5m
  sourceRef:
    kind: GitRepository
    name: flux-system
  git:
    checkout:
      ref:
        branch: main
    push:
      branch: staging  # Push to staging branch for PR review
  update:
    path: ./clusters/production
    strategy: Setters
---
# GitHub Actions workflow for auto PR creation
name: Staging Auto-PR
on:
  create:
jobs:
  pull-request:
    runs-on: ubuntu-latest
    if: github.event.ref == 'staging'
    permissions:
      pull-requests: write
    steps:
    - name: Create Pull Request
      run: |
        gh pr create \
          --head=staging \
          --base=main \
          --title="🚀 Automated Image Updates" \
          --body="🤖 *Automated PR for image updates*" \
          --label=automated,image-update \
          --assignee=@me
```

## Benefits

### Policy Compliance

- Enforce review processes for automated changes
- Maintain audit trails for all deployments
- Support compliance requirements for production changes

### Risk Mitigation

- Prevent accidental deployments to production
- Allow manual validation of automated changes
- Enable rollback capabilities through PR reverts

### Collaboration

- Team visibility into automated changes
- Opportunity for peer review of updates
- Documentation of change rationale

## Experiment with Strategies

Experiment with these strategies to find the right automated workflow solution for your team! Different organizations may require different levels of automation vs. manual control based on their risk tolerance and compliance requirements.

Last modified 2025-06-04: Fix GitHub Action syntax error and filter with if statement (0046244)
