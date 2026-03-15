#!/usr/bin/env python3
"""
Final Validation - Simple and accurate API pattern detection
"""

import os
import yaml
from pathlib import Path

class FinalSkillValidator:
    def __init__(self, agents_dir: str):
        self.agents_dir = Path(agents_dir)
        
    def get_all_skills(self) -> list:
        """Get all skill directories"""
        skills = []
        for item in self.agents_dir.iterdir():
            if item.is_dir() and item.name not in ['scripts', 'templates', '__pycache__']:
                skill_file = item / "SKILL.md"
                if skill_file.exists():
                    skills.append(skill_file)
        return sorted(skills)
    
    def validate_agentskills_io_compliance(self, skill_file: Path) -> dict:
        """Validate agentskills.io frontmatter compliance"""
        with open(skill_file, 'r') as f:
            content = f.read()
        
        result = {'compliant': True, 'issues': [], 'score': 100}
        
        # Check for YAML frontmatter
        if not content.startswith('---'):
            result['compliant'] = False
            result['issues'].append('Missing YAML frontmatter')
            result['score'] -= 30
            return result
        
        # Parse frontmatter
        try:
            frontmatter_end = content.find('---', 3)
            if frontmatter_end == -1:
                result['compliant'] = False
                result['issues'].append('Unclosed YAML frontmatter')
                result['score'] -= 20
                return result
            
            frontmatter_content = content[3:frontmatter_end]
            frontmatter_data = yaml.safe_load(frontmatter_content)
            
            # Check required fields
            required_fields = ['name', 'description', 'license', 'metadata', 'compatibility']
            for field in required_fields:
                if field not in frontmatter_data:
                    result['compliant'] = False
                    result['issues'].append(f'Missing required field: {field}')
                    result['score'] -= 10
            
            # Check metadata
            if 'metadata' in frontmatter_data:
                metadata_required = ['author', 'version', 'category']
                for field in metadata_required:
                    if field not in frontmatter_data['metadata']:
                        result['compliant'] = False
                        result['issues'].append(f'Missing metadata field: {field}')
                        result['score'] -= 5
            
            # Check allowed-tools
            if 'allowed-tools' not in frontmatter_data:
                result['compliant'] = False
                result['issues'].append('Missing allowed-tools field')
                result['score'] -= 10
            
        except yaml.YAMLError as e:
            result['compliant'] = False
            result['issues'].append(f'Invalid YAML frontmatter: {e}')
            result['score'] -= 25
        
        return result
    
    def validate_agents_md_compliance(self, skill_file: Path) -> dict:
        """Validate AGENTS.md section compliance"""
        with open(skill_file, 'r') as f:
            content = f.read()
        
        result = {'compliant': True, 'issues': [], 'score': 100}
        
        # Required sections
        required_sections = [
            '## Purpose', '## When to Use', '## Inputs', '## Process', '## Outputs',
            '## Environment', '## Dependencies', '## Scripts', '## Trigger Keywords',
            '## Human Gate Requirements', '## API Patterns', '## Parameter Schema',
            '## Return Schema', '## Error Handling'
        ]
        
        for section in required_sections:
            if section not in content:
                result['compliant'] = False
                result['issues'].append(f'Missing required section: {section}')
                result['score'] -= 7
        
        # Check for indicators
        world_class_indicators = ['', 'enterprise-grade', 'multi-cloud', 'AI-powered']
        found_indicators = sum(1 for indicator in world_class_indicators if indicator.lower() in content.lower())
        if found_indicators < 2:
            result['compliant'] = False
            result['issues'].append(f'Insufficient indicators (found {found_indicators}/2)')
            result['score'] -= 15
        
        return result
    
    def validate_python_first_approach(self, skill_file: Path) -> dict:
        """Validate Python-first approach"""
        with open(skill_file, 'r') as f:
            content = f.read()
        
        result = {'compliant': True, 'issues': [], 'score': 100}
        
        # Check for Python code blocks
        if '```python' not in content:
            result['compliant'] = False
            result['issues'].append('Missing Python code blocks')
            result['score'] -= 25
        
        # Check for multi-cloud support
        multi_cloud_terms = ['aws', 'azure', 'gcp', 'onprem', 'multi-cloud']
        found_cloud = sum(1 for term in multi_cloud_terms if term.lower() in content.lower())
        if found_cloud < 2:
            result['compliant'] = False
            result['issues'].append(f'Insufficient multi-cloud support (found {found_cloud}/2)')
            result['score'] -= 20
        
        return result
    
    def validate_world_class_level(self, skill_file: Path) -> dict:
        """Validate level declaration"""
        with open(skill_file, 'r') as f:
            content = f.read()
        
        result = {'compliant': True, 'issues': [], 'score': 100}
        
        # Check for phrases
        world_class_phrases = ['', 'enterprise-grade', 'multi-cloud', 'python-first', 'agent-executable']
        found_phrases = sum(1 for phrase in world_class_phrases if phrase.lower() in content.lower())
        if found_phrases < 3:
            result['compliant'] = False
            result['issues'].append(f'Insufficient phrases (found {found_phrases}/3)')
            result['score'] -= (3 - found_phrases) * 10
        
        # Check API Patterns section and count types - SIMPLIFIED LOGIC
        api_patterns_section = content.find('## API Patterns')
        if api_patterns_section == -1:
            result['compliant'] = False
            result['issues'].append('Missing API Patterns section')
            result['score'] -= 30
        else:
            # Extract API Patterns content
            next_section = content.find('##', api_patterns_section + 3)
            if next_section == -1:
                next_section = len(content)
            
            api_content = content[api_patterns_section:next_section]
            
            # Simple string matching for API pattern types
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
            
            # Require at least 3 different API pattern types
            if found_api_types < 3:
                result['compliant'] = False
                result['issues'].append(f'Insufficient API pattern types (found {found_api_types}/3)')
                result['score'] -= (3 - found_api_types) * 10
        
        return result
    
    def validate_single_skill(self, skill_file: Path) -> dict:
        """Validate a single skill file"""
        skill_name = skill_file.parent.name
        
        agentskills_result = self.validate_agentskills_io_compliance(skill_file)
        agents_md_result = self.validate_agents_md_compliance(skill_file)
        python_result = self.validate_python_first_approach(skill_file)
        world_class_result = self.validate_world_class_level(skill_file)
        
        overall_score = (
            agentskills_result['score'] * 0.25 +
            agents_md_result['score'] * 0.25 +
            python_result['score'] * 0.25 +
            world_class_result['score'] * 0.25
        )
        
        overall_compliant = all([
            agentskills_result['compliant'],
            agents_md_result['compliant'],
            python_result['compliant'],
            world_class_result['compliant']
        ])
        
        return {
            'skill_name': skill_name,
            'overall_compliant': overall_compliant,
            'overall_score': round(overall_score, 1),
            'agentskills_io': agentskills_result,
            'agents_md': agents_md_result,
            'python_first': python_result,
            'world_class': world_class_result,
            'all_issues': (agentskills_result['issues'] + 
                          agents_md_result['issues'] + 
                          python_result['issues'] + 
                          world_class_result['issues'])
        }
    
    def validate_all_skills(self) -> dict:
        """Validate all skills"""
        print(f"🔍 Starting FINAL comprehensive validation...")
        
        skills = self.get_all_skills()
        print(f"📊 Found {len(skills)} skills to validate")
        
        results = []
        compliant_count = 0
        total_score = 0
        
        for skill_file in skills:
            result = self.validate_single_skill(skill_file)
            results.append(result)
            
            if result['overall_compliant']:
                compliant_count += 1
                print(f"✅ {result['skill_name']}: {result['overall_score']}/100 - COMPLIANT")
            else:
                print(f"❌ {result['skill_name']}: {result['overall_score']}/100 - NON-COMPLIANT")
                # Show only the most critical issue
                if result['all_issues']:
                    print(f"   • {result['all_issues'][0]}")
            
            total_score += result['overall_score']
        
        average_score = total_score / len(skills) if skills else 0
        
        summary = {
            'total_skills': len(skills),
            'compliant_skills': compliant_count,
            'non_compliant_skills': len(skills) - compliant_count,
            'compliance_percentage': (compliant_count / len(skills)) * 100 if skills else 0,
            'average_score': round(average_score, 1),
            'results': results
        }
        
        return summary
    
    def print_summary(self, summary: dict):
        """Print validation summary"""
        print(f"\n🎯 FINAL COMPREHENSIVE VALIDATION RESULTS")
        print(f"=" * 60)
        print(f"📊 Total Skills: {summary['total_skills']}")
        print(f"✅ Compliant Skills: {summary['compliant_skills']}")
        print(f"❌ Non-Compliant Skills: {summary['non_compliant_skills']}")
        print(f"📈 Compliance Percentage: {summary['compliance_percentage']:.1f}%")
        print(f"⭐ Average Score: {summary['average_score']}/100")
        
        if summary['compliance_percentage'] == 100:
            print(f"\n🎉 ALL SKILLS ARE WORLD-CLASS COMPLIANT!")
            print(f"🌟 100% agentskills.io + AGENTS.md specification compliance!")
            print(f"🚀 Python-first multi-cloud enterprise ready!")
            print(f"💯 World-class level achieved across all skills!")
            print(f"🔥 Each SKILL.md follows both specifications perfectly!")
            print(f"⚡ All skills declared at level for their personas!")
        else:
            print(f"\n⚠️  {summary['non_compliant_skills']} skills need attention")
        
        # Detailed breakdown
        print(f"\n📋 SPECIFICATION COMPLIANCE BREAKDOWN:")
        
        agentskills_compliant = sum(1 for r in summary['results'] if r['agentskills_io']['compliant'])
        print(f"   agentskills.io: {agentskills_compliant}/{summary['total_skills']} ({(agentskills_compliant/summary['total_skills'])*100:.1f}%)")
        
        agents_md_compliant = sum(1 for r in summary['results'] if r['agents_md']['compliant'])
        print(f"   AGENTS.md: {agents_md_compliant}/{summary['total_skills']} ({(agents_md_compliant/summary['total_skills'])*100:.1f}%)")
        
        python_compliant = sum(1 for r in summary['results'] if r['python_first']['compliant'])
        print(f"   Python-first: {python_compliant}/{summary['total_skills']} ({(python_compliant/summary['total_skills'])*100:.1f}%)")
        
        world_class_compliant = sum(1 for r in summary['results'] if r['world_class']['compliant'])
        print(f"   World-class: {world_class_compliant}/{summary['total_skills']} ({(world_class_compliant/summary['total_skills'])*100:.1f}%)")

def main():
    """Main execution"""
    agents_dir = Path(__file__).parent.parent / ".agents"
    
    if not agents_dir.exists():
        print(f"❌ Agents directory not found: {agents_dir}")
        return
    
    validator = FinalSkillValidator(agents_dir)
    summary = validator.validate_all_skills()
    validator.print_summary(summary)

if __name__ == "__main__":
    main()
