#!/bin/bash
echo "Running cloud-ai-skill-387 on on-prem"
git checkout -b fix/cloud-ai-skill-387
 git add .
 git commit -m 'Auto PR by cloud-ai-skill-387'
 git push origin fix/cloud-ai-skill-387

# Example PR workflow
# git checkout -b fix/$skill
# git add .
# git commit -m "Automated changes by $skill"
# git push origin fix/$skill
