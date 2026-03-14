#!/bin/bash
echo "Running cloud-ai-skill-81 on azure"
helm upgrade --install mychart ./charts/mychart

# Example PR workflow
# git checkout -b fix/$skill
# git add .
# git commit -m "Automated changes by $skill"
# git push origin fix/$skill
