#!/usr/bin/env python3
"""
Phase 1: Foundation & Provider Validation - Automation Script

Automates the installation and validation of Crossplane providers and initial setup.
This script implements the Phase 1 implementation plan from docs/migration/PHASE1-IMPLEMENTATION-PLAN.md.

Usage:
    python3 phase1_crossplane_setup.py [--dry-run] [--skip-providers] [--skip-gitops] [--test-resource]

Options:
    --dry-run        Show what would be executed without making changes
    --skip-providers Skip provider installation (assume already installed)
    --skip-gitops    Skip GitOps/Flux setup
    --test-resource  Create test managed resource (S3 bucket or equivalent)
    --help           Show this help message
"""

import argparse
import subprocess
import sys
import time
from typing import Tuple, List, Dict, Optional

def run_command(cmd: List[str], dry_run: bool = False, timeout: int = 300) -> Tuple[int, str, str]:
    """Execute a shell command and return exit code, stdout, stderr."""
    if dry_run:
        print(f"[DRY RUN] Would execute: {' '.join(cmd)}")
        return 0, "", ""

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"Command timed out after {timeout}s"
    except Exception as e:
        return -1, "", f"Error executing command: {str(e)}"


def check_prerequisites() -> bool:
    """Check if kubectl is available and cluster is accessible."""
    print("🔍 Checking prerequisites...")

    # Check kubectl
    code, stdout, stderr = run_command(["kubectl", "version", "--client"])
    if code != 0:
        print("❌ kubectl not found or not configured")
        print(f"   Error: {stderr}")
        return False
    print("✅ kubectl available")

    # Check cluster connectivity
    code, stdout, stderr = run_command(["kubectl", "cluster-info"])
    if code != 0:
        print("❌ Cannot connect to Kubernetes cluster")
        print(f"   Error: {stderr}")
        return False
    print("✅ Cluster accessible")

    # Check Crossplane installation
    code, stdout, stderr = run_command([
        "kubectl", "get", "deployment", "crossplane", "-n", "crossplane-system"
    ])
    if code != 0:
        print("⚠️  Crossplane not detected. Will attempt to install.")
        return True
    print("✅ Crossplane already installed")
    return True


def install_providers(dry_run: bool = False) -> bool:
    """Install Crossplane providers from repository definitions."""
    print("\n📦 Installing Crossplane providers...")

    provider_dir = "core/operators/control-plane/crossplane/providers"

    # Apply provider definitions
    code, stdout, stderr = run_command(
        ["kubectl", "apply", "-k", provider_dir],
        dry_run=dry_run
    )
    if code != 0 and not dry_run:
        print(f"❌ Failed to install providers: {stderr}")
        return False
    print("✅ Providers applied")

    # Wait for providers to become healthy
    print("⏳ Waiting for providers to become HEALTHY (timeout: 300s)...")
    code, stdout, stderr = run_command([
        "kubectl", "wait", "--for=condition=Healthy", "providers",
        "-n", "crossplane-system", "--all", "--timeout=300s"
    ], dry_run=dry_run, timeout=310)

    if code != 0 and not dry_run:
        print(f"⚠️  Some providers may not be healthy yet: {stderr}")
        # Don't fail, just warn
    else:
        print("✅ All providers HEALTHY")

    return True


def verify_providers() -> bool:
    """Verify provider installation and health status."""
    print("\n🔍 Verifying provider installation...")

    all_healthy = True

    # Check providers
    print("\nProvider status:")
    code, stdout, stderr = run_command([
        "kubectl", "get", "providers", "-n", "crossplane-system", "-o", "wide"
    ])
    if code == 0:
        print(stdout)
        # Check if all are Healthy
        if "False" in stdout or "Unknown" in stdout:
            all_healthy = False
            print("⚠️  Some providers are not Healthy")
    else:
        print(f"❌ Error getting providers: {stderr}")
        all_healthy = False

    # Check ProviderConfigs
    print("\nProviderConfig status:")
    code, stdout, stderr = run_command([
        "kubectl", "get", "providerconfigs", "-n", "crossplane-system"
    ])
    if code == 0:
        print(stdout)
    else:
        print(f"❌ Error getting ProviderConfigs: {stderr}")
        all_healthy = False

    # Check CRDs
    print("\nProvider-specific CRDs:")
    code, stdout, stderr = run_command([
        "kubectl", "get", "crd"
    ])
    if code == 0:
        crds = [line.split()[0] for line in stdout.strip().split('\n')[1:]]
        expected_prefixes = ['rds.aws', 'eks.aws', 'container.gcp', 'azure']
        for prefix in expected_prefixes:
            matching = [crd for crd in crds if prefix in crd]
            if matching:
                print(f"  ✅ {prefix}: {len(matching)} CRDs")
            else:
                print(f"  ❌ {prefix}: No CRDs found")
                all_healthy = False
    else:
        print(f"❌ Error getting CRDs: {stderr}")
        all_healthy = False

    return all_healthy


def create_test_resource(dry_run: bool = False) -> bool:
    """Create a test managed resource (AWS S3 bucket)."""
    print("\n🔨 Creating test managed resource (AWS S3 bucket)...")
    print("   Note: This requires valid AWS credentials in ProviderConfig")

    bucket_name = f"crossplane-test-bucket-{int(time.time())}"

    manifest = f"""apiVersion: s3.aws.crossplane.io/v1beta1
kind: Bucket
metadata:
  name: {bucket_name}
  namespace: crossplane-system
spec:
  forProvider:
    locationConstraint: us-west-2
  providerConfigRef:
    name: aws-provider
"""

    code, stdout, stderr = run_command(
        ["kubectl", "apply", "-f", "-"],
        dry_run=dry_run,
        timeout=10
    )

    if code == 0 or dry_run:
        print(f"✅ Test bucket manifest submitted: {bucket_name}")
        print("   Monitor with: kubectl get buckets -n crossplane-system -w")
        print("   Expected status: Ready=True within a few minutes")
        return True
    else:
        print(f"❌ Failed to create test bucket: {stderr}")
        return False


def check_xrds() -> bool:
    """Check if core XRDs are recognized."""
    print("\n🔍 Checking XRD definitions...")

    expected_xrds = [
        "xnetworks.networking.examples.crossplane.io",
        "xclusters.compute.examples.crossplane.io",
        "xdatabases.database.examples.crossplane.io"
    ]

    code, stdout, stderr = run_command(["kubectl", "get", "xrd"])
    if code != 0:
        print("❌ Error getting XRDs")
        return False

    xrds = stdout.strip().split('\n')[1:] if stdout.strip() else []
    xrd_names = [line.split()[0] for line in xrds if line.strip()]

    all_present = True
    for xrd in expected_xrds:
        if xrd in xrd_names:
            print(f"  ✅ {xrd}")
        else:
            print(f"  ❌ {xrd} not found")
            all_present = False

    return all_present


def setup_gitops(dry_run: bool = False) -> bool:
    """Set up Flux CD for GitOps automation."""
    print("\n⚙️  Setting up GitOps with Flux CD...")

    # Check if Flux is already installed
    code, stdout, stderr = run_command([
        "kubectl", "get", "namespace", "flux-system"
    ])
    if code == 0:
        print("✅ Flux already installed (flux-system namespace exists)")
        return True

    # Install Flux
    print("Installing Flux CLI...")
    # Note: This assumes flux CLI is available. In practice, would need to install it first.
    code, stdout, stderr = run_command(["flux", "check", "--pre"], dry_run=dry_run)
    if code != 0 and not dry_run:
        print("❌ Flux CLI not available or cluster not ready")
        print("   Install Flux: https://fluxcd.io/flux/installation/")
        return False

    code, stdout, stderr = run_command(["flux", "install"], dry_run=dry_run, timeout=600)
    if code != 0 and not dry_run:
        print(f"❌ Flux installation failed: {stderr}")
        return False
    print("✅ Flux installed")

    # Create GitRepository
    print("Creating GitRepository resource...")
    git_repo = """apiVersion: source.toolkit.fluxcd.io/v1
kind: GitRepository
metadata:
  name: crossplane-infra
  namespace: flux-system
spec:
  interval: 5m
  url: https://github.com/lloydchang/agentic-reconciliation-engine
  ref:
    branch: main
  secretRef:
    name: github-pat
"""

    code, stdout, stderr = run_command(
        ["kubectl", "apply", "-f", "-"],
        dry_run=dry_run,
        input=git_repo
    )
    if code != 0 and not dry_run:
        print(f"❌ Failed to create GitRepository: {stderr}")
        # Try without secretRef if private repo issues
        git_repo_public = git_repo.replace("  secretRef:\n    name: github-pat\n", "")
        code, stdout, stderr = run_command(
            ["kubectl", "apply", "-f", "-"],
            dry_run=dry_run,
            input=git_repo_public
        )
        if code != 0:
            return False
    print("✅ GitRepository created")

    # Create Kustomization
    print("Creating Kustomization...")
    kustomization = """apiVersion: kustomize.toolkit.fluxcd.io/v1beta1
kind: Kustomization
metadata:
  name: crossplane
  namespace: flux-system
spec:
  interval: 10m
  path: ./core/operators/control-plane/crossplane
  prune: true
  sourceRef:
    kind: GitRepository
    name: crossplane-infra
  validation: client
  wait: true
"""

    code, stdout, stderr = run_command(
        ["kubectl", "apply", "-f", "-"],
        dry_run=dry_run,
        input=kustomization
    )
    if code != 0 and not dry_run:
        print(f"❌ Failed to create Kustomization: {stderr}")
        return False
    print("✅ Kustomization created")

    print("\n⏳ Watching sync status...")
    print("Run: kubectl get kustomization -n flux-system -w")
    return True


def update_orchestrator() -> bool:
    """Update multi-cloud orchestrator to detect Crossplane resources."""
    print("\n🔧 Updating multi-cloud orchestrator...")

    orchestrator_path = "core/ai/skills/orchestrate-automation/scripts/multi_cloud_orchestrator.py"

    # Check if CrossplaneProvider class exists
    code, stdout, stderr = run_command([
        "grep", "-q", "class CrossplaneProvider", orchestrator_path
    ])

    if code == 0:
        print("✅ CrossplaneProvider already implemented")
        return True

    print("⚠️  CrossplaneProvider not found - needs implementation")
    print("   This requires manual coding as described in the Phase 1 plan.")
    print("   Expected location: multi_cloud_orchestrator.py")
    print("   Methods needed: list_clusters, get_database_connection, etc.")
    return False


def main():
    parser = argparse.ArgumentParser(
        description="Automated Phase 1 Crossplane Migration Implementation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be executed without making changes")
    parser.add_argument("--skip-providers", action="store_true",
                        help="Skip provider installation")
    parser.add_argument("--skip-gitops", action="store_true",
                        help="Skip GitOps/Flux setup")
    parser.add_argument("--test-resource", action="store_true",
                        help="Create test managed resource")
    args = parser.parse_args()

    print("=" * 60)
    print("PHASE 1: CROSSPLANE FOUNDATION & PROVIDER VALIDATION")
    print("=" * 60)

    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Prerequisites check failed. Exiting.")
        sys.exit(1)

    # Install providers
    if not args.skip_providers:
        if not install_providers(dry_run=args.dry_run):
            print("\n❌ Provider installation failed. Exiting.")
            sys.exit(1)
    else:
        print("\n⏭️  Skipping provider installation")

    # Verify providers
    if not verify_providers():
        print("\n⚠️  Provider verification had warnings")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            sys.exit(1)

    # Check XRDs
    if not check_xrds():
        print("\n⚠️  XRD check had warnings")
    else:
        print("\n✅ Core XRDs verified")

    # Create test resource
    if args.test_resource:
        if not create_test_resource(dry_run=args.dry_run):
            print("\n⚠️  Test resource creation failed")
    else:
        print("\n⏭️  Skipping test resource (use --test-resource to create)")

    # Setup GitOps
    if not args.skip_gitops:
        if not setup_gitops(dry_run=args.dry_run):
            print("\n⚠️  GitOps setup had issues")
    else:
        print("\n⏭️  Skipping GitOps setup")

    # Update orchestrator
    if not update_orchestrator():
        print("\n⚠️  Orchestrator update needed (manual implementation required)")

    print("\n" + "=" * 60)
    print("PHASE 1 AUTOMATION COMPLETE")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Review provider health: kubectl get providers -A")
    print("2. Check XRDs: kubectl get xrd")
    print("3. Monitor test resources: kubectl get buckets -n crossplane-system -w")
    print("4. Implement CrossplaneProvider in multi_cloud_orchestrator.py")
    print("5. Proceed to Phase 2: Network Migration")
    print("\nSee docs/migration/PHASE1-IMPLEMENTATION-PLAN.md for details.")


if __name__ == "__main__":
    main()
