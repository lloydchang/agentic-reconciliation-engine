--- 
name: node-scale-assistant 
description: Assist with scaling Kubernetes node pools and clusters. Triggers: requests to scale nodes, adjust autoscaling. 
tools: 
  - bash 
  - computer 
--- 

# Node Scale Assistant Skill 

Help scale node pools, adjust autoscaling settings, and manage cluster capacity. 

## Inputs 
Scaling request (e.g., "scale node pool to 5 nodes", "increase CPU capacity") 

## Process 
1. Analyze current cluster state 
2. Determine scaling action (manual or autoscaler adjustment) 
3. Generate commands or UI steps 
4. Validate capacity requirements 

## Outputs 
Scaling instructions or commands. 

## Examples 
- "Add 2 more nodes to the default pool" -> kubectl scale nodepool default --replicas=5 (for AKS/EKS) 
- "Enable cluster autoscaler" -> Commands to enable autoscaling 

## Output Format 
Action: Scale node pool 
Command: kubectl scale ... 
Explanation: This will add capacity for your workloads. 

