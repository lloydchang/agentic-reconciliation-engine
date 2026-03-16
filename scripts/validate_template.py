#!/usr/bin/env python3
"""
Template Validation - Check if template meets specifications
"""

import yaml
from pathlib import Path

def validate_template():
    """Validate the single template file"""
    template_file = Path(__file__).parent.parent / ".agents" / "SKILL_TEMPLATE.md"
    
    if not template_file.exists():
        print(f"❌ Template not found: {template_file}")
        return
    
    print(f"🔍 Validating template: {template_file}")
    
    with open(template_file, 'r') as f:
        content = f.read()
    
    # Check agentskills.io compliance
    agentskills_compliant = True
    agentskills_issues = []
    
    if not content.startswith('---'):
        agentskills_compliant = False
        agentskills_issues.append('Missing YAML frontmatter')
    else:
        try:
            frontmatter_end = content.find('---', 3)
            frontmatter_content = content[3:frontmatter_end]
            frontmatter_data = yaml.safe_load(frontmatter_content)
            
            required_fields = ['name', 'description', 'license', 'metadata', 'compatibility']
            for field in required_fields:
                if field not in frontmatter_data:
                    agentskills_compliant = False
                    agentskills_issues.append(f'Missing required field: {field}')
            
            if 'metadata' in frontmatter_data:
                metadata_required = ['author', 'version', 'category']
                for field in metadata_required:
                    if field not in frontmatter_data['metadata']:
                        agentskills_compliant = False
                        agentskills_issues.append(f'Missing metadata field: {field}')
            
            if 'allowed-tools' not in frontmatter_data:
                agentskills_compliant = False
                agentskills_issues.append('Missing allowed-tools field')
                
        except yaml.YAMLError as e:
            agentskills_compliant = False
            agentskills_issues.append(f'Invalid YAML frontmatter: {e}')
    
    # Check AGENTS.md compliance
    agents_md_compliant = True
    agents_md_issues = []
    
    required_sections = [
        '## Purpose', '## When to Use', '## Inputs', '## Process', '## Outputs',
        '## Environment', '## Dependencies', '## Scripts', '## Trigger Keywords',
        '## Human Gate Requirements', '## API Patterns', '## Parameter Schema',
        '## Return Schema', '## Error Handling'
    ]
    
    for section in required_sections:
        if section not in content:
            agents_md_compliant = False
            agents_md_issues.append(f'Missing required section: {section}')
    
    # Check features
    world_class_compliant = True
    world_class_issues = []
    
    world_class_indicators = ['', 'enterprise-grade', 'multi-cloud', 'AI-powered']
    found_indicators = sum(1 for indicator in world_class_indicators if indicator.lower() in content.lower())
    if found_indicators < 3:
        world_class_compliant = False
        world_class_issues.append(f'Insufficient indicators (found {found_indicators}/3)')
    
    # Check multi-cloud support
    multi_cloud_compliant = True
    multi_cloud_issues = []
    
    multi_cloud_terms = ['aws', 'azure', 'gcp', 'onprem', 'multi-cloud']
    found_cloud = sum(1 for term in multi_cloud_terms if term.lower() in content.lower())
    if found_cloud < 4:
        multi_cloud_compliant = False
        multi_cloud_issues.append(f'Insufficient multi-cloud support (found {found_cloud}/4)')
    
    # Check Python-first approach
    python_first_compliant = True
    python_first_issues = []
    
    if '```python' not in content:
        python_first_compliant = False
        python_first_issues.append('Missing Python code blocks')
    
    # Check API Patterns
    api_patterns_compliant = True
    api_patterns_issues = []
    
    api_patterns_section = content.find('## API Patterns')
    if api_patterns_section == -1:
        api_patterns_compliant = False
        api_patterns_issues.append('Missing API Patterns section')
    else:
        next_section = content.find('##', api_patterns_section + 3)
        if next_section == -1:
            next_section = len(content)
        
        api_content = content[api_patterns_section:next_section]
        
        api_type_indicators = [
            'Python Agent Scripts',
            'MCP Server Integration', 
            'Shell Commands',
            'Go Temporal Integration',
            'REST API',
            'GraphQL'
        ]
        
        found_api_types = 0
        for api_type in api_type_indicators:
            if api_type in api_content:
                found_api_types += 1
        
        if found_api_types < 3:
            api_patterns_compliant = False
            api_patterns_issues.append(f'Insufficient API pattern types (found {found_api_types}/3)')
    
    # Overall assessment
    overall_compliant = all([
        agentskills_compliant,
        agents_md_compliant,
        world_class_compliant,
        multi_cloud_compliant,
        python_first_compliant,
        api_patterns_compliant
    ])
    
    print(f"\n🎯 TEMPLATE VALIDATION RESULTS")
    print(f"=" * 40)
    print(f"📄 Template: SKILL_TEMPLATE.md")
    print(f"✅ Overall Compliant: {'YES' if overall_compliant else 'NO'}")
    
    print(f"\n📋 SPECIFICATION COMPLIANCE:")
    print(f"   agentskills.io: {'✅' if agentskills_compliant else '❌'}")
    print(f"   AGENTS.md: {'✅' if agents_md_compliant else '❌'}")
    print(f"   World-class: {'✅' if world_class_compliant else '❌'}")
    print(f"   Multi-cloud: {'✅' if multi_cloud_compliant else '❌'}")
    print(f"   Python-first: {'✅' if python_first_compliant else '❌'}")
    print(f"   API Patterns: {'✅' if api_patterns_compliant else '❌'}")
    
    if not overall_compliant:
        print(f"\n❌ ISSUES FOUND:")
        all_issues = (agentskills_issues + agents_md_issues + world_class_issues + 
                     multi_cloud_issues + python_first_issues + api_patterns_issues)
        for issue in all_issues[:5]:  # Show first 5 issues
            print(f"   • {issue}")
        
        if len(all_issues) > 5:
            print(f"   ... and {len(all_issues) - 5} more")
    else:
        print(f"\n🎉 TEMPLATE IS WORLD-CLASS COMPLIANT!")
        print(f"🌟 Follows both agentskills.io and AGENTS.md specifications!")
        print(f"🚀 Multi-cloud Python-first enterprise ready!")

if __name__ == "__main__":
    validate_template()
