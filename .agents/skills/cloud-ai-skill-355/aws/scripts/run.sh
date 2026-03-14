#!/bin/bash
echo "Running cloud-ai-skill-355 on aws"
kubectl apply -f compositions/

# Example PR workflow
# git checkout -b fix/$skill
# git add .
# git commit -m "Automated changes by $skill"
# git push origin fix/$skill
