use axum::{
    extract::{Path, State, Query},
    http::StatusCode,
    response::Json,
    routing::{get, post},
    Router,
};
use serde::{Deserialize, Serialize};

use crate::models::*;
use crate::events::{EventProcessor, AlertEvent};
use crate::workflows::WorkflowEngine;
use crate::skills::SkillEngine;

#[derive(Clone)]
pub struct IntegrationState {
    pub event_processor: EventProcessor,
    pub workflow_engine: WorkflowEngine,
    pub skill_engine: SkillEngine,
}

pub fn create_integration_routes(state: IntegrationState) -> Router {
    Router::new()
        .route("/api/integration/alerts", post(process_alert))
        .route("/api/integration/alerts", get(list_alerts))
        .route("/api/integration/alerts/:id", get(get_alert))
        .route("/api/integration/correlations/:id", get(get_correlation))
        .route("/api/integration/summary", get(get_summary))
        .route("/api/integration/workflows/trigger", post(trigger_workflow))
        .with_state(state)
}

#[derive(Deserialize)]
pub struct AlertQuery {
    pub correlation_id: Option<String>,
    pub status: Option<String>,
    pub component: Option<String>,
    pub limit: Option<u32>,
}

pub async fn process_alert(
    State(state): State<IntegrationState>,
    Json(alert): Json<AlertEvent>,
) -> Result<Json<EnrichedEvent>, StatusCode> {
    // Process the alert through enrichment and correlation
    let mut processor = state.event_processor;
    let enriched_event = processor.process_alert(alert).await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    // Determine if workflow should be triggered
    if should_trigger_workflow(&enriched_event) {
        if let Ok(workflow_name) = determine_workflow(&enriched_event) {
            let input_data = serde_json::to_value(&enriched_event).unwrap_or_default();
            
            if let Ok(execution_id) = state.workflow_engine.execute_workflow(&workflow_name, input_data).await {
                tracing::info!("Triggered workflow {} for alert correlation {}", 
                    workflow_name, enriched_event.correlation_id);
            }
        }
    }

    Ok(Json(enriched_event))
}

pub async fn list_alerts(
    State(state): State<IntegrationState>,
    Query(query): Query<AlertQuery>,
) -> Result<Json<Vec<EnrichedEvent>>, StatusCode> {
    let processor = &state.event_processor;
    let alerts = processor.get_pending_events()
        .into_iter()
        .filter(|event| {
            if let Some(ref correlation_id) = query.correlation_id {
                event.correlation_id != *correlation_id
            } else {
                true
            }
        })
        .filter(|event| {
            if let Some(ref component) = query.component {
                event.enriched.resource_name.as_ref().map_or(false, |name| name == component)
            } else {
                true
            }
        })
        .take(query.limit.unwrap_or(50) as usize)
        .cloned()
        .collect();

    Ok(Json(alerts))
}

pub async fn get_alert(
    State(state): State<IntegrationState>,
    Path(correlation_id): Path<String>,
) -> Result<Json<Vec<EnrichedEvent>>, StatusCode> {
    let processor = &state.event_processor;
    let events = processor.get_correlated_events(&correlation_id)
        .into_iter()
        .cloned()
        .collect();

    if events.is_empty() {
        return Err(StatusCode::NOT_FOUND);
    }

    Ok(Json(events))
}

pub async fn get_correlation(
    State(state): State<IntegrationState>,
    Path(correlation_id): Path<String>,
) -> Result<Json<CorrelationDetails>, StatusCode> {
    let processor = &state.event_processor;
    let events = processor.get_correlated_events(&correlation_id);
    
    if events.is_empty() {
        return Err(StatusCode::NOT_FOUND);
    }

    let primary_event = events.first().unwrap();
    let related_events: Vec<String> = primary_event.related_events.clone();

    let details = CorrelationDetails {
        correlation_id: correlation_id.clone(),
        primary_event: primary_event.clone(),
        related_events,
        event_count: events.len(),
        component_health: primary_event.enriched.component_health.clone(),
        recommended_actions: generate_recommendations(primary_event),
    };

    Ok(Json(details))
}

pub async fn get_summary(
    State(state): State<IntegrationState>,
) -> Json<EventSummary> {
    let processor = &state.event_processor;
    let summary = processor.generate_event_summary();
    Json(summary)
}

pub async fn trigger_workflow(
    State(state): State<IntegrationState>,
    Json(request): Json<WorkflowTriggerRequest>,
) -> Result<Json<WorkflowTriggerResponse>, StatusCode> {
    let input_data = serde_json::to_value(&request.input_data).unwrap_or_default();
    
    let execution_id = state.workflow_engine.execute_workflow(&request.workflow_name, input_data).await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    Ok(Json(WorkflowTriggerResponse {
        execution_id,
        workflow_name: request.workflow_name,
        status: "triggered".to_string(),
        message: "Workflow execution started".to_string(),
    }))
}

#[derive(Debug, Serialize, Deserialize)]
pub struct CorrelationDetails {
    pub correlation_id: String,
    pub primary_event: EnrichedEvent,
    pub related_events: Vec<String>,
    pub event_count: usize,
    pub component_health: crate::events::ComponentHealth,
    pub recommended_actions: Vec<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct WorkflowTriggerRequest {
    pub workflow_name: String,
    pub input_data: serde_json::Value,
    pub context: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct WorkflowTriggerResponse {
    pub execution_id: String,
    pub workflow_name: String,
    pub status: String,
    pub message: String,
}

fn should_trigger_workflow(event: &EnrichedEvent) -> bool {
    // Trigger workflow for critical alerts or repeated failures
    match event.original.severity.as_str() {
        "critical" => true,
        "warning" => event.enriched.failure_count >= 3,
        "info" => false,
        _ => false,
    }
}

fn determine_workflow(event: &EnrichedEvent) -> Result<String, ()> {
    // Determine appropriate workflow based on event characteristics
    if let Some(controller_type) = &event.enriched.controller_type {
        match controller_type.as_str() {
            "flux" | "crossplane" => Ok("troubleshooting".to_string()),
            _ => Ok("security-analysis".to_string()),
        }
    } else {
        // Fallback based on alert name
        if event.original.alertname.contains("cost") {
            Ok("cost-optimization".to_string())
        } else if event.original.alertname.contains("security") {
            Ok("security-analysis".to_string())
        } else if event.original.alertname.contains("certificate") {
            Ok("certificate-rotation".to_string())
        } else {
            Ok("troubleshooting".to_string())
        }
    }
}

fn generate_recommendations(event: &EnrichedEvent) -> Vec<String> {
    let mut recommendations = Vec::new();

    match event.enriched.component_health.status.as_str() {
        "unhealthy" => {
            recommendations.push("Immediate investigation required".to_string());
            recommendations.push("Consider service restart or rollback".to_string());
        },
        "degraded" => {
            recommendations.push("Monitor for escalation".to_string());
            recommendations.push("Review resource utilization".to_string());
        },
        "healthy" => {
            recommendations.push("Continue monitoring".to_string());
        },
        _ => {
            recommendations.push("Investigate component status".to_string());
        }
    }

    // Add specific recommendations based on failure reason
    if let Some(ref reason) = event.enriched.failure_reason {
        if reason.contains("reconciliation") {
            recommendations.push("Check Git repository connectivity".to_string());
            recommendations.push("Verify resource definitions".to_string());
        } else if reason.contains("network") {
            recommendations.push("Check network policies".to_string());
            recommendations.push("Verify service connectivity".to_string());
        } else if reason.contains("permission") {
            recommendations.push("Review RBAC permissions".to_string());
            recommendations.push("Check service account tokens".to_string());
        }
    }

    recommendations
}
