#!/usr/bin/env python3
"""
Migration wizard orchestrator.
"""
import argparse
import json
import os
import shutil
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterable, List, Sequence


class GitHostConnector(ABC):
    """Abstract Git host adapter used by the wizard."""

    def __init__(self, repo_url: str) -> None:
        self.repo_url = repo_url

    @abstractmethod
    def clone_repository(self, path: Path) -> None:
        """Clone the repository or sync existing clone."""

    @abstractmethod
    def push_branch(self, path: Path, branch: str) -> None:
        pass

    @abstractmethod
    def create_merge_request(self, path: Path, branch: str) -> None:
        pass


class LocalGitConnector(GitHostConnector):
    """Simple connector that assumes a bare Git environment."""

    def clone_repository(self, path: Path) -> None:
        if path.exists():
            print(f"[connector] Repository path {path} already exists, skipping clone.")
            return
        print("[connector] Cloning repository...")
        subprocess.run(["git", "clone", self.repo_url, str(path)], check=True)

    def push_branch(self, path: Path, branch: str) -> None:
        print(f"[connector] Pushing branch {branch}...")
        subprocess.run(["git", "push", "-u", "origin", branch], cwd=path, check=True)

    def create_merge_request(self, path: Path, branch: str) -> None:
        print("[connector] Merge request creation not implemented for local connector.")


class AzureDevOpsConnector(GitHostConnector):
    """Connector that uses Azure DevOps CLI for PR automation."""

    def __init__(self, repo_url: str) -> None:
        super().__init__(repo_url)

    def _auth_url(self) -> str:
        token = os.environ.get("AZURE_DEVOPS_TOKEN")
        if not token:
            raise RuntimeError("AZURE_DEVOPS_TOKEN must be set to clone from Azure DevOps.")
        if self.repo_url.startswith("https://"):
            return self.repo_url.replace("https://", f"https://{token}@", 1)
        return self.repo_url

    def _provider_metadata(self) -> dict:
        org = os.environ.get("AZURE_DEVOPS_ORG")
        project = os.environ.get("AZURE_DEVOPS_PROJECT")
        if not org or not project:
            raise RuntimeError("AZURE_DEVOPS_ORG and AZURE_DEVOPS_PROJECT must be set.")
        repo_path = self.repo_url.rstrip("/").split("/")[-1]
        return {"org": org, "project": project, "repo": repo_path}

    def clone_repository(self, path: Path) -> None:
        if path.exists():
            print(f"[connector] Repository path {path} already exists, skipping clone.")
            return
        auth_url = self._auth_url()
        print("[connector] Cloning Azure DevOps repository...")
        subprocess.run(["git", "clone", auth_url, str(path)], check=True)

    def push_branch(self, path: Path, branch: str) -> None:
        print(f"[connector] Pushing branch {branch} to Azure DevOps...")
        subprocess.run(["git", "push", "-u", "origin", branch], cwd=path, check=True)

    def create_merge_request(self, path: Path, branch: str) -> None:
        meta = self._provider_metadata()
        print("[connector] Creating Azure DevOps pull request...")
        subprocess.run(
            [
                "az",
                "repos",
                "pr",
                "create",
                "--org",
                f"https://dev.azure.com/{meta['org']}",
                "--project",
                meta["project"],
                "--repository",
                meta["repo"],
                "--source-branch",
                branch,
                "--target-branch",
                "main",
                "--title",
                "Migration wizard changes",
                "--description",
                "Automated migration wizard results.",
        ],
        cwd=path,
        check=True,
    )


class GitHubEnterpriseServerConnector(GitHostConnector):
    """Connector for GitHub Enterprise Server using gh CLI and personal access token."""

    def __init__(self, repo_url: str) -> None:
        super().__init__(repo_url)
        self.token = os.environ.get("GITHUB_ENTERPRISE_TOKEN")
        self.host = os.environ.get("GITHUB_ENTERPRISE_HOST")
        if not self.token or not self.host:
            raise RuntimeError("GITHUB_ENTERPRISE_TOKEN and GITHUB_ENTERPRISE_HOST are required.")

    def _auth_url(self) -> str:
        if self.repo_url.startswith("https://"):
            hostless = self.repo_url.split("https://", 1)[1]
            return f"https://{self.token}@{hostless}"
        raise RuntimeError("GitHub Enterprise Server repo URL must start with https://")

    def clone_repository(self, path: Path) -> None:
        if path.exists():
            print(f"[connector] Repository path {path} already exists, skipping clone.")
            return
        auth_url = self._auth_url()
        print("[connector] Cloning GitHub Enterprise Server repository...")
        subprocess.run(["git", "clone", auth_url, str(path)], check=True)

    def push_branch(self, path: Path, branch: str) -> None:
        print(f"[connector] Pushing branch {branch} to GitHub Enterprise Server...")
        subprocess.run(["git", "push", "-u", "origin", branch], cwd=path, check=True)

    def create_merge_request(self, path: Path, branch: str) -> None:
        print("[connector] Creating GitHub Enterprise Server pull request via gh CLI...")
        subprocess.run(
            ["gh", "pr", "create", "--repo", f"{self.host}/{path.name}", "--base", "main", "--head", branch, "--title", "Migration wizard changes", "--body", "Automated migration wizard results."],
            cwd=path,
            check=True,
        )


class GitHubEnterpriseCloudConnector(GitHostConnector):
    """Connector for GitHub Enterprise Cloud using gh CLI."""

    def __init__(self, repo_url: str) -> None:
        super().__init__(repo_url)
        self.token = os.environ.get("GITHUB_ENTERPRISE_TOKEN")
        if not self.token:
            raise RuntimeError("GITHUB_ENTERPRISE_TOKEN must be set for GitHub Enterprise Cloud.")

    def _auth_url(self) -> str:
        if self.repo_url.startswith("https://"):
            hostless = self.repo_url.split("https://", 1)[1]
            return f"https://{self.token}@{hostless}"
        raise RuntimeError("GitHub Enterprise Cloud repo URL must start with https://")

    def clone_repository(self, path: Path) -> None:
        if path.exists():
            print(f"[connector] Repository path {path} already exists, skipping clone.")
            return
        auth_url = self._auth_url()
        print("[connector] Cloning GitHub Enterprise Cloud repository...")
        subprocess.run(["git", "clone", auth_url, str(path)], check=True)

    def push_branch(self, path: Path, branch: str) -> None:
        print(f"[connector] Pushing branch {branch} to GitHub Enterprise Cloud...")
        subprocess.run(["git", "push", "-u", "origin", branch], cwd=path, check=True)

    def create_merge_request(self, path: Path, branch: str) -> None:
        print("[connector] Creating GitHub Enterprise Cloud pull request via gh CLI...")
        subprocess.run(
            [
                "gh",
                "pr",
                "create",
                "--repo",
                path.name,
                "--base",
                "main",
                "--head",
                branch,
                "--title",
                "Migration wizard changes",
                "--body",
                "Automated migration wizard results.",
        ],
        cwd=path,
        check=True,
    )


class GitLabConnector(GitHostConnector):
    """Connector for GitLab using GitLab API and gh CLI/push."""

    def __init__(self, repo_url: str) -> None:
        super().__init__(repo_url)
        self.host = os.environ.get("GITLAB_HOST", "gitlab.com")
        self.token = os.environ.get("GITLAB_TOKEN")
        if not self.token:
            raise RuntimeError("GITLAB_TOKEN must be set for GitLab connector.")

    def _auth_url(self) -> str:
        if self.repo_url.startswith("https://"):
            hostless = self.repo_url.split("https://", 1)[1]
            return f"https://oauth2:{self.token}@{hostless}"
        raise RuntimeError("GitLab repo URL must start with https://")

    def _project_path(self) -> str:
        hostless = self.repo_url.split("https://", 1)[1]
        return hostless.strip("/").replace(".git", "")

    def clone_repository(self, path: Path) -> None:
        if path.exists():
            print(f"[connector] Repository path {path} already exists, skipping clone.")
            return
        auth_url = self._auth_url()
        print("[connector] Cloning GitLab repository...")
        subprocess.run(["git", "clone", auth_url, str(path)], check=True)

    def push_branch(self, path: Path, branch: str) -> None:
        print(f"[connector] Pushing branch {branch} to GitLab...")
        subprocess.run(["git", "push", "-u", "origin", branch], cwd=path, check=True)

    def create_merge_request(self, path: Path, branch: str) -> None:
        project = self._project_path()
        print("[connector] Creating GitLab merge request via API...")
        subprocess.run(
            [
                "curl",
                "-X",
                "POST",
                f"https://{self.host}/api/v4/projects/{project.replace('/', '%2F')}/merge_requests",
                "-H",
                f"PRIVATE-TOKEN: {self.token}",
                "-d",
                f"source_branch={branch}",
                "-d",
                "target_branch=main",
                "-d",
                "title=Migration wizard changes",
                "-d",
                "description=Automated migration wizard results.",
            ],
            cwd=path,
            check=True,
        )


class BitbucketDataCenterConnector(GitHostConnector):
    """Connector for Bitbucket Data Center via REST API."""

    def __init__(self, repo_url: str) -> None:
        super().__init__(repo_url)
        self.host = os.environ.get("BITBUCKET_DC_HOST")
        self.user = os.environ.get("BITBUCKET_DC_USER")
        self.token = os.environ.get("BITBUCKET_DC_TOKEN")
        if not self.host or not self.user or not self.token:
            raise RuntimeError("BITBUCKET_DC_HOST, BITBUCKET_DC_USER, and BITBUCKET_DC_TOKEN required.")

    def _auth_url(self) -> str:
        if self.repo_url.startswith("https://"):
            hostless = self.repo_url.split("https://", 1)[1]
            return f"https://{self.user}:{self.token}@{hostless}"
        raise RuntimeError("Bitbucket Data Center repo URL must start with https://")

    def _project_repo(self) -> str:
        hostless = self.repo_url.split("https://", 1)[1]
        return hostless.strip("/").replace(".git", "")

    def clone_repository(self, path: Path) -> None:
        if path.exists():
            print(f"[connector] Repository path {path} already exists, skipping clone.")
            return
        auth_url = self._auth_url()
        print("[connector] Cloning Bitbucket Data Center repository...")
        subprocess.run(["git", "clone", auth_url, str(path)], check=True)

    def push_branch(self, path: Path, branch: str) -> None:
        print(f"[connector] Pushing branch {branch} to Bitbucket Data Center...")
        subprocess.run(["git", "push", "-u", "origin", branch], cwd=path, check=True)

    def create_merge_request(self, path: Path, branch: str) -> None:
        project_repo = self._project_repo()
        print("[connector] Creating Bitbucket Data Center pull request...")
        subprocess.run(
            [
                "curl",
                "-u",
                f"{self.user}:{self.token}",
                "-X",
                "POST",
                f"https://{self.host}/rest/api/1.0/projects/{project_repo.split('/')[0]}/repos/{project_repo.split('/')[1]}/pull-requests",
                "-H",
                "Content-Type: application/json",
                "-d",
                json.dumps(
                    {
                        "title": "Migration wizard changes",
                        "description": "Automated migration wizard results.",
                        "state": "OPEN",
                        "open": True,
                        "closed": False,
                        "fromRef": {"id": f"refs/heads/{branch}", "repository": {"slug": project_repo.split('/')[1]}},
                        "toRef": {"id": "refs/heads/main"},
                    }
                ),
        ],
        cwd=path,
        check=True,
    )


class BitbucketCloudConnector(GitHostConnector):
    """Connector for Bitbucket Cloud using API token."""

    def __init__(self, repo_url: str) -> None:
        super().__init__(repo_url)
        self.username = os.environ.get("BITBUCKET_USER")
        self.token = os.environ.get("BITBUCKET_TOKEN")
        if not self.username or not self.token:
            raise RuntimeError("BITBUCKET_USER and BITBUCKET_TOKEN required for Bitbucket Cloud.")

    def _auth_url(self) -> str:
        if self.repo_url.startswith("https://"):
            hostless = self.repo_url.split("https://", 1)[1]
            return f"https://{self.username}:{self.token}@{hostless}"
        raise RuntimeError("Bitbucket Cloud repo URL must start with https://")

    def clone_repository(self, path: Path) -> None:
        if path.exists():
            print(f"[connector] Repository path {path} already exists, skipping clone.")
            return
        auth_url = self._auth_url()
        print("[connector] Cloning Bitbucket Cloud repository...")
        subprocess.run(["git", "clone", auth_url, str(path)], check=True)

    def push_branch(self, path: Path, branch: str) -> None:
        print(f"[connector] Pushing branch {branch} to Bitbucket Cloud...")
        subprocess.run(["git", "push", "-u", "origin", branch], cwd=path, check=True)

    def create_merge_request(self, path: Path, branch: str) -> None:
        project_repo = self.repo_url.split("https://", 1)[1].replace(".git", "")
        workspace = project_repo.split("/")[0]
        repo_slug = project_repo.split("/")[1]
        print("[connector] Creating Bitbucket Cloud pull request via API...")
        subprocess.run(
            [
                "curl",
                "-X",
                "POST",
                f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo_slug}/pullrequests",
                "-u",
                f"{self.username}:{self.token}",
                "-H",
                "Content-Type: application/json",
                "-d",
                json.dumps(
                    {
                        "title": "Migration wizard changes",
                        "source": {"branch": {"name": branch}},
                        "destination": {"branch": {"name": "main"}},
                        "description": "Automated migration wizard results.",
                    }
                ),
        ],
        cwd=path,
        check=True,
    )


class GCPSSMConnector(GitHostConnector):
    """Connector for GCP Secure Source Manager / Cloud Source Repositories."""

    def clone_repository(self, path: Path) -> None:
        if path.exists():
            print(f"[connector] Repository path {path} already exists, skipping clone.")
            return
        print("[connector] Cloning GCP Secure Source Manager repository...")
        subprocess.run(["git", "clone", self.repo_url, str(path)], check=True)

    def push_branch(self, path: Path, branch: str) -> None:
        print(f"[connector] Pushing branch {branch} to GCP Secure Source Manager...")
        subprocess.run(["git", "push", "-u", "origin", branch], cwd=path, check=True)

    def create_merge_request(self, path: Path, branch: str) -> None:
        print("[connector] GCP Secure Source Manager does not expose a centralized PR API; open PRs via the Cloud Console.")


class AWSCodeCommitConnector(GitHostConnector):
    """Connector for AWS CodeCommit using HTTPS + git credentials helper."""

    def clone_repository(self, path: Path) -> None:
        if path.exists():
            print(f"[connector] Repository path {path} already exists, skipping clone.")
            return
        print("[connector] Cloning AWS CodeCommit repository...")
        subprocess.run(["git", "clone", self.repo_url, str(path)], check=True)

    def push_branch(self, path: Path, branch: str) -> None:
        print(f"[connector] Pushing branch {branch} to AWS CodeCommit...")
        subprocess.run(["git", "push", "-u", "origin", branch], cwd=path, check=True)

    def create_merge_request(self, path: Path, branch: str) -> None:
        print("[connector] AWS CodeCommit does not support PR creation via CLI; please open via AWS Console.")


class AzureDevOpsConnector(GitHostConnector):
    """Connector that uses Azure DevOps CLI for PR automation."""

    def _auth_url(self, repo_url: str) -> str:
        token = os.environ.get("AZURE_DEVOPS_TOKEN")
        if not token:
            raise RuntimeError("AZURE_DEVOPS_TOKEN must be set to clone from Azure DevOps.")
        if repo_url.startswith("https://"):
            return repo_url.replace("https://", f"https://{token}@", 1)
        return repo_url

    def _provider_metadata(self, repo_url: str) -> dict:
        org = os.environ.get("AZURE_DEVOPS_ORG")
        project = os.environ.get("AZURE_DEVOPS_PROJECT")
        if not org or not project:
            raise RuntimeError("AZURE_DEVOPS_ORG and AZURE_DEVOPS_PROJECT must be set.")
        repo_path = repo_url.rstrip("/").split("/")[-1]
        return {"org": org, "project": project, "repo": repo_path}

    def clone_repository(self, repo_url: str, path: Path) -> None:
        if path.exists():
            print(f"[connector] Repository path {path} already exists, skipping clone.")
            return
        auth_url = self._auth_url(repo_url)
        print("[connector] Cloning Azure DevOps repository...")
        subprocess.run(["git", "clone", auth_url, str(path)], check=True)

    def push_branch(self, path: Path, branch: str) -> None:
        print(f"[connector] Pushing branch {branch} to Azure DevOps...")
        subprocess.run(["git", "push", "-u", "origin", branch], cwd=path, check=True)

    def create_merge_request(self, path: Path, branch: str) -> None:
        meta = self._provider_metadata(path.as_uri())
        print("[connector] Creating Azure DevOps pull request...")
        subprocess.run([
            "az", "repos", "pr", "create",
            "--org", f"https://dev.azure.com/{meta['org']}",
            "--project", meta["project"],
            "--repository", meta["repo"],
            "--source-branch", branch,
            "--target-branch", "main",
            "--title", "Migration wizard changes",
            "--description", "Automated migration wizard results.",
        ], cwd=path, check=True)


def run_helper(script: Path, args: Sequence[str]) -> None:
    subprocess.run([str(script)] + list(args), check=True)


def reorder_overlays(kustomization: Path, ordered: Iterable[str]) -> None:
    text = kustomization.read_text().splitlines()
    start = None
    end = None
    for i, line in enumerate(text):
        if line.strip().startswith("resources:"):
            start = i
            break
    if start is None:
        raise RuntimeError("resources block not found in kustomization")
    for j in range(start + 1, len(text)):
        if text[j].startswith("# SOPS configuration"):
            end = j
            break
    end = end or len(text)
    base = [line for line in text[start + 1 : end] if line.strip()]
    # keep base entries until "cloud-..." overlays
    fixed = [line for line in base if not line.strip().startswith("./cloud-") and "local-emulator" not in line]
    new_resources = fixed + [f"  - {entry}" for entry in ordered]
    text = text[: start + 1] + new_resources + text[end:]
    kustomization.write_text("\n".join(text) + "\n")
    print(f"[wizard] Reordered overlays to: {ordered}")


def run_ci_gate(repo_path: Path, gate_cmd: Sequence[str]) -> None:
    print(f"[wizard] Running CI gate: {' '.join(gate_cmd)}")
    subprocess.run(list(gate_cmd), cwd=repo_path, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Multi-cloud migration wizard.")
    parser.add_argument("--repo-url", required=True, help="Git repository URL (any provider).")
    parser.add_argument("--branch", default="migration-wizard", help="Working branch.")
    parser.add_argument("--workdir", default="workspace", help="Local workspace directory.")
    parser.add_argument(
        "--overlay-order",
        nargs="+",
        default=["./bootstrap", "./hub", "./cloud-azure", "./cloud-aws", "./cloud-gcp"],
        help="Ordered list of overlays to apply.",
    )
    parser.add_argument(
        "--overlay-order-file",
        default="control-plane/flux/overlay-order.txt",
        help="Path to a file containing the overlay order list.",
    )
    parser.add_argument(
        "--use-overlay-order",
        choices=["true", "false"],
        default="true",
        help="Run scripts/apply-overlay-order.sh before manual ordering.",
    )
    parser.add_argument(
        "--helper-script",
        nargs="*",
        default=["./scripts/enable-cloud.sh"],
        help="Helper scripts to invoke after ordering.",
    )
    parser.add_argument(
        "--ci-gate",
        nargs="*",
        default=["./scripts/bootstrap.sh"],
        help="Command (with args) that validates CI policy.",
    )
    parser.add_argument("--emulator", choices=["enable", "disable"], help="Toggle Azure emulator.")
    parser.add_argument(
        "--connector",
        choices=[
            "local",
            "azure-devops",
            "github-enterprise-server",
            "github-enterprise-cloud",
            "gitlab",
            "bitbucket-dc",
            "bitbucket-cloud",
            "codecommit",
            "gcp-ssm",
        ],
        default="local",
        help="Git host connector to use for clone/push/PR.",
    )
    args = parser.parse_args()

    workdir = Path(args.workdir).expanduser().resolve()
    workdir.mkdir(parents=True, exist_ok=True)
    if args.connector == "azure-devops":
        connector = AzureDevOpsConnector(args.repo_url)
    elif args.connector == "github-enterprise-server":
        connector = GitHubEnterpriseServerConnector(args.repo_url)
    elif args.connector == "github-enterprise-cloud":
        connector = GitHubEnterpriseCloudConnector(args.repo_url)
    elif args.connector == "gitlab":
        connector = GitLabConnector(args.repo_url)
    elif args.connector == "bitbucket-dc":
        connector = BitbucketDataCenterConnector(args.repo_url)
    elif args.connector == "bitbucket-cloud":
        connector = BitbucketCloudConnector(args.repo_url)
    elif args.connector == "codecommit":
        connector = AWSCodeCommitConnector(args.repo_url)
    elif args.connector == "gcp-ssm":
        connector = GCPSSMConnector(args.repo_url)
    else:
        connector = LocalGitConnector(args.repo_url)
    connector.clone_repository(args.repo_url, workdir / "repo")
    repo_path = workdir / "repo"
    subprocess.run(["git", "checkout", "-B", args.branch], cwd=repo_path, check=True)

    apply_order_script = Path("scripts/apply-overlay-order.sh")
    temp_order = None
    if args.use_overlay_order == "true" and apply_order_script.exists():
        order_file = Path(args.overlay_order_file)
        if args.overlay_order:
            import tempfile

            fd, path = tempfile.mkstemp()
            temp_order = Path(path)
            Path(fd).close()
            temp_order.write_text("\n".join(args.overlay_order) + "\n")
            order_arg = str(temp_order)
        else:
            order_arg = args.overlay_order_file
        subprocess.run([str(apply_order_script), order_arg], cwd=repo_path, check=True)
    else:
        overlay_file = repo_path / "control-plane" / "flux" / "kustomization.yaml"
        reorder_overlays(overlay_file, args.overlay_order)

    logician_script = Path("scripts/overlay-logician.py")
    if logician_script.exists():
        subprocess.run([str(logician_script)], cwd=repo_path, check=True)
    if temp_order:
        temp_order.unlink()

    if args.emulator:
        run_helper(Path("scripts/enable-cloud.sh"), ["azure", f"--emulator={args.emulator}"])

    for helper in args.helper_script:
        run_helper(Path(helper), ["azure"])

    run_ci_gate(repo_path, args.ci_gate)

    connector.push_branch(repo_path, args.branch)
    connector.create_merge_request(repo_path, args.branch)


if __name__ == "__main__":
    main()
