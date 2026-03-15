--- 
name: kubectl-assistant 
description: Translate user requests into safe kubectl commands. Triggers: user asks how to perform Kubernetes operations. 
tools: 
  - bash 
  - computer 
--- 

# Kubectl Assistant Skill 

Generate safe kubectl commands based on natural language requests. 

## Inputs 
Natural language description of desired kubectl operation. 

## Process 
1. Parse the request 
2. Identify the kubectl command and flags 
3. Ensure safety (no destructive commands without confirmation) 
4. Generate the command with explanation 

## Outputs 
kubectl command string with usage explanation. 

## Examples 
- "How do I check pod status in namespace production?" -> kubectl get pods -n production 
- "Restart the web deployment" -> kubectl rollout restart deployment web 
- "Show logs for pod mypod" -> kubectl logs mypod 

## Output Format 
Command: kubectl get pods -n default 
Explanation: This command lists all pods in the default namespace. 

