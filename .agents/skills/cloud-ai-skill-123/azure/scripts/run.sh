#!/bin/bash
echo "Running cloud-ai-skill-123 on azure"
kubectl diff -f generated/deploy.yaml

# Example PR workflow
# git checkout -b fix/$skill
# git add .
# git commit -m "Automated changes by $skill"
# git push origin fix/$skill
