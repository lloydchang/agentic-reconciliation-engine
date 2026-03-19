use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use anyhow::{Result, anyhow};
use std::fs;
use std::path::Path;
use chrono::Utc;
use uuid::Uuid;

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Skill {
    pub name: String,
    pub description: String,
    pub metadata: SkillMetadata,
    pub content: String,
    pub scripts: Vec<String>,
    pub references: Vec<String>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct SkillMetadata {
    pub author: String,
    pub version: String,
    pub category: String,
    pub risk_level: String,
    pub autonomy: String,
    pub layer: String,
    pub compatibility: String,
    pub allowed_tools: Vec<String>,
}

pub struct SkillEngine {
    skills: HashMap<String, Skill>,
    skills_directory: String,
}

impl SkillEngine {
    pub fn new(skills_directory: String) -> Self {
        Self {
            skills: HashMap::new(),
            skills_directory,
        }
    }

    pub async fn load_skills(&mut self) -> Result<()> {
        let skills_dir = Path::new(&self.skills_directory);
        
        if !skills_dir.exists() {
            return Err(anyhow!("Skills directory does not exist: {}", self.skills_directory));
        }

        let entries = fs::read_dir(skills_dir)?;
        
        for entry in entries {
            let entry = entry?;
            let path = entry.path();
            
            if path.is_dir() {
                if let Some(skill_name) = path.file_name().and_then(|n| n.to_str()) {
                    if let Ok(skill) = self.load_skill(skill_name).await {
                        self.skills.insert(skill_name.to_string(), skill);
                    }
                }
            }
        }
        
        tracing::info!("Loaded {} skills", self.skills.len());
        Ok(())
    }

    async fn load_skill(&self, skill_name: &str) -> Result<Skill> {
        let skill_dir = Path::new(&self.skills_directory).join(skill_name);
        let skill_file = skill_dir.join("SKILL.md");
        
        if !skill_file.exists() {
            return Err(anyhow!("SKILL.md not found for skill: {}", skill_name));
        }

        let content = fs::read_to_string(&skill_file)?;
        
        // Parse frontmatter and content
        let (metadata, body_content) = self.parse_skill_md(&content)?;
        
        // Load scripts and references
        let scripts = self.load_skill_files(&skill_dir.join("scripts")).unwrap_or_default();
        let references = self.load_skill_files(&skill_dir.join("references")).unwrap_or_default();

        Ok(Skill {
            name: skill_name.to_string(),
            description: metadata.description.clone(),
            metadata,
            content: body_content,
            scripts,
            references,
        })
    }

    fn parse_skill_md(&self, content: &str) -> Result<(SkillMetadata, String)> {
        let lines: Vec<&str> = content.lines().collect();
        
        if !lines.starts_with(&["---"]) {
            return Err(anyhow!("Invalid SKILL.md format - missing frontmatter"));
        }

        let mut frontmatter_end = None;
        for (i, line) in lines.iter().enumerate().skip(1) {
            if *line == "---" {
                frontmatter_end = Some(i);
                break;
            }
        }

        let frontmatter_end = frontmatter_end.ok_or_else(|| anyhow!("Frontmatter not closed"))?;
        let frontmatter_str = lines[1..frontmatter_end].join("\n");
        let body_content = lines[frontmatter_end + 1..].join("\n");

        let metadata: SkillMetadata = serde_yaml::from_str(&frontmatter_str)?;
        
        Ok((metadata, body_content))
    }

    fn load_skill_files(&self, dir: &Path) -> Result<Vec<String>> {
        if !dir.exists() {
            return Ok(vec![]);
        }

        let mut files = Vec::new();
        let entries = fs::read_dir(dir)?;

        for entry in entries {
            let entry = entry?;
            let path = entry.path();
            
            if path.is_file() {
                if let Some(content) = self.read_file_content(&path) {
                    files.push(content);
                }
            }
        }

        Ok(files)
    }

    fn read_file_content(&self, path: &Path) -> Option<String> {
        fs::read_to_string(path).ok()
    }

    pub fn find_skill_for_problem(&self, problem_description: &str) -> Vec<&Skill> {
        let problem_lower = problem_description.to_lowercase();
        let mut matching_skills = Vec::new();

        for skill in self.skills.values() {
            let description_lower = skill.description.to_lowercase();
            
            // Simple keyword matching for now
            if self.contains_keywords(&description_lower, &problem_lower) {
                matching_skills.push(skill);
            }
        }

        matching_skills
    }

    fn contains_keywords(&self, description: &str, problem: &str) -> bool {
        let keywords = vec![
            "cost", "optimize", "security", "certificate", "kubernetes", "scale",
            "troubleshoot", "backup", "monitor", "deploy", "incident", "alert"
        ];

        for keyword in keywords {
            if problem.contains(keyword) && description.contains(keyword) {
                return true;
            }
        }

        false
    }

    pub fn get_skill(&self, skill_name: &str) -> Option<&Skill> {
        self.skills.get(skill_name)
    }

    pub fn list_skills(&self) -> Vec<&String> {
        self.skills.keys().collect()
    }

    pub async fn execute_skill_plan(&self, skill_name: &str, input_data: &serde_json::Value) -> Result<Vec<String>> {
        let skill = self.get_skill(skill_name)
            .ok_or_else(|| anyhow!("Skill not found: {}", skill_name))?;

        // Generate execution plan based on skill content
        let plan = self.generate_execution_plan(skill, input_data).await?;
        
        Ok(plan)
    }

    async fn generate_execution_plan(&self, skill: &Skill, input_data: &serde_json::Value) -> Result<Vec<String>> {
        // This would integrate with Qwen for intelligent plan generation
        // For now, return a basic plan based on skill metadata
        let mut plan = Vec::new();

        plan.push(format!("Validate input parameters for skill: {}", skill.name));
        
        if skill.metadata.risk_level == "high" {
            plan.push("Perform risk assessment and require human approval".to_string());
        }
        
        plan.push(format!("Execute {} skill logic", skill.name));
        
        if skill.metadata.layer == "gitops" {
            plan.push("Create GitOps pull request for changes".to_string());
            plan.push("Wait for approval and merge".to_string());
        }
        
        plan.push("Verify results and update memory".to_string());

        Ok(plan)
    }

    pub fn assess_risk(&self, skill_name: &str) -> Result<String> {
        let skill = self.get_skill(skill_name)
            .ok_or_else(|| anyhow!("Skill not found: {}", skill_name))?;

        Ok(skill.metadata.risk_level.clone())
    }

    pub fn requires_human_gate(&self, skill_name: &str) -> Result<bool> {
        let skill = self.get_skill(skill_name)
            .ok_or_else(|| anyhow!("Skill not found: {}", skill_name))?;

        Ok(skill.metadata.autonomy != "fully_auto" || skill.metadata.risk_level == "high")
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[tokio::test]
    async fn test_skill_loading() {
        let mut engine = SkillEngine::new("/path/to/skills".to_string());
        
        // This would require actual skill files to test
        // For now, just test the structure
        assert_eq!(engine.skills.len(), 0);
    }

    #[test]
    fn test_skill_matching() {
        let engine = SkillEngine::new("/path/to/skills".to_string());
        
        // Test keyword matching
        assert!(engine.contains_keywords("optimize cloud costs", "cost"));
        assert!(engine.contains_keywords("security analysis", "security"));
        assert!(!engine.contains_keywords("deployment issue", "cost"));
    }
}
