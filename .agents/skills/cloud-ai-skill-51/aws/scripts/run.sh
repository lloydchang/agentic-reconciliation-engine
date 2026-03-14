#!/bin/bash
echo "Running cloud-ai-skill-51 on aws"
echo Generating manifests
 mkdir -p generated
 echo '# Kubernetes YAML' > generated/deploy.yaml

# Example PR workflow
# git checkout -b fix/$skill
# git add .
# git commit -m "Automated changes by $skill"
# git push origin fix/$skill
