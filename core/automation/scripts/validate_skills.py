#!/usr/bin/env python3
"""
Script to validate all SKILL.md files against agentskills.io specification
"""

import os
import re
import glob
import yaml

def validate_skill_file(skill_path):
    """Validate a single SKILL.md file against specification"""
    errors = []
    warnings = []
    
    with open(skill_path, 'r') as f:
        content = f.read()
    
    # Extract frontmatter
    if not content.startswith('---'):
        errors.append("Missing YAML frontmatter delimiter")
        return errors, warnings
    
    try:
        frontmatter_end = content.find('---', 3)
        if frontmatter_end == -1:
            errors.append("Missing closing YAML frontmatter delimiter")
            return errors, warnings
        
        frontmatter_str = content[3:frontmatter_end].strip()
        frontmatter = yaml.safe_load(frontmatter_str)
        
        # Validate required fields
        if 'name' not in frontmatter:
            errors.append("Missing required 'name' field")
        else:
            name = frontmatter['name']
            # Validate name format
            if not re.match(r'^[a-z0-9]+(-[a-z0-9]+)*$', name):
                errors.append(f"Invalid name format: '{name}'. Must be lowercase letters, numbers, and hyphens only")
            if name.startswith('-') or name.endswith('-'):
                errors.append(f"Name cannot start or end with hyphen: '{name}'")
            if '--' in name:
                errors.append(f"Name cannot contain consecutive hyphens: '{name}'")
            if len(name) > 64:
                errors.append(f"Name too long (max 64 chars): '{name}'")
            
            # Check if name matches directory
            expected_dir = os.path.basename(os.path.dirname(skill_path))
            if name != expected_dir:
                warnings.append(f"Name '{name}' does not match directory name '{expected_dir}'")
        
        if 'description' not in frontmatter:
            errors.append("Missing required 'description' field")
        else:
            desc = frontmatter['description']
            if not isinstance(desc, str):
                errors.append("Description must be a string")
            elif len(desc) == 0:
                errors.append("Description cannot be empty")
            elif len(desc) > 1024:
                errors.append(f"Description too long (max 1024 chars): {len(desc)} chars")
        
        # Validate optional fields
        if 'license' in frontmatter and not isinstance(frontmatter['license'], str):
            errors.append("License must be a string")
        
        if 'compatibility' in frontmatter:
            comp = frontmatter['compatibility']
            if not isinstance(comp, str):
                errors.append("Compatibility must be a string")
            elif len(comp) > 500:
                errors.append(f"Compatibility too long (max 500 chars): {len(comp)} chars")
        
        if 'metadata' in frontmatter and not isinstance(frontmatter['metadata'], dict):
            errors.append("Metadata must be a dictionary")
        
        if 'allowed-tools' in frontmatter:
            tools = frontmatter['allowed-tools']
            if not isinstance(tools, str):
                errors.append("allowed-tools must be a space-delimited string")
            elif not re.match(r'^[a-zA-Z0-9_()]+( [a-zA-Z0-9_()]+)*$', tools):
                errors.append("allowed-tools must be space-delimited tool names")
        
    except yaml.YAMLError as e:
        errors.append(f"Invalid YAML frontmatter: {e}")
    
    return errors, warnings

def main():
    # Find all SKILL.md files
    skill_files = glob.glob('/Users/lloyd/github/antigravity/gitops-infra-core/operators/core/ai/skills/*/SKILL.md')
    
    total_errors = 0
    total_warnings = 0
    
    for skill_file in skill_files:
        errors, warnings = validate_skill_file(skill_file)
        
        if errors or warnings:
            skill_name = os.path.basename(os.path.dirname(skill_file))
            print(f"\n{skill_name}:")
            
            for error in errors:
                print(f"  ERROR: {error}")
                total_errors += 1
            
            for warning in warnings:
                print(f"  WARNING: {warning}")
                total_warnings += 1
    
    print(f"\nValidation complete:")
    print(f"  Files checked: {len(skill_files)}")
    print(f"  Errors: {total_errors}")
    print(f"  Warnings: {total_warnings}")
    
    if total_errors == 0:
        print("  ✅ All files are valid!")
    else:
        print("  ❌ Some files have errors that need to be fixed")

if __name__ == "__main__":
    main()
