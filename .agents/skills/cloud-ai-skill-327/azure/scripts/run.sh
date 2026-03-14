#!/bin/bash
echo "Running cloud-ai-skill-327 on azure"
terraform init
 terraform plan -out=tfplan
 terraform apply tfplan

# Example PR workflow
# git checkout -b fix/$skill
# git add .
# git commit -m "Automated changes by $skill"
# git push origin fix/$skill
