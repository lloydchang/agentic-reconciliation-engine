#!/bin/bash
echo "Running cloud-ai-skill-319 on aws"
kubectl get roles --all-namespaces
 vault policy read default

# Example PR workflow
# git checkout -b fix/$skill
# git add .
# git commit -m "Automated changes by $skill"
# git push origin fix/$skill
