#!/bin/bash
echo "Running cloud-ai-skill-115 on aws"
helm upgrade --install mychart ./charts/mychart

# Example PR workflow
# git checkout -b fix/$skill
# git add .
# git commit -m "Automated changes by $skill"
# git push origin fix/$skill
