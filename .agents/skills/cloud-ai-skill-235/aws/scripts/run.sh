#!/bin/bash
echo "Running cloud-ai-skill-235 on aws"
echo Analyzing costs
 aws ce get-cost-and-usage --time-period Start=2026-03-01,End=2026-03-31

# Example PR workflow
# git checkout -b fix/$skill
# git add .
# git commit -m "Automated changes by $skill"
# git push origin fix/$skill
