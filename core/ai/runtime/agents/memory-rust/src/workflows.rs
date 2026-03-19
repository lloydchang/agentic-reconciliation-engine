use serde::{Deserialize, Serialize};
use anyhow::{Result, anyhow};
use std::collections::HashMap;
use chrono::{DateTime, Utc};
use uuid::Uuid;
use crate::skills::SkillEngine;

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct WorkflowDefinition {
    pub id: String,
    pub name: String,
    pub description: String,
    pub skill_name: String,
    pub steps: Vec<WorkflowStep>,
    pub risk_level: String,
    pub human_gate_required: bool,
    pub created_at: DateTime<Utc>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct WorkflowStep {
    pub id: String,
    pub name: String,
    pub step_type: StepType,
    pub parameters: serde_json::Value,
    pub dependencies: Vec<String>,
    pub timeout_seconds: u64,
    pub retry_policy: RetryPolicy,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
#[serde(tag = "type")]
pub enum StepType {
    SkillExecution {
        skill_name: String,
        input_mapping: HashMap<String, String>,
    },
    GitOpsOperation {
        operation: String,
        target_path: String,
        validation_required: bool,
    },
    HumanApproval {
        message: String,
        approvers: Vec<String>,
        timeout_minutes: u64,
    },
    MemoryOperation {
        operation: String,
        query: Option<String>,
        data: Option<serde_json::Value>,
    },
    LLMAnalysis {
        prompt_template: String,
        context_sources: Vec<String>,
    },
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct RetryPolicy {
    pub max_attempts: u32,
    pub backoff_seconds: u64,
    pub multiplier: f32,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct WorkflowExecution {
    pub id: String,
    pub workflow_id: String,
    pub status: ExecutionStatus,
    pub started_at: DateTime<Utc>,
    pub completed_at: Option<DateTime<Utc>>,
    pub current_step: Option<String>,
    pub step_results: HashMap<String, StepResult>,
    pub error_message: Option<String>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
#[serde(tag = "status")]
pub enum ExecutionStatus {
    Pending,
    Running,
    Completed,
    Failed,
    Cancelled,
    WaitingForApproval,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct StepResult {
    pub step_id: String,
    pub status: ExecutionStatus,
    pub output: Option<serde_json::Value>,
    pub error: Option<String>,
    pub started_at: DateTime<Utc>,
    pub completed_at: Option<DateTime<Utc>>,
    pub attempt_count: u32,
}

pub struct WorkflowEngine {
    skill_engine: SkillEngine,
    workflows: HashMap<String, WorkflowDefinition>,
    executions: HashMap<String, WorkflowExecution>,
}

impl WorkflowEngine {
    pub fn new(skill_engine: SkillEngine) -> Self {
        Self {
            skill_engine,
            workflows: HashMap::new(),
            executions: HashMap::new(),
        }
    }

    pub async fn initialize_workflows(&mut self) -> Result<()> {
        // Load predefined workflow templates
        self.register_cost_optimization_workflow().await?;
        self.register_security_analysis_workflow().await?;
        self.register_troubleshooting_workflow().await?;
        self.register_certificate_rotation_workflow().await?;
        
        tracing::info!("Initialized {} workflow templates", self.workflows.len());
        Ok(())
    }

    async fn register_cost_optimization_workflow(&mut self) -> Result<()> {
        let workflow = WorkflowDefinition {
            id: "cost-optimization-v1".to_string(),
            name: "Cost Optimization Workflow".to_string(),
            description: "Analyze cloud costs and implement optimization measures".to_string(),
            skill_name: "optimize-costs".to_string(),
            steps: vec![
                WorkflowStep {
                    id: "analyze-costs".to_string(),
                    name: "Analyze current cost patterns".to_string(),
                    step_type: StepType::LLMAnalysis {
                        prompt_template: "Analyze cloud cost data and identify optimization opportunities: {input_data}".to_string(),
                        context_sources: vec!["historical_costs".to_string(), "resource_usage".to_string()],
                    },
                    parameters: serde_json::json!({}),
                    dependencies: vec![],
                    timeout_seconds: 300,
                    retry_policy: RetryPolicy {
                        max_attempts: 3,
                        backoff_seconds: 30,
                        multiplier: 2.0,
                    },
                },
                WorkflowStep {
                    id: "generate-plan".to_string(),
                    name: "Generate optimization plan".to_string(),
                    step_type: StepType::SkillExecution {
                        skill_name: "optimize-costs".to_string(),
                        input_mapping: HashMap::from([
                            ("operation".to_string(), "analyze".to_string()),
                            ("cloud_provider".to_string(), "all".to_string()),
                        ]),
                    },
                    parameters: serde_json::json!({}),
                    dependencies: vec!["analyze-costs".to_string()],
                    timeout_seconds: 600,
                    retry_policy: RetryPolicy {
                        max_attempts: 2,
                        backoff_seconds: 60,
                        multiplier: 1.5,
                    },
                },
                WorkflowStep {
                    id: "human-approval".to_string(),
                    name: "Request human approval for changes".to_string(),
                    step_type: StepType::HumanApproval {
                        message: "Cost optimization changes require approval".to_string(),
                        approvers: vec!["platform-team".to_string()],
                        timeout_minutes: 60,
                    },
                    parameters: serde_json::json!({}),
                    dependencies: vec!["generate-plan".to_string()],
                    timeout_seconds: 3600,
                    retry_policy: RetryPolicy {
                        max_attempts: 1,
                        backoff_seconds: 0,
                        multiplier: 1.0,
                    },
                },
                WorkflowStep {
                    id: "apply-changes".to_string(),
                    name: "Apply approved changes via GitOps".to_string(),
                    step_type: StepType::GitOpsOperation {
                        operation: "apply".to_string(),
                        target_path: "/infrastructure/cost-optimizations".to_string(),
                        validation_required: true,
                    },
                    parameters: serde_json::json!({}),
                    dependencies: vec!["human-approval".to_string()],
                    timeout_seconds: 900,
                    retry_policy: RetryPolicy {
                        max_attempts: 3,
                        backoff_seconds: 120,
                        multiplier: 2.0,
                    },
                },
            ],
            risk_level: "medium".to_string(),
            human_gate_required: true,
            created_at: Utc::now(),
        };

        self.workflows.insert("cost-optimization".to_string(), workflow);
        Ok(())
    }

    async fn register_security_analysis_workflow(&mut self) -> Result<()> {
        let workflow = WorkflowDefinition {
            id: "security-analysis-v1".to_string(),
            name: "Security Analysis Workflow".to_string(),
            description: "Perform comprehensive security analysis and remediation".to_string(),
            skill_name: "analyze-security".to_string(),
            steps: vec![
                WorkflowStep {
                    id: "security-scan".to_string(),
                    name: "Execute security scanning".to_string(),
                    step_type: StepType::SkillExecution {
                        skill_name: "analyze-security".to_string(),
                        input_mapping: HashMap::from([
                            ("operation".to_string(), "scan".to_string()),
                            ("scope".to_string(), "cluster".to_string()),
                        ]),
                    },
                    parameters: serde_json::json!({}),
                    dependencies: vec![],
                    timeout_seconds: 1200,
                    retry_policy: RetryPolicy {
                        max_attempts: 2,
                        backoff_seconds: 300,
                        multiplier: 2.0,
                    },
                },
                WorkflowStep {
                    id: "analyze-findings".to_string(),
                    name: "Analyze security findings".to_string(),
                    step_type: StepType::LLMAnalysis {
                        prompt_template: "Analyze security scan results and prioritize remediation: {findings}".to_string(),
                        context_sources: vec!["security_policies".to_string(), "compliance_requirements".to_string()],
                    },
                    parameters: serde_json::json!({}),
                    dependencies: vec!["security-scan".to_string()],
                    timeout_seconds: 600,
                    retry_policy: RetryPolicy {
                        max_attempts: 3,
                        backoff_seconds: 60,
                        multiplier: 1.5,
                    },
                },
                WorkflowStep {
                    id: "apply-fixes".to_string(),
                    name: "Apply security fixes".to_string(),
                    step_type: StepType::GitOpsOperation {
                        operation: "apply".to_string(),
                        target_path: "/security/remediations".to_string(),
                        validation_required: true,
                    },
                    parameters: serde_json::json!({}),
                    dependencies: vec!["analyze-findings".to_string()],
                    timeout_seconds: 1800,
                    retry_policy: RetryPolicy {
                        max_attempts: 3,
                        backoff_seconds: 300,
                        multiplier: 2.0,
                    },
                },
            ],
            risk_level: "high".to_string(),
            human_gate_required: true,
            created_at: Utc::now(),
        };

        self.workflows.insert("security-analysis".to_string(), workflow);
        Ok(())
    }

    async fn register_troubleshooting_workflow(&mut self) -> Result<()> {
        let workflow = WorkflowDefinition {
            id: "troubleshooting-v1".to_string(),
            name: "Kubernetes Troubleshooting Workflow".to_string(),
            description: "Diagnose and resolve Kubernetes cluster issues".to_string(),
            skill_name: "troubleshoot-kubernetes".to_string(),
            steps: vec![
                WorkflowStep {
                    id: "diagnose-issue".to_string(),
                    name: "Diagnose the issue".to_string(),
                    step_type: StepType::SkillExecution {
                        skill_name: "troubleshoot-kubernetes".to_string(),
                        input_mapping: HashMap::from([
                            ("operation".to_string(), "diagnose".to_string()),
                            ("component".to_string(), "{component}".to_string()),
                        ]),
                    },
                    parameters: serde_json::json!({}),
                    dependencies: vec![],
                    timeout_seconds: 600,
                    retry_policy: RetryPolicy {
                        max_attempts: 3,
                        backoff_seconds: 60,
                        multiplier: 1.5,
                    },
                },
                WorkflowStep {
                    id: "apply-remediation".to_string(),
                    name: "Apply remediation steps".to_string(),
                    step_type: StepType::GitOpsOperation {
                        operation: "apply".to_string(),
                        target_path: "/cluster/remediations".to_string(),
                        validation_required: false,
                    },
                    parameters: serde_json::json!({}),
                    dependencies: vec!["diagnose-issue".to_string()],
                    timeout_seconds: 900,
                    retry_policy: RetryPolicy {
                        max_attempts: 2,
                        backoff_seconds: 120,
                        multiplier: 2.0,
                    },
                },
            ],
            risk_level: "low".to_string(),
            human_gate_required: false,
            created_at: Utc::now(),
        };

        self.workflows.insert("troubleshooting".to_string(), workflow);
        Ok(())
    }

    async fn register_certificate_rotation_workflow(&mut self) -> Result<()> {
        let workflow = WorkflowDefinition {
            id: "cert-rotation-v1".to_string(),
            name: "Certificate Rotation Workflow".to_string(),
            description: "Rotate TLS certificates with minimal downtime".to_string(),
            skill_name: "manage-certificates".to_string(),
            steps: vec![
                WorkflowStep {
                    id: "validate-rotation".to_string(),
                    name: "Validate rotation requirements".to_string(),
                    step_type: StepType::SkillExecution {
                        skill_name: "manage-certificates".to_string(),
                        input_mapping: HashMap::from([
                            ("operation".to_string(), "validate".to_string()),
                            ("certificate".to_string(), "{certificate_name}".to_string()),
                        ]),
                    },
                    parameters: serde_json::json!({}),
                    dependencies: vec![],
                    timeout_seconds: 300,
                    retry_policy: RetryPolicy {
                        max_attempts: 3,
                        backoff_seconds: 30,
                        multiplier: 1.5,
                    },
                },
                WorkflowStep {
                    id: "backup-current".to_string(),
                    name: "Backup current certificates".to_string(),
                    step_type: StepType::MemoryOperation {
                        operation: "backup".to_string(),
                        query: None,
                        data: Some(serde_json::json!({"type": "certificates", "timestamp": Utc::now()})),
                    },
                    parameters: serde_json::json!({}),
                    dependencies: vec!["validate-rotation".to_string()],
                    timeout_seconds: 300,
                    retry_policy: RetryPolicy {
                        max_attempts: 2,
                        backoff_seconds: 60,
                        multiplier: 2.0,
                    },
                },
                WorkflowStep {
                    id: "rotate-certificates".to_string(),
                    name: "Rotate certificates".to_string(),
                    step_type: StepType::GitOpsOperation {
                        operation: "apply".to_string(),
                        target_path: "/certificates".to_string(),
                        validation_required: true,
                    },
                    parameters: serde_json::json!({}),
                    dependencies: vec!["backup-current".to_string()],
                    timeout_seconds: 1200,
                    retry_policy: RetryPolicy {
                        max_attempts: 2,
                        backoff_seconds: 300,
                        multiplier: 2.0,
                    },
                },
                WorkflowStep {
                    id: "verify-rotation".to_string(),
                    name: "Verify certificate rotation".to_string(),
                    step_type: StepType::SkillExecution {
                        skill_name: "manage-certificates".to_string(),
                        input_mapping: HashMap::from([
                            ("operation".to_string(), "verify".to_string()),
                            ("certificate".to_string(), "{certificate_name}".to_string()),
                        ]),
                    },
                    parameters: serde_json::json!({}),
                    dependencies: vec!["rotate-certificates".to_string()],
                    timeout_seconds: 600,
                    retry_policy: RetryPolicy {
                        max_attempts: 3,
                        backoff_seconds: 60,
                        multiplier: 1.5,
                    },
                },
            ],
            risk_level: "high".to_string(),
            human_gate_required: true,
            created_at: Utc::now(),
        };

        self.workflows.insert("certificate-rotation".to_string(), workflow);
        Ok(())
    }

    pub async fn execute_workflow(&mut self, workflow_name: &str, input_data: serde_json::Value) -> Result<String> {
        let workflow = self.workflows.get(workflow_name)
            .ok_or_else(|| anyhow!("Workflow not found: {}", workflow_name))?;

        let execution_id = Uuid::new_v4().to_string();
        let execution = WorkflowExecution {
            id: execution_id.clone(),
            workflow_id: workflow.id.clone(),
            status: ExecutionStatus::Pending,
            started_at: Utc::now(),
            completed_at: None,
            current_step: None,
            step_results: HashMap::new(),
            error_message: None,
        };

        self.executions.insert(execution_id.clone(), execution);
        
        // Start workflow execution (in a real implementation, this would be async)
        tracing::info!("Started workflow execution: {}", execution_id);
        
        Ok(execution_id)
    }

    pub fn get_workflow_execution(&self, execution_id: &str) -> Option<&WorkflowExecution> {
        self.executions.get(execution_id)
    }

    pub fn list_available_workflows(&self) -> Vec<&String> {
        self.workflows.keys().collect()
    }

    pub fn get_workflow_definition(&self, workflow_name: &str) -> Option<&WorkflowDefinition> {
        self.workflows.get(workflow_name)
    }
}
