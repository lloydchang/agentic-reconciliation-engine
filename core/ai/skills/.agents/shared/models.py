#!/usr/bin/env python3
"""
Shared Pydantic models for agent skills type safety
"""

# /// script
# dependencies = [
#   "pydantic>=1.10.0",
#   "typing-extensions>=4.0.0"
# ]
# ///

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class CloudProvider(str, Enum):
    """Supported cloud providers"""
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    ONPREM = "onprem"
    ALL = "all"


class OperationType(str, Enum):
    """Supported operation types"""
    PROVISION = "provision"
    DEPLOY = "deploy"
    SCALE = "scale"
    STOP = "stop"
    START = "start"
    STATUS = "status"
    HEALTH_CHECK = "health_check"
    OPTIMIZE = "optimize"
    ROLLBACK = "rollback"


class RiskLevel(str, Enum):
    """Risk levels for operations"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class AutonomyLevel(str, Enum):
    """Autonomy levels for operations"""
    FULLY_AUTO = "fully_auto"
    CONDITIONAL = "conditional"
    REQUIRES_PR = "requires_pr"


class Environment(str, Enum):
    """Target environments"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    ALL = "all"


class BaseAgentRequest(BaseModel):
    """Base model for all agent requests"""
    operation: OperationType = Field(..., description="Operation type to perform")
    target_resource: str = Field(..., description="Target resource identifier")
    cloud_provider: CloudProvider = Field(CloudProvider.ALL, description="Cloud provider")
    environment: Environment = Field(Environment.PRODUCTION, description="Target environment")
    dry_run: bool = Field(True, description="Dry run mode")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Operation-specific parameters")
    
    @validator('parameters')
    def validate_parameters(cls, v):
        """Validate parameters dictionary"""
        if not isinstance(v, dict):
            raise ValueError("Parameters must be a dictionary")
        return v


class InfrastructureRequest(BaseAgentRequest):
    """Infrastructure provisioning specific request"""
    resource_type: str = Field(..., description="Type of resource to provision")
    region: str = Field(..., description="Target region")
    configuration: Dict[str, Any] = Field(..., description="Resource configuration")
    tags: Dict[str, str] = Field(default_factory=dict, description="Resource tags")
    dependencies: List[str] = Field(default_factory=list, description="Resource dependencies")


class HealthCheckRequest(BaseAgentRequest):
    """Health check specific request"""
    check_types: List[str] = Field(default_factory=["node", "pod", "network"], description="Types of health checks to perform")
    cluster_name: Optional[str] = Field(None, description="Specific cluster name")
    severity_threshold: str = Field("warning", description="Minimum severity to report")


class OptimizationRequest(BaseAgentRequest):
    """Resource optimization specific request"""
    optimization_type: str = Field("cost", description="Type of optimization (cost, performance, security)")
    savings_target: Optional[float] = Field(None, description="Target savings percentage")
    performance_threshold: Optional[float] = Field(None, description="Minimum performance threshold")


class BaseAgentResult(BaseModel):
    """Base model for all agent results"""
    operation_id: str = Field(..., description="Unique operation identifier")
    operation: OperationType = Field(..., description="Operation performed")
    status: str = Field(..., description="Operation status")
    message: str = Field("", description="Result message")
    data: Optional[Dict[str, Any]] = Field(None, description="Result data")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Result timestamp")
    execution_time: Optional[float] = Field(None, description="Execution time in seconds")
    cloud_provider: CloudProvider = Field(..., description="Cloud provider")
    environment: Environment = Field(..., description="Target environment")


class InfrastructureResult(BaseAgentResult):
    """Infrastructure provisioning specific result"""
    resource_id: Optional[str] = Field(None, description="Provisioned resource ID")
    resource_type: str = Field(..., description="Type of resource provisioned")
    configuration: Optional[Dict[str, Any]] = Field(None, description="Final resource configuration")
    cost_estimate: Optional[float] = Field(None, description="Estimated monthly cost")


class HealthCheckResult(BaseAgentResult):
    """Health check specific result"""
    cluster_name: str = Field(..., description="Cluster name")
    health_score: Optional[float] = Field(None, description="Overall health score (0-100)")
    issues: List[Dict[str, Any]] = Field(default_factory=list, description="Identified issues")
    recommendations: List[str] = Field(default_factory=list, description="Health recommendations")


class OptimizationResult(BaseAgentResult):
    """Resource optimization specific result"""
    optimization_type: str = Field(..., description="Type of optimization performed")
    estimated_savings: Optional[float] = Field(None, description="Estimated monthly savings")
    actual_savings: Optional[float] = Field(None, description="Actual monthly savings")
    recommendations: List[Dict[str, Any]] = Field(default_factory=list, description="Optimization recommendations")


class OrchestrationTask(BaseModel):
    """Orchestration task model"""
    task_id: str = Field(..., description="Unique task identifier")
    provider: CloudProvider = Field(..., description="Cloud provider")
    action: OperationType = Field(..., description="Action to perform")
    parameters: Dict[str, Any] = Field(..., description="Task parameters")
    priority: str = Field("medium", description="Task priority")
    status: str = Field("pending", description="Task status")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Task creation time")
    dependencies: List[str] = Field(default_factory=list, description="Task dependencies")
    started_at: Optional[datetime] = Field(None, description="Task start time")
    completed_at: Optional[datetime] = Field(None, description="Task completion time")
    result: Optional[Dict[str, Any]] = Field(None, description="Task result")
    error: Optional[str] = Field(None, description="Task error")


class OrchestrationResult(BaseModel):
    """Orchestration result model"""
    task_id: str = Field(..., description="Task identifier")
    provider: CloudProvider = Field(..., description="Cloud provider")
    action: OperationType = Field(..., description="Action performed")
    status: str = Field(..., description="Result status")
    message: str = Field("", description="Result message")
    data: Optional[Dict[str, Any]] = Field(None, description="Result data")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Result timestamp")
    execution_time: Optional[float] = Field(None, description="Execution time in seconds")


class OrchestrationSummary(BaseModel):
    """Orchestration summary model"""
    orchestration_id: str = Field(..., description="Orchestration identifier")
    total_tasks: int = Field(..., description="Total number of tasks")
    completed_tasks: int = Field(..., description="Number of completed tasks")
    successful_tasks: int = Field(..., description="Number of successful tasks")
    failed_tasks: int = Field(..., description="Number of failed tasks")
    total_resources: int = Field(..., description="Total resources affected")
    total_cost_estimate: Optional[float] = Field(None, description="Total cost estimate")
    success_rate: float = Field(..., description="Success rate (0-1)")
    providers: List[CloudProvider] = Field(..., description="Providers involved")
    resource_types: List[str] = Field(..., description="Resource types affected")
    start_time: datetime = Field(..., description="Orchestration start time")
    end_time: Optional[datetime] = Field(None, description="Orchestration end time")
    status: str = Field("in_progress", description="Orchestration status")


# Human gate configuration
class HumanGateConfig(BaseModel):
    """Human gate configuration"""
    required: bool = Field(False, description="Whether human approval is required")
    approvers: List[str] = Field(default_factory=list, description="Required approvers")
    timeout_minutes: int = Field(60, description="Approval timeout in minutes")
    message: str = Field("", description="Gate message for approvers")


class SkillMetadata(BaseModel):
    """Skill execution metadata"""
    skill_name: str = Field(..., description="Skill name")
    version: str = Field("1.0", description="Skill version")
    risk_level: RiskLevel = Field(RiskLevel.MEDIUM, description="Operation risk level")
    autonomy: AutonomyLevel = Field(AutonomyLevel.CONDITIONAL, description="Operation autonomy level")
    human_gate: HumanGateConfig = Field(default_factory=HumanGateConfig, description="Human gate configuration")
    execution_id: str = Field(..., description="Unique execution identifier")
    started_at: datetime = Field(default_factory=datetime.utcnow, description="Execution start time")
