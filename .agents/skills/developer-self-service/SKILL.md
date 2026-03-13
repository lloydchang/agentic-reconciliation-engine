---
name: developer-self-service
description: >
  Use this skill to implement and operate an Internal Developer Portal (IDP)
  and self-service catalog for platform capabilities. Triggers: any request to
  set up or manage a Backstage developer portal, create a self-service template
  for a new service or environment, onboard a developer team to the platform,
  build a service catalog, automate the golden-path service scaffolding, or
  reduce toil for engineering teams that need platform resources.
tools:
  - bash
  - computer
---

# Developer Self-Service Skill

Build and operate the Internal Developer Portal (IDP) using Backstage.
Provide golden-path templates, a service catalog, and automated provisioning
so engineering teams can self-serve platform resources without waiting for
the platform team.

---

## Platform: Backstage

```bash
# Create new Backstage app
npx @backstage/create-app@latest --name platform-portal

# Install required plugins
cd platform-portal
yarn --cwd packages/app add \
  @backstage/plugin-kubernetes \
  @backstage/plugin-techdocs \
  @backstage/plugin-github-actions \
  @roadiehq/backstage-plugin-argo-cd \
  @backstage-community/plugin-cost-insights

# Start in dev
yarn dev
```

---

## Service Catalog

### catalog-info.yaml (per service)
```yaml
apiVersion: backstage.io/v1alpha1
kind: Component
metadata:
  name: ${SERVICE_NAME}
  description: ${SERVICE_DESCRIPTION}
  annotations:
    github.com/project-slug: org/${REPO_NAME}
    backstage.io/kubernetes-id: ${SERVICE_NAME}
    backstage.io/kubernetes-namespace: ${TENANT_ID}
    argocd/app-name: ${SERVICE_NAME}-${ENV}
    backstage.io/techdocs-ref: dir:.
  tags:
    - ${TENANT_ID}
    - ${SERVICE_TYPE}
  links:
    - url: https://${TENANT_ID}.app.example.com
      title: Production
    - url: https://grafana.internal/d/${DASHBOARD_ID}
      title: Dashboard
spec:
  type: service
  lifecycle: production
  owner: group:${TEAM_NAME}
  system: ${TENANT_ID}
  dependsOn:
    - component:${DATABASE_SERVICE}
    - resource:${QUEUE_RESOURCE}
  providesApis:
    - ${SERVICE_NAME}-api
```

### Auto-Register All Services
```bash
# Scan all repos for catalog-info.yaml and register in Backstage
for repo in $(gh repo list "$GITHUB_ORG" --limit 200 --json name -q '.[].name'); do
  if gh api "repos/${GITHUB_ORG}/${repo}/contents/catalog-info.yaml" &>/dev/null; then
    curl -X POST "${BACKSTAGE_URL}/api/catalog/locations" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $BACKSTAGE_TOKEN" \
      -d "{\"type\":\"url\",\"target\":\"https://github.com/${GITHUB_ORG}/${repo}/blob/main/catalog-info.yaml\"}"
  fi
done
```

---

## Golden-Path Templates

### New Service Template (Scaffolder)
```yaml
# template.yaml
apiVersion: scaffolder.backstage.io/v1beta3
kind: Template
metadata:
  name: new-service
  title: New Platform Service
  description: Scaffold a new service with CI/CD, K8s manifests, and observability baked in
  tags:
    - recommended
    - platform
spec:
  owner: platform-team
  type: service
  parameters:
    - title: Service Details
      required: [name, owner, description]
      properties:
        name:
          title: Service Name
          type: string
          pattern: '^[a-z][a-z0-9-]{2,48}$'
        owner:
          title: Owner Team
          type: string
          ui:field: OwnerPicker
          ui:options:
            catalogFilter:
              kind: Group
        language:
          title: Language / Framework
          type: string
          default: python-fastapi
          enum: [python-fastapi, typescript-express, java-spring, go-gin]
        database:
          title: Needs a database?
          type: boolean
          default: false

  steps:
    - id: fetch
      name: Fetch template
      action: fetch:template
      input:
        url: ./skeleton
        values:
          name: ${{ parameters.name }}
          owner: ${{ parameters.owner }}
          language: ${{ parameters.language }}
          database: ${{ parameters.database }}

    - id: publish
      name: Create GitHub repo
      action: publish:github
      input:
        allowedHosts: ['github.com']
        description: ${{ parameters.description }}
        repoUrl: github.com?repo=${{ parameters.name }}&owner=${{ parameters.owner }}
        defaultBranch: main
        repoVisibility: internal

    - id: register
      name: Register in catalog
      action: catalog:register
      input:
        repoContentsUrl: ${{ steps.publish.output.repoContentsUrl }}
        catalogInfoPath: /catalog-info.yaml

    - id: provision-k8s
      name: Create K8s namespace + RBAC
      action: http:backstage:request
      input:
        method: POST
        path: /api/proxy/platform-api/namespaces
        body:
          service: ${{ parameters.name }}
          owner: ${{ parameters.owner }}
          database: ${{ parameters.database }}
```

---

## Self-Service Actions (via Backstage Software Templates)

Provide these as one-click actions in the portal:

| Action                      | Automated? | Approval? |
|-----------------------------|------------|-----------|
| Create new service (golden path) | ✅    | None      |
| Add a database to my service    | ✅     | None      |
| Scale my service (HPA limits)   | ✅     | None      |
| Promote to production           | ✅     | TechLead  |
| Request a secret                | ✅     | SecOps    |
| Add a new environment           | ✅     | Platform  |
| Get production access (break-glass) | ⚠️ | CISO      |
| Request a new cluster           | ⚠️     | Platform  |

---

## Team Onboarding Checklist

Auto-generated when a new team joins the platform:

```markdown
## Platform Onboarding: ${TEAM_NAME}

### Automated (done on your behalf)
- [x] GitHub team created with correct permissions
- [x] Backstage catalog entry created
- [x] Dev and staging namespaces provisioned
- [x] CI/CD pipeline scaffolded (GitHub Actions)
- [x] Observability dashboards provisioned (Grafana)
- [x] Cost center tag applied
- [x] Platform Slack channel created: #${TEAM_NAME}-platform

### You need to do
- [ ] Review the platform handbook: ${HANDBOOK_URL}
- [ ] Book a 30-min platform intro call: ${CALENDAR_LINK}
- [ ] Confirm your on-call rotation preference

### Resources
- Platform portal:  ${BACKSTAGE_URL}
- Runbooks:         ${RUNBOOKS_URL}
- Slack:            #platform-support
- SLA targets:      ${SLA_DOC_URL}
```

---

## Developer Experience Metrics

Track golden-path adoption:

```
Developer Experience Metrics — [Month]
──────────────────────────────────────
Teams using golden-path templates:  28/34 (82%)
Services with catalog entries:      156/162 (96%)
Self-service vs manual requests:    89% / 11%
Avg time to first deployment (new service): 22 min ↓ from 3 days
P75 time to answer platform question (portal): 45 sec
Support tickets (platform):        41 ↓ 31% vs last month
```

---

## Examples

- "Set up the developer portal for the new engineering org"
- "Create a Backstage template for a new Python microservice with all platform defaults"
- "Onboard the payments team to the platform — run the full checklist"
- "Show me which teams haven't registered their services in the catalog"
- "Add a self-service action for developers to request a read-replica for their database"

---

## Output Format

```json
{
  "operation": "scaffold|onboard|catalog-register|template-create|audit",
  "service": "string",
  "team": "string",
  "template": "string",
  "catalog_registered": true,
  "pipeline_created": true,
  "namespace_provisioned": true,
  "status": "success|failure",
  "portal_url": "string"
}
```
