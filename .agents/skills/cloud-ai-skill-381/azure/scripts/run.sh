#!/bin/bash
echo "Running cloud-ai-skill-381 on azure"
git checkout -b fix/cloud-ai-skill-381
 git add .
 git commit -m 'Auto PR by cloud-ai-skill-381'
 git push origin fix/cloud-ai-skill-381

# Example PR workflow
# git checkout -b fix/$skill
# git add .
# git commit -m "Automated changes by $skill"
# git push origin fix/$skill
