use serde::{Deserialize, Serialize};
use anyhow::{Result, anyhow};
use std::collections::HashMap;
use chrono::{DateTime, Utc, Duration};
use uuid::Uuid;

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct AlertEvent {
    pub alertname: String,
    pub namespace: String,
    pub severity: String,
    pub description: String,
    pub summary: String,
    pub labels: HashMap<String, String>,
    pub annotations: HashMap<String, String>,
    pub starts_at: DateTime<Utc>,
    pub ends_at: Option<DateTime<Utc>>,
    pub generator_url: Option<String>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct EnrichedEvent {
    pub original: AlertEvent,
    pub enriched: EventEnrichment,
    pub correlation_id: String,
    pub deduplicated: bool,
    pub related_events: Vec<String>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct EventEnrichment {
    pub controller_type: Option<String>,
    pub resource_kind: Option<String>,
    pub resource_name: Option<String>,
    pub failure_reason: Option<String>,
    pub reconciliation_status: Option<String>,
    pub last_success: Option<DateTime<Utc>>,
    pub failure_count: u32,
    pub component_health: ComponentHealth,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct ComponentHealth {
    pub status: String,
    pub uptime_percentage: f32,
    pub recent_failures: Vec<DateTime<Utc>>,
    pub error_rate: f32,
    pub last_error: Option<String>,
}

pub struct EventProcessor {
    event_cache: HashMap<String, EnrichedEvent>,
    correlation_window: Duration,
    deduplication_window: Duration,
}

impl EventProcessor {
    pub fn new() -> Self {
        Self {
            event_cache: HashMap::new(),
            correlation_window: Duration::minutes(5),
            deduplication_window: Duration::minutes(2),
        }
    }

    pub async fn process_alert(&mut self, alert: AlertEvent) -> Result<EnrichedEvent> {
        // Step 1: Check for deduplication
        if let Some(existing) = self.check_deduplication(&alert) {
            return Ok(existing.clone());
        }

        // Step 2: Enrich alert with additional context
        let enriched = self.enrich_alert(alert.clone()).await?;

        // Step 3: Correlate with related events
        let correlation_id = self.generate_correlation_id(&enriched);
        let related_events = self.find_related_events(&enriched, &correlation_id);

        // Step 4: Create enriched event
        let enriched_event = EnrichedEvent {
            original: alert,
            enriched,
            correlation_id: correlation_id.clone(),
            deduplicated: false,
            related_events,
        };

        // Step 5: Cache the event
        self.cache_event(correlation_id, enriched_event.clone());

        Ok(enriched_event)
    }

    fn check_deduplication(&mut self, alert: &AlertEvent) -> Option<&EnrichedEvent> {
        let alert_key = self.generate_alert_key(alert);
        
        for cached_event in self.event_cache.values() {
            if cached_event.original.alertname == alert.alertname 
                && cached_event.original.namespace == alert.namespace
                && cached_event.original.labels == alert.labels {
                
                // Check if within deduplication window
                let time_diff = alert.starts_at - cached_event.original.starts_at;
                if time_diff < self.deduplication_window {
                    return Some(cached_event);
                }
            }
        }

        None
    }

    async fn enrich_alert(&self, alert: &AlertEvent) -> Result<EventEnrichment> {
        let mut enrichment = EventEnrichment {
            controller_type: None,
            resource_kind: None,
            resource_name: None,
            failure_reason: None,
            reconciliation_status: None,
            last_success: None,
            failure_count: 0,
            component_health: ComponentHealth {
                status: "unknown".to_string(),
                uptime_percentage: 0.0,
                recent_failures: vec![],
                error_rate: 0.0,
                last_error: None,
            },
        };

        // Extract controller type from labels
        if let Some(controller) = alert.labels.get("controller") {
            enrichment.controller_type = Some(controller.clone());
        }

        // Extract resource information
        enrichment.resource_kind = alert.labels.get("resource_kind").cloned();
        enrichment.resource_name = alert.labels.get("resource_name").cloned();

        // Determine failure reason from annotations
        enrichment.failure_reason = alert.annotations.get("failure_reason").cloned();

        // Get reconciliation status from labels
        enrichment.reconciliation_status = alert.labels.get("reconciliation_status").cloned();

        // Calculate component health metrics
        enrichment.component_health = self.calculate_component_health(&alert).await;

        Ok(enrichment)
    }

    async fn calculate_component_health(&self, alert: &AlertEvent) -> ComponentHealth {
        // This would integrate with Prometheus/kube-state-metrics to get real health data
        // For now, return basic health based on alert severity
        let status = match alert.severity.as_str() {
            "critical" => "unhealthy",
            "warning" => "degraded", 
            "info" => "healthy",
            _ => "unknown",
        }.to_string();

        ComponentHealth {
            status,
            uptime_percentage: if status == "healthy" { 99.9 } else if status == "degraded" { 95.0 } else { 80.0 },
            recent_failures: vec![alert.starts_at],
            error_rate: if status == "healthy" { 0.01 } else if status == "degraded" { 0.05 } else { 0.15 },
            last_error: Some(alert.summary.clone()),
        }
    }

    fn generate_correlation_id(&self, enriched: &EventEnrichment) -> String {
        // Generate correlation ID based on component and failure type
        let base = format!(
            "{}-{}-{}",
            enriched.enriched.controller_type.as_deref().unwrap_or("unknown"),
            enriched.enriched.resource_name.as_deref().unwrap_or("unknown"),
            enriched.original.alertname
        );
        
        // Add hash for uniqueness
        format!("{}-{:x}", base, md5::compute(base.as_bytes())[0])
    }

    fn find_related_events(&self, enriched: &EventEnrichment, correlation_id: &str) -> Vec<String> {
        let mut related = Vec::new();

        for (cached_id, cached_event) in &self.event_cache {
            if cached_id != correlation_id {
                // Check if events are related (same component, similar timeframe)
                if self.are_events_related(enriched, cached_event) {
                    related.push(cached_id.clone());
                }
            }
        }

        related
    }

    fn are_events_related(&self, event1: &EnrichedEvent, event2: &EnrichedEvent) -> bool {
        // Events are related if they involve the same component and are within correlation window
        let same_component = match (&event1.enriched.resource_name, &event2.enriched.resource_name) {
            (Some(name1), Some(name2)) => name1 == name2,
            _ => false,
        };

        if !same_component {
            return false;
        }

        let time_diff = (event1.original.starts_at - event2.original.starts_at).abs();
        time_diff < self.correlation_window
    }

    fn generate_alert_key(&self, alert: &AlertEvent) -> String {
        format!(
            "{}-{}-{}",
            alert.alertname,
            alert.namespace,
            alert.labels.iter()
                .filter(|(k, _)| k.starts_with("resource_"))
                .map(|(k, v)| format!("{}:{}", k, v))
                .collect::<Vec<_>>()
                .join("-")
        )
    }

    fn cache_event(&mut self, correlation_id: String, event: EnrichedEvent) {
        self.event_cache.insert(correlation_id, event);
        
        // Clean old events from cache (keep last 1000)
        if self.event_cache.len() > 1000 {
            let mut events_by_time: Vec<_> = self.event_cache.values()
                .map(|e| (e.original.starts_at, e))
                .collect();
            events_by_time.sort_by_key(|(time, _)| *time);
            
            // Remove oldest 200 events
            for (_, event) in events_by_time.drain(..200) {
                if let Some(id) = self.event_cache.keys()
                    .find(|k| self.event_cache.get(k).map(|e| std::ptr::eq(e, event)).unwrap_or(false)) {
                    self.event_cache.remove(id);
                }
            }
        }
    }

    pub fn get_correlated_events(&self, correlation_id: &str) -> Vec<&EnrichedEvent> {
        self.event_cache
            .values()
            .filter(|e| e.correlation_id == correlation_id || e.related_events.contains(&correlation_id.to_string()))
            .collect()
    }

    pub fn get_pending_events(&self) -> Vec<&EnrichedEvent> {
        self.event_cache
            .values()
            .filter(|e| !e.deduplicated && e.enriched.component_health.status != "healthy")
            .collect()
    }

    pub fn generate_event_summary(&self) -> EventSummary {
        let total_events = self.event_cache.len();
        let pending_events = self.get_pending_events().len();
        let deduplicated_events = self.event_cache.values()
            .filter(|e| e.deduplicated)
            .count();

        let component_status = self.calculate_component_status_summary();

        EventSummary {
            total_events,
            pending_events,
            deduplicated_events,
            component_status,
            last_updated: Utc::now(),
        }
    }

    fn calculate_component_status_summary(&self) -> HashMap<String, ComponentStatusSummary> {
        let mut component_summary: HashMap<String, ComponentStatusSummary> = HashMap::new();

        for event in self.event_cache.values() {
            if let Some(component_name) = &event.enriched.resource_name {
                let summary = component_summary.entry(component_name.clone()).or_insert_with(|| ComponentStatusSummary {
                    name: component_name.clone(),
                    controller_type: event.enriched.controller_type.clone().unwrap_or_default(),
                    status: "healthy".to_string(),
                    event_count: 0,
                    last_event: None,
                    error_rate: 0.0,
                });

                summary.event_count += 1;
                if event.original.starts_at > summary.last_event.unwrap_or_else(|| DateTime::<Utc>::MIN_UTC) {
                    summary.last_event = Some(event.original.starts_at);
                }

                // Update status based on most recent event
                if summary.last_event == Some(event.original.starts_at) {
                    summary.status = event.enriched.component_health.status.clone();
                    summary.error_rate = event.enriched.component_health.error_rate;
                }
            }
        }

        component_summary
    }
}

#[derive(Debug, Serialize, Deserialize)]
pub struct EventSummary {
    pub total_events: usize,
    pub pending_events: usize,
    pub deduplicated_events: usize,
    pub component_status: HashMap<String, ComponentStatusSummary>,
    pub last_updated: DateTime<Utc>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ComponentStatusSummary {
    pub name: String,
    pub controller_type: String,
    pub status: String,
    pub event_count: usize,
    pub last_event: Option<DateTime<Utc>>,
    pub error_rate: f32,
}
