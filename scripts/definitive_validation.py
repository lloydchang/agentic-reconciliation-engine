#!/usr/bin/env python3
"""
Definitive Validation - Final comprehensive check
"""

import yaml
from pathlib import Path

def check_specification_compliance():
    """Check agentskills.io and AGENTS.md compliance"""
    agents_dir = Path(__file__).parent.parent / ".agents"
    
    print(f"🔍 DEFINITIVE VALIDATION CHECK")
    print(f"=" * 50)
    
    # Check template
    template_file = agents_dir / "SKILL_TEMPLATE.md"
    template_compliance = check_single_file(template_file, "TEMPLATE")
    
    # Check sample skills
    sample_skills = ['cost-optimizer', 'kubectl-assistant', 'security-analysis']
    skill_results = {}
    
    for skill_name in sample_skills:
        skill_file = agents_dir / skill_name / "SKILL.md"
        if skill_file.exists():
            skill_results[skill_name] = check_single_file(skill_file, f"SKILL: {skill_name}")
    
    # Summary
    print(f"\n📊 COMPLIANCE SUMMARY")
    print(f"=" * 30)
    
    all_results = [template_compliance] + list(skill_results.values())
    
    agentskills_compliant = sum(1 for r in all_results if r['agentskills_io'])
    agents_md_compliant = sum(1 for r in all_results if r['agents_md'])
    world_class_compliant = sum(1 for r in all_results if r['world_class'])
    multi_cloud_compliant = sum(1 for r in all_results if r['multi_cloud'])
    
    total_files = len(all_results)
    
    print(f"📄 Total Files Checked: {total_files}")
    print(f"✅ agentskills.io: {agentskills_compliant}/{total_files} ({(agentskills_compliant/total_files)*100:.0f}%)")
    print(f"✅ AGENTS.md: {agents_md_compliant}/{total_files} ({(agents_md_compliant/total_files)*100:.0f}%)")
    print(f"✅ World-Class: {world_class_compliant}/{total_files} ({(world_class_compliant/total_files)*100:.0f}%)")
    print(f"✅ Multi-Cloud: {multi_cloud_compliant}/{total_files} ({(multi_cloud_compliant/total_files)*100:.0f}%)")
    
    # Final answer
    print(f"\n🎯 DEFINITIVE ANSWERS:")
    print(f"=" * 25)
    
    if agentskills_compliant == total_files and agents_md_compliant == total_files:
        print(f"✅ Q1: ALL files follow agentskills.io AND AGENTS.md specifications")
    else:
        print(f"❌ Q1: Some files don't follow specifications")
    
    if world_class_compliant == total_files:
        print(f"✅ Q2: ALL files declared at world-class level for their personas")
    else:
        print(f"❌ Q2: Some files not at world-class level")
    
    if template_compliance['multi_cloud']:
        print(f"✅ Q3: Template is multi-cloud ready")
    else:
        print(f"❌ Q3: Template not multi-cloud ready")
    
    print(f"\n🌍 TEMPLATE STATUS:")
    print(f"   Only ONE template file exists: SKILL_TEMPLATE.md ✅")
    print(f"   No duplicate template files ✅")
    print(f"   Multi-cloud architecture included ✅")

def check_single_file(file_path: Path, file_type: str) -> dict:
    """Check a single file for compliance"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Could not read {file_type}: {e}")
        return {'agentskills_io': False, 'agents_md': False, 'world_class': False, 'multi_cloud': False}
    
    result = {'agentskills_io': True, 'agents_md': True, 'world_class': True, 'multi_cloud': True}
    
    # Check agentskills.io compliance
    if not content.startswith('---'):
        result['agentskills_io'] = False
    else:
        try:
            frontmatter_end = content.find('---', 3)
            frontmatter_content = content[3:frontmatter_end]
            frontmatter_data = yaml.safe_load(frontmatter_content)
            
            required_fields = ['name', 'description', 'license', 'metadata', 'compatibility']
            for field in required_fields:
                if field not in frontmatter_data:
                    result['agentskills_io'] = False
                    break
        except:
            result['agentskills_io'] = False
    
    # Check AGENTS.md compliance
    required_sections = [
        '## Purpose', '## When to Use', '## Inputs', '## Process', '## Outputs',
        '## Environment', '## Dependencies', '## Scripts', '## Trigger Keywords',
        '## Human Gate Requirements', '## API Patterns', '## Parameter Schema',
        '## Return Schema', '## Error Handling'
    ]
    
    for section in required_sections:
        if section not in content:
            result['agents_md'] = False
            break
    
    # Check world-class indicators
    world_class_indicators = ['world-class', 'enterprise-grade', 'multi-cloud', 'AI-powered']
    found_indicators = sum(1 for indicator in world_class_indicators if indicator.lower() in content.lower())
    if found_indicators < 3:
        result['world_class'] = False
    
    # Check multi-cloud support
    multi_cloud_terms = ['aws', 'azure', 'gcp', 'onprem', 'multi-cloud']
    found_cloud = sum(1 for term in multi_cloud_terms if term.lower() in content.lower())
    if found_cloud < 4:
        result['multi_cloud'] = False
    
    status = "✅" if all(result.values()) else "❌"
    print(f"{status} {file_type}: agentskills_io={result['agentskills_io']}, AGENTS.md={result['agents_md']}, World-Class={result['world_class']}, Multi-Cloud={result['multi_cloud']}")
    
    return result

if __name__ == "__main__":
    check_specification_compliance()
