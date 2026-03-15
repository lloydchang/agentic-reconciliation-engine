Name: kubectl-assistant
Purpose: Generate and explain kubectl commands for Kubernetes cluster operations.
Inputs: Natural language request, Cluster context, Resource type, Operation intent
Process: Parse user request, identify appropriate kubectl command pattern, generate safe executable commands with proper flags and selectors, explain command behavior and potential impacts.
Outputs: Executable kubectl command, Command explanation, Safety warnings, Alternative commands, Expected output description
Optional scripts: scripts/gen_kubectl_cmds.py
Optional manifests: manifests/example.yaml

