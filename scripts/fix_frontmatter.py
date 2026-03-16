#!/usr/bin/env python3
"""
Script to fix YAML frontmatter issues in SKILL.md files
"""

import os
import re
import glob

def fix_frontmatter(skill_path):
    """Fix YAML frontmatter in a SKILL.md file"""
    with open(skill_path, 'r') as f:
        content = f.read()
    
    # Find the frontmatter section
    if not content.startswith('---'):
        print(f"Skipping {skill_path} - no frontmatter start")
        return
    
    # Find the end of frontmatter
    lines = content.split('\n')
    end_idx = -1
    
    for i in range(1, len(lines)):
        if lines[i].strip() == '---' and not lines[i-1].strip().startswith('compatibility'):
            end_idx = i
            break
    
    if end_idx == -1:
        # Find where frontmatter should end (before first non-YAML line)
        for i in range(1, len(lines)):
            line = lines[i].strip()
            if line and not line.startswith('name:') and not line.startswith('description:') and not line.startswith('license:') and not line.startswith('metadata:') and not line.startswith('compatibility:') and not line.startswith('allowed-tools:'):
                end_idx = i
                break
        
        if end_idx == -1:
            end_idx = len(lines) - 1
    
    # Reconstruct content with proper frontmatter
    frontmatter_lines = lines[:end_idx]
    body_lines = lines[end_idx:]
    
    # Ensure allowed-tools is present before closing
    if not any('allowed-tools:' in line for line in frontmatter_lines):
        frontmatter_lines.append('allowed-tools: Bash Read Write Grep')
    
    # Ensure proper closing
    if frontmatter_lines[-1].strip() != '---':
        frontmatter_lines.append('---')
    
    # Remove any leading empty lines from body
    while body_lines and not body_lines[0].strip():
        body_lines = body_lines[1:]
    
    # Reconstruct content
    fixed_content = '\n'.join(frontmatter_lines + [''] + body_lines)
    
    # Save fixed content
    with open(skill_path, 'w') as f:
        f.write(fixed_content)
    
    print(f"Fixed {skill_path}")

def main():
    # Find all SKILL.md files
    skill_files = glob.glob('/Users/lloyd/github/antigravity/gitops-infra-control-plane/.agents/*/SKILL.md')
    
    for skill_file in skill_files:
        fix_frontmatter(skill_file)
    
    print(f"Fixed {len(skill_files)} skill files")

if __name__ == "__main__":
    main()
