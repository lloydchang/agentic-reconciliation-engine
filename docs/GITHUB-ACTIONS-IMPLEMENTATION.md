# GitHub Actions Auto Pull Request Implementation

This repository now implements the Flux CD GitHub Actions Auto PR workflow for automated image updates with pull request approval.

## Overview

The implementation provides:

1. **Automated Image Updates**: Flux detects new container images and updates manifests
2. **Staging Branch**: Changes are pushed to a `staging` branch instead of directly to `main`
3. **Auto PR Creation**: GitHub Actions automatically creates a pull request when staging branch is created
4. **Review Process**: Changes require manual approval before merging to production

## Components

### 1. GitHub Actions Workflow

**File**: `.github/workflows/staging-auto-pr.yml`

- Triggers on branch creation
- Creates PR when `staging` branch is detected
- Includes comprehensive PR template with review guidelines
- Adds appropriate labels and assigns to the triggering user

### 2. Flux ImageUpdateAutomation

**File**: `core/operators/flux/image-update-automation.yaml`

```yaml
apiVersion: image.toolkit.fluxcd.io/v1beta2
kind: ImageUpdateAutomation
metadata:
  name: $TOPDIR-updates
  namespace: flux-system
spec:
  interval: 5m
  git:
    checkout:
      ref:
        branch: main
    push:
      branch: staging  # Push to staging for PR review
  update:
    path: ./core/resources/tenants/3-workloads
    strategy: Setters
```

### 3. Image Repository & Policy

**File**: `core/operators/flux/image-policy.yaml`

- Monitors container registry for new images
- Defines update policies and filtering
- Works with ImageUpdateAutomation to trigger updates

## Workflow Process

1. **Image Detection**: Flux monitors container registry for new image versions
2. **Manifest Update**: When new image is found, Flux updates workload manifests
3. **Staging Push**: Changes are committed and pushed to `staging` branch
4. **PR Creation**: GitHub Actions detects staging branch and creates PR
5. **Review & Merge**: Team reviews changes and merges to main when approved
6. **Auto Cleanup**: Branch is automatically deleted after merge

## Configuration

### Repository Settings

Enable these settings in your GitHub repository:

- **Automatically delete head branches**: Settings → General → Pull Requests
- **Branch protection rules**: Require PR review for main branch
- **Required status checks**: Ensure CI/CD passes before merge

### Customization Options

#### PR Labels and Assignees

Edit `.github/workflows/staging-auto-pr.yml`:

```yaml
--label=automated,image-update,staging \
--assignee=${{ github.actor }} \
```

#### PR Title and Body

Customize the PR template in the workflow:

```yaml
--title="🚀 Automated Updates from ${GITHUB_REF}" \
--body="Custom PR description..."
```

#### Branch Names

Change branch names in both files:

1. **ImageUpdateAutomation**: `push.branch: staging`
2. **GitHub Actions**: `if: github.event.ref == 'staging'`

## Security Considerations

### Permissions

The workflow uses minimal required permissions:

```yaml
permissions:
  pull-requests: write
  contents: read
```

### Access Control

- PR requires manual review before merge
- Changes are tracked in git history
- Automated commits use dedicated bot identity

## Troubleshooting

### Common Issues

1. **PR Not Created**
   - Check workflow permissions
   - Verify staging branch creation
   - Review GitHub Actions logs

2. **Duplicate PRs**
   - Workflow checks for existing PRs
   - Manual cleanup may be needed

3. **Merge Conflicts**
   - Rebase staging branch on main
   - Resolve conflicts and push updates

### Debug Commands

```bash
# Check workflow status
gh run list --repo=your-repo

# Manually trigger workflow
gh workflow run staging-auto-pr.yml --repo=your-repo

# Check existing PRs
gh pr list --head staging --base main
```

## Best Practices

1. **Regular Updates**: Keep Flux and GitHub Actions updated
2. **Monitoring**: Monitor workflow success/failure rates
3. **Documentation**: Document team-specific review processes
4. **Testing**: Test workflow in non-production environment first

## Integration with Existing CI/CD

This auto PR workflow integrates seamlessly with:

- **Docker Build Pipeline**: Triggers on new image builds
- **Flux Sync**: Continues to sync manifests to clusters
- **Existing Workflows**: No conflicts with other GitHub Actions

## Example PR Template

The generated PRs include:

- **Changes List**: Automated summary of image updates
- **Review Guidelines**: Instructions for reviewers
- **Merge Process**: Step-by-step approval workflow
- **Timestamp**: Automatic creation time

## Next Steps

1. **Test Workflow**: Push a test change to verify the complete flow
2. **Configure Reviewers**: Set up default PR reviewers
3. **Monitor Results**: Watch first few automated PRs
4. **Adjust Settings**: Fine-tune based on team feedback

---

This implementation provides a robust, secure, and auditable workflow for automated infrastructure updates while maintaining human oversight and control.
