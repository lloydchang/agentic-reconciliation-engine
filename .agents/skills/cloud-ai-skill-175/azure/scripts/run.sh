#!/bin/bash
echo "Running cloud-ai-skill-175 on azure"
kubectl create rolebinding example --clusterrole=edit --user=dev@example.com

# Example PR workflow
# git checkout -b fix/$skill
# git add .
# git commit -m "Automated changes by $skill"
# git push origin fix/$skill
