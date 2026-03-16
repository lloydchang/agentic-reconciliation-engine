#!/usr/bin/env python3
"""
Accurate Validation - Fix the API pattern detection issue
"""

import yaml
from pathlib import Path

def validate_single_file_accurate(file_path: Path, file_name: str) -> dict:
    """Validate a single file with accurate API pattern detection"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
    except Exception as e:
        return {
            'file_name': file_name,
            'status': 'ERROR',
            'error': f"Could not read file: {e}",
            'agentskills_io': False,
            'agents_md': False,
            'world_class': False,
            'multi_cloud': False,
            'issues': []
        }
    
    result = {
        'file_name': file_name,
        'status': 'CHECKED',
        'agentskills_io': True,
        'agents_md': True,
        'world_class': True,
        'multi_cloud': True,
        'issues': []
    }
    
    # Check agentskills.io compliance
    if not content.startswith('---'):
        result['agentskills_io'] = False
        result['issues'].append('Missing YAML frontmatter (---)')
    else:
        try:
            frontmatter_end = content.find('---', 3)
            if frontmatter_end == -1:
                result['agentskills_io'] = False
                result['issues'].append('Unclosed YAML frontmatter')
            else:
                frontmatter_content = content[3:frontmatter_end]
                frontmatter_data = yaml.safe_load(frontmatter_content)
                
                # Check required fields
                required_fields = ['name', 'description', 'license', 'metadata', 'compatibility']
                for field in required_fields:
                    if field not in frontmatter_data:
                        result['agentskills_io'] = False
                        result['issues'].append(f'Missing required field: {field}')
                
                # Check metadata
                if 'metadata' in frontmatter_data:
                    metadata_required = ['author', 'version', 'category']
                    for field in metadata_required:
                        if field not in frontmatter_data['metadata']:
                            result['agentskills_io'] = False
                            result['issues'].append(f'Missing metadata field: {field}')
                else:
                    result['agentskills_io'] = False
                    result['issues'].append('Missing metadata section')
                
                # Check allowed-tools
                if 'allowed-tools' not in frontmatter_data:
                    result['agentskills_io'] = False
                    result['issues'].append('Missing allowed-tools field')
                
        except yaml.YAMLError as e:
            result['agentskills_io'] = False
            result['issues'].append(f'Invalid YAML frontmatter: {e}')
    
    # Check AGENTS.md compliance
    required_sections = [
        '## Purpose', '## When to Use', '## Inputs', '## Process', '## Outputs',
        '## Environment', '## Dependencies', '## Scripts', '## Trigger Keywords',
        '## Human Gate Requirements', '## API Patterns', '## Parameter Schema',
        '## Return Schema', '## Error Handling'
    ]
    
    missing_sections = []
    for section in required_sections:
        if section not in content:
            missing_sections.append(section)
    
    if missing_sections:
        result['agents_md'] = False
        result['issues'].append(f'Missing sections: {", ".join(missing_sections)}')
    
    # Check indicators
    world_class_indicators = ['', 'enterprise-grade', 'multi-cloud', 'AI-powered']
    found_indicators = sum(1 for indicator in world_class_indicators if indicator.lower() in content.lower())
    if found_indicators < 3:
        result['world_class'] = False
        result['issues'].append(f'Insufficient indicators (found {found_indicators}/3)')
    
    # Check multi-cloud support
    multi_cloud_terms = ['aws', 'azure', 'gcp', 'onprem', 'multi-cloud']
    found_cloud = sum(1 for term in multi_cloud_terms if term.lower() in content.lower())
    if found_cloud < 4:
        result['multi_cloud'] = False
        result['issues'].append(f'Insufficient multi-cloud support (found {found_cloud}/4)')
    
    # Check Python code blocks
    if '```python' not in content:
        result['world_class'] = False
        result['issues'].append('Missing Python code blocks')
    
    # ACCURATE API Patterns section check
    api_patterns_section = content.find('## API Patterns')
    if api_patterns_section == -1:
        result['world_class'] = False
        result['issues'].append('Missing API Patterns section')
    else:
        next_section = content.find('##', api_patterns_section + 3)
        if next_section == -1:
            next_section = len(content)
        
        api_content = content[api_patterns_section:next_section]
        
        # ACCURATE API pattern detection - check for exact patterns
        api_patterns_found = []
        
        # Check for Python Agent Scripts
        if '### Python Agent Scripts' in api_content or 'Python Agent Scripts' in api_content:
            api_patterns_found.append('Python Agent Scripts')
        
        # Check for MCP Server Integration
        if '### MCP Server Integration' in api_content or 'MCP Server Integration' in api_content:
            api_patterns_found.append('MCP Server Integration')
        
        # Check for Shell Commands
        if '### Shell Commands' in api_content or 'Shell Commands' in api_content:
            api_patterns_found.append('Shell Commands')
        
        # Check for Go Temporal Integration
        if '### Go Temporal Integration' in api_content or 'Go Temporal Integration' in api_content:
            api_patterns_found.append('Go Temporal Integration')
        
        # Check for REST API Pattern
        if '### REST API' in api_content or 'REST API' in api_content:
            api_patterns_found.append('REST API Pattern')
        
        # Check for GraphQL Integration
        if '### GraphQL' in api_content or 'GraphQL' in api_content:
            api_patterns_found.append('GraphQL Integration')
        
        if len(api_patterns_found) < 3:
            result['world_class'] = False
            result['issues'].append(f'Insufficient API pattern types (found {len(api_patterns_found)}/3): {", ".join(api_patterns_found)}')
    
    return result

def main():
    """Check each file with accurate validation"""
    agents_dir = Path(__file__).parent.parent / ".agents"
    
    print(f"🔍 ACCURATE INDIVIDUAL VALIDATION")
    print(f"=" * 50)
    print(f"Checking each file with corrected API pattern detection...")
    
    # Get all skill directories
    skill_files = []
    for item in agents_dir.iterdir():
        if item.is_dir() and item.name not in ['scripts', 'templates', '__pycache__']:
            skill_file = item / "SKILL.md"
            if skill_file.exists():
                skill_files.append(skill_file)
    
    # Sort files for consistent order
    skill_files = sorted(skill_files)
    
    # Add template file
    template_file = agents_dir / "SKILL_TEMPLATE.md"
    if template_file.exists():
        skill_files.insert(0, template_file)  # Check template first
    
    print(f"📊 Total files to check: {len(skill_files)}")
    print(f"")
    
    # Validate each file
    results = []
    compliant_count = 0
    total_count = len(skill_files)
    
    for i, file_path in enumerate(skill_files, 1):
        if file_path.name == "SKILL_TEMPLATE.md":
            file_name = "TEMPLATE"
        else:
            file_name = f"SKILL: {file_path.parent.name}"
        
        result = validate_single_file_accurate(file_path, file_name)
        results.append(result)
        
        # Print status
        status_icon = "✅" if all([result['agentskills_io'], result['agents_md'], result['world_class'], result['multi_cloud']]) else "❌"
        print(f"{i:2d}. {status_icon} {file_name}")
        
        if all([result['agentskills_io'], result['agents_md'], result['world_class'], result['multi_cloud']]):
            compliant_count += 1
        else:
            # Show issues for non-compliant files
            for issue in result['issues'][:2]:  # Show first 2 issues
                print(f"     • {issue}")
    
    # Summary
    print(f"\n🎯 ACCURATE VALIDATION SUMMARY")
    print(f"=" * 40)
    print(f"📊 Total Files Checked: {total_count}")
    print(f"✅ Fully Compliant: {compliant_count}")
    print(f"❌ Not Compliant: {total_count - compliant_count}")
    print(f"📈 Compliance Rate: {(compliant_count/total_count)*100:.1f}%")
    
    # Detailed breakdown
    agentskills_compliant = sum(1 for r in results if r['agentskills_io'])
    agents_md_compliant = sum(1 for r in results if r['agents_md'])
    world_class_compliant = sum(1 for r in results if r['world_class'])
    multi_cloud_compliant = sum(1 for r in results if r['multi_cloud'])
    
    print(f"\n📋 SPECIFICATION BREAKDOWN:")
    print(f"   agentskills.io: {agentskills_compliant}/{total_count} ({(agentskills_compliant/total_count)*100:.1f}%)")
    print(f"   AGENTS.md: {agents_md_compliant}/{total_count} ({(agents_md_compliant/total_count)*100:.1f}%)")
    print(f"   World-Class: {world_class_compliant}/{total_count} ({(world_class_compliant/total_count)*100:.1f}%)")
    print(f"   Multi-Cloud: {multi_cloud_compliant}/{total_count} ({(multi_cloud_compliant/total_count)*100:.1f}%)")
    
    # Final answer
    print(f"\n🎯 DEFINITIVE ANSWERS:")
    print(f"=" * 25)
    
    if agentskills_compliant == total_count and agents_md_compliant == total_count:
        print(f"✅ Q1: ALL files follow agentskills.io AND AGENTS.md specifications")
    else:
        print(f"❌ Q1: Specification compliance issues found")
    
    if world_class_compliant == total_count:
        print(f"✅ Q2: ALL files declared at level for their personas")
    else:
        print(f"❌ Q2: {total_count - world_class_compliant} files not at level")
    
    # Show sample of API patterns found
    sample_result = results[0] if results else None
    if sample_result and 'API pattern types' in str(sample_result.get('issues', [])):
        print(f"\n🔍 API Pattern Detection Sample:")
        print(f"   Checking: {sample_result['file_name']}")
        # Let's manually check one file to show what's actually there
        sample_file = skill_files[0]
        with open(sample_file, 'r') as f:
            content = f.read()
        
        api_patterns_section = content.find('## API Patterns')
        if api_patterns_section != -1:
            next_section = content.find('##', api_patterns_section + 3)
            if next_section == -1:
                next_section = len(content)
            
            api_content = content[api_patterns_section:api_patterns_section + 500]
            print(f"   API Patterns section preview:")
            print(f"   {api_content[:200]}...")

if __name__ == "__main__":
    main()
