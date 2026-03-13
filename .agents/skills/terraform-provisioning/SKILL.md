---
name: terraform-provisioning
description: >
  Use this skill to automate cloud infrastructure provisioning,
  modification, and teardown using Terraform, CDK, CloudFormation,
  ARM templates, Google Cloud Infrastructure Manager Terraform Blueprint
  across AWS, Azure, and GCP. Also validates IaC changes against company
  standards during code reviews or before merging infrastructure changes.
  Triggers: any request to provision, destroy, plan, or validate cloud
  infrastructure; generate or review Terraform, CDK, CloudFormation,
  ARM templates, or Blueprints; manage state files;
  run drift detection; or enforce infrastructure-as-code standards.
tools:
  - bash
  - computer
---

# Terraform Provisioning Skill

Automate multi-cloud infrastructure lifecycle using Terraform
with full plan → apply → validate → destroy workflows, modular
design patterns, and state management best practices.

---

## Workflow

### 1. Initialise & Validate
```bash
terraform init -backend-config="backend.hcl"
terraform validate
terraform fmt -check -recursive
```
Always run `validate` and `fmt` before any plan. Surface warnings as structured
output before proceeding.

### 2. Plan
```bash
terraform plan -out=tfplan -var-file="env/${ENV}.tfvars" -detailed-exitcode
```
Parse the plan output and summarise:
- Resources to **add** / **change** / **destroy**
- Any destructive actions → require explicit human approval before proceeding
- Estimated cost delta (if `infracost` is available)

### 3. Apply
```bash
terraform apply tfplan
```
Only apply after plan is approved. Stream output in real time. On failure:
- Capture the error block
- Attempt auto-remediation for known errors (provider version mismatch,
  missing permissions, quota exceeded)
- Otherwise surface a structured incident with context

### 4. Post-Apply Validation
- Run `terraform output -json` and verify expected values
- Ping key endpoints / run smoke tests defined in `tests/` directory
- Tag resources with `managed_by=terraform`, `env`, `owner`, `cost_center`

### 5. Drift Detection
```bash
terraform plan -detailed-exitcode -refresh=true
```
Schedule via cron or CI trigger. Report drift as a structured diff and open a
PR or incident ticket automatically.

---

## IaC Validation & Standards Enforcement

### Pre-Merge Validation
Validate Terraform/ARM/Bicep/CloudFormation/Google Cloud Infrastructure Manager changes against company standards during code reviews.

**When to Use:**
- During a pull request review for cloud infrastructure changes
- Before running `terraform apply` or IaC deployments

**Instructions:**
1. Run `terraform plan` or IaC validation tools
2. Check the code against `references/iac-naming-conventions.md` and `security-best-practices.md`
3. Verify that the change includes mandatory tags (e.g., `Owner`, `Environment`, `CostCenter`)
4. Highlight any deviation from modular deployment patterns
5. Output the specific lines of code that need adjustment and the reasons why

**Validation Checks:**
- **Naming Conventions**: Resources follow approved naming patterns
- **Mandatory Tagging**: All resources have required tags (`Owner`, `Environment`, `CostCenter`)
- **Security Standards**: No violations of security best practices
- **Modular Design**: Code follows approved architectural patterns
- **Documentation**: Modules have proper README and variable descriptions

---

## Module Standards

Follow these conventions for all generated modules:

```
modules/
  <cloud>-<resource>/
    main.tf        # resource definitions only
    variables.tf   # typed, described, validated inputs
    outputs.tf     # all useful attributes exported
    versions.tf    # required_providers pinned
    README.md      # auto-generated via terraform-docs
```

- Use `for_each` over `count` for multi-instance resources
- All variables must have `description` and `type`; use `validation` blocks
- Never hardcode secrets — use `data "azurerm_key_vault_secret"` or env vars
- Always pin provider versions with `~>` (pessimistic constraint)

---

## State Management

- Remote state could range from Azure Storage, Amazon S3, Google Cloud Infrastructure Manager, IBM HCP Terraform, Terraform Enterprise
- State locking enabled by default
- Workspaces per environment: `dev`, `staging`, `prod`
- Never edit state manually — use `terraform state mv/rm` commands only

---

## ARM Template Mode

When working with ARM/Bicep templates:
```bash
az deployment group validate --resource-group $RG --template-file main.bicep
az deployment group what-if  --resource-group $RG --template-file main.bicep
az deployment group create   --resource-group $RG --template-file main.bicep
```
Convert ARM JSON to Bicep using `az bicep decompile` when refactoring.

---

## Safety Rules

- **Never run `terraform apply` without a saved plan file**
- **Destructive operations** (delete, replace) require explicit `CONFIRM=true` env var
- Production applies must have a change-window ticket reference in the commit
- All modules must pass `tfsec` and `checkov` scans before merge
- Tag every resource; fail the plan if required tags are absent

---

## Examples

- "Provision a new Amazon EKS cluster in the us-east-1 region for the payments tenant"
- "Run drift detection on the prod environment and report changes"
- "Generate a Terraform module for an Azure Service Bus with dead-letter queues"
- "Destroy the staging environment after the release cycle"
- "Validate all modules against our security baseline"

---

## Output Format

Always return:
```json
{
  "operation": "plan|apply|destroy|drift-detect",
  "environment": "string",
  "status": "success|failure|pending_approval",
  "plan_summary": { "add": 0, "change": 0, "destroy": 0 },
  "resources_affected": [],
  "warnings": [],
  "next_action": "apply|review|abort"
}
```
