---
name: multi-cloud-networking
description: >
  Use this skill to design, provision, and operate network infrastructure
  across Azure, AWS, and GCP. Triggers: any request to provision or create VNets/VPCs, spoke networks,
  peering connections, private endpoints, DNS zones, load balancers, WAF
  rules, firewall policies, NSGs, ExpressRoute/Direct Connect circuits,
  troubleshoot connectivity between tenants, diagnose why service cannot reach endpoint, services, or clouds.
tools:
  - bash
  - computer
---

# Multi-Cloud Networking Skill

Automate the full network lifecycle: hub-and-spoke topology, private
connectivity, DNS, traffic management, WAF, and zero-trust firewall policy.

---

## Network Architecture: Hub-and-Spoke

```
Hub VNet (shared services)      10.0.0.0/16
  Subnets:
    AzureFirewallSubnet         10.0.0.0/26
    GatewaySubnet               10.0.1.0/27
    AzureBastionSubnet          10.0.2.0/27
    snet-shared                 10.0.4.0/24

Spoke VNets (per tenant)
    spoke-t-acme-prod           10.10.0.0/16
    spoke-t-widgets-prod        10.11.0.0/16
    ...
```

---

## Provisioning

### Hub VNet
```bash
az network vnet create \
  --resource-group "$HUB_RG" \
  --name "vnet-hub-${REGION}" \
  --address-prefixes "10.0.0.0/16" \
  --location "$REGION"
```

### Tenant Spoke + Bidirectional Peering
```bash
create_spoke() {
  local tenant_id=$1 cidr=$2

  az network vnet create \
    --resource-group "rg-${tenant_id}" \
    --name "vnet-spoke-${tenant_id}" \
    --address-prefixes "$cidr"

  az network vnet peering create \
    --resource-group "rg-${tenant_id}" \
    --name "peer-spoke-to-hub" \
    --vnet-name "vnet-spoke-${tenant_id}" \
    --remote-vnet "${HUB_VNET_ID}" \
    --allow-vnet-access true \
    --use-remote-gateways true

  az network vnet peering create \
    --resource-group "$HUB_RG" \
    --name "peer-hub-to-${tenant_id}" \
    --vnet-name "vnet-hub-${REGION}" \
    --remote-vnet "${SPOKE_VNET_ID}" \
    --allow-vnet-access true \
    --allow-gateway-transit true
}
```

---

## Private Endpoints

```bash
# Create private endpoint (example: Azure SQL)
az network private-endpoint create \
  --resource-group "rg-${TENANT_ID}" \
  --name "pe-sql-${TENANT_ID}" \
  --vnet-name "vnet-spoke-${TENANT_ID}" \
  --subnet "snet-data" \
  --private-connection-resource-id "${SQL_SERVER_ID}" \
  --group-id sqlServer \
  --connection-name "pec-sql-${TENANT_ID}"

# Register DNS A record in hub private zone
PE_IP=$(az network private-endpoint show \
  --name "pe-sql-${TENANT_ID}" -g "rg-${TENANT_ID}" \
  --query 'customDnsConfigs[0].ipAddresses[0]' -o tsv)

az network private-dns record-set a add-record \
  --resource-group "$HUB_RG" \
  --zone-name "privatelink.database.windows.net" \
  --record-set-name "sql-${TENANT_ID}" \
  --ipv4-address "$PE_IP"
```

---

## NSG Baseline (Deny-All + Hub Allow)

```bash
az network nsg create \
  --resource-group "rg-${TENANT_ID}" \
  --name "nsg-workload-${TENANT_ID}"

# Allow inbound from hub only
az network nsg rule create \
  --nsg-name "nsg-workload-${TENANT_ID}" \
  -g "rg-${TENANT_ID}" \
  --name AllowFromHub --priority 100 \
  --source-address-prefixes "10.0.0.0/16" \
  --destination-port-ranges "*" \
  --access Allow --direction Inbound

# Deny all else
az network nsg rule create \
  --nsg-name "nsg-workload-${TENANT_ID}" \
  -g "rg-${TENANT_ID}" \
  --name DenyAll --priority 4096 \
  --source-address-prefixes "*" \
  --destination-port-ranges "*" \
  --access Deny --direction Inbound
```

---

## Private DNS Zones (Hub-Hosted)

```bash
ZONES=(
  "privatelink.database.windows.net"
  "privatelink.blob.core.windows.net"
  "privatelink.vaultcore.azure.net"
  "privatelink.servicebus.windows.net"
  "privatelink.azurecr.io"
)
for ZONE in "${ZONES[@]}"; do
  az network private-dns zone create -g "$HUB_RG" --name "$ZONE"
  az network private-dns link vnet create \
    -g "$HUB_RG" --zone-name "$ZONE" \
    --name "link-hub" \
    --virtual-network "vnet-hub-${REGION}" \
    --registration-enabled false
done
```

---

## Connectivity Troubleshooting

```bash
diagnose_connectivity() {
  local src_vm=$1 dest_ip=$2 port=$3

  az network watcher test-connectivity \
    --resource-group "$RG" \
    --source-resource "$src_vm" \
    --dest-address "$dest_ip" \
    --dest-port "$port" \
    --output json | jq '{
      result: .connectionStatus,
      hops: [.hops[] | {type, address}],
      issues: [.issues[] | {severity, type, origin}]
    }'
}

# Effective route table on a NIC
az network nic show-effective-route-table -g "$RG" -n "$NIC_NAME" --output table

# Effective NSG rules on a NIC
az network nic list-effective-nsg -g "$RG" -n "$NIC_NAME" --output json | \
  jq '[.effectiveNetworkSecurityGroups[].effectiveSecurityRules[]
    | select(.access=="Deny") | {name, priority, sourceAddressPrefix, destinationPortRange}]'
```

---

## Network Audit

```bash
# Rogue public IPs
az network public-ip list \
  --query "[?ipConfiguration==null].{Name:name, RG:resourceGroup, SKU:sku.name}" \
  --output table

# NSGs with allow-all inbound rules
az network nsg list --output json | \
  jq '[.[] | select(.securityRules[] | .access=="Allow" and .sourceAddressPrefix=="*" and .direction=="Inbound")
    | {name: .name, rg: .resourceGroup}]'

# Peerings not in Connected state
az network vnet peering list \
  --resource-group "$HUB_RG" \
  --vnet-name "vnet-hub-${REGION}" \
  --query "[?peeringState!='Connected'].{name:name, state:peeringState}" \
  --output table
```

---

## Cross-Cloud VPN (Azure to AWS)

```bash
# Create Azure VPN Gateway (already provisioned in hub GatewaySubnet)
# Create Local Network Gateway pointing at AWS VGW public IP
az network local-gateway create \
  --resource-group "$HUB_RG" \
  --name "lgw-aws-${REGION}" \
  --gateway-ip-address "$AWS_VGW_IP" \
  --address-prefixes "$AWS_CIDR" \
  --asn "$AWS_BGP_ASN" \
  --bgp-peering-address "$AWS_BGP_IP"

# Create IPSec connection
az network vpn-connection create \
  --name "conn-azure-to-aws" \
  --resource-group "$HUB_RG" \
  --vnet-gateway1 "vpngw-hub-${REGION}" \
  --local-gateway2 "lgw-aws-${REGION}" \
  --shared-key "$VPN_PSK" \
  --enable-bgp
```

---

## Examples

- "Provision a spoke VNet for tenant-53 at 10.20.0.0/16 and peer it to the hub"
- "Create private endpoints for the SQL and Key Vault resources in tenant-42"
- "Why can't the payments-api pod reach the database? Diagnose connectivity"
- "Audit all NSGs — flag any that allow inbound from 0.0.0.0/0"
- "Set up the private DNS zones for the new East Europe hub"

---

## Output Format

```json
{
  "operation": "provision|peer|private-endpoint|diagnose|audit",
  "resource": "string",
  "status": "success|failure",
  "connectivity": "Reachable|Unreachable|Unknown",
  "issues": [],
  "topology": { "vnets": 0, "peerings": 0, "private_endpoints": 0, "public_ips": 0 }
}
```
