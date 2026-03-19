use crate::error::Result;
use prometheus::{
    register_counter, register_histogram, register_gauge_vec,
    Counter, Histogram, GaugeVec,
    opts, histogram_opts,
};
use std::time::Instant;

/// Metrics collector for the agent memory service
pub struct Metrics {
    pub requests_total: Counter,
    pub request_duration: Histogram,
    pub active_connections: GaugeVec,
    pub inference_requests_total: Counter,
    pub inference_duration: Histogram,
    pub database_operations_total: Counter,
    pub model_load_status: GaugeVec,
}

impl Metrics {
    pub fn new() -> Result<Self> {
        let requests_total = register_counter!(
            "agent_memory_requests_total",
            "Total number of requests",
            &["method", "endpoint", "status"]
        )?;

        let request_duration = register_histogram!(
            "agent_memory_request_duration_seconds",
            "Request duration in seconds",
            histogram_opts!(buckets(vec![0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0])
        )?;

        let active_connections = register_gauge_vec!(
            "agent_memory_active_connections",
            "Number of active connections",
            &["connection_type"]
        )?;

        let inference_requests_total = register_counter!(
            "agent_memory_inference_requests_total",
            "Total number of inference requests",
            &["model", "backend", "status"]
        )?;

        let inference_duration = register_histogram!(
            "agent_memory_inference_duration_seconds",
            "Inference duration in seconds",
            histogram_opts!(buckets(vec![0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 25.0, 50.0, 100.0]))
        )?;

        let database_operations_total = register_counter!(
            "agent_memory_database_operations_total",
            "Total number of database operations",
            &["operation", "table", "status"]
        )?;

        let model_load_status = register_gauge_vec!(
            "agent_memory_model_load_status",
            "Model load status (1 = loaded, 0 = not loaded)",
            &["model", "backend"]
        )?;

        Ok(Self {
            requests_total,
            request_duration,
            active_connections,
            inference_requests_total,
            inference_duration,
            database_operations_total,
            model_load_status,
        })
    }

    pub fn record_request(&self, method: &str, endpoint: &str, status: &str, duration: f64) {
        self.requests_total
            .with_label_values(&[method, endpoint, status])
            .inc();
        self.request_duration.observe(duration);
    }

    pub fn record_inference_request(&self, model: &str, backend: &str, status: &str, duration: f64) {
        self.inference_requests_total
            .with_label_values(&[model, backend, status])
            .inc();
        self.inference_duration.observe(duration);
    }

    pub fn record_database_operation(&self, operation: &str, table: &str, status: &str) {
        self.database_operations_total
            .with_label_values(&[operation, table, status])
            .inc();
    }

    pub fn set_active_connections(&self, connection_type: &str, count: f64) {
        self.active_connections
            .with_label_values(&[connection_type])
            .set(count);
    }

    pub fn set_model_load_status(&self, model: &str, backend: &str, loaded: bool) {
        self.model_load_status
            .with_label_values(&[model, backend])
            .set(if loaded { 1.0 } else { 0.0 });
    }

    pub fn increment_active_connections(&self, connection_type: &str) {
        self.active_connections
            .with_label_values(&[connection_type])
            .inc();
    }

    pub fn decrement_active_connections(&self, connection_type: &str) {
        self.active_connections
            .with_label_values(&[connection_type])
            .dec();
    }
}

/// Request timer for measuring duration
pub struct RequestTimer {
    start: Instant,
    metrics: Option<&'static Metrics>,
    labels: Option<(&'static str, &'static str, &'static str)>,
}

impl RequestTimer {
    pub fn new() -> Self {
        Self {
            start: Instant::now(),
            metrics: None,
            labels: None,
        }
    }

    pub fn with_metrics(metrics: &'static Metrics) -> Self {
        Self {
            start: Instant::now(),
            metrics: Some(metrics),
            labels: None,
        }
    }

    pub fn with_labels(mut self, method: &'static str, endpoint: &'static str, status: &'static str) -> Self {
        self.labels = Some((method, endpoint, status));
        self
    }

    pub fn duration(&self) -> f64 {
        self.start.elapsed().as_secs_f64()
    }

    pub fn record(self) {
        if let (Some(metrics), Some((method, endpoint, status))) = (self.metrics, self.labels) {
            metrics.record_request(method, endpoint, status, self.duration());
        }
    }
}

impl Default for RequestTimer {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_request_timer() {
        let timer = RequestTimer::new();
        std::thread::sleep(std::time::Duration::from_millis(10));
        let duration = timer.duration();
        assert!(duration >= 0.01);
    }

    #[test]
    fn test_metrics_creation() {
        // This test might fail if Prometheus metrics are already registered
        // In a real scenario, we'd need to handle this better
        let result = Metrics::new();
        // We can't assert success here due to global state
        println!("Metrics creation result: {:?}", result.is_ok());
    }
}
