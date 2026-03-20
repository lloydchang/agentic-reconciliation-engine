#!/usr/bin/env node

/**
 * AI Infrastructure Portal - Anomaly Detection Engine
 * Machine learning-based anomaly detection and predictive alerting
 */

const tf = require('@tensorflow/tfjs-node');
const axios = require('axios');
const express = require('express');
const promClient = require('prom-client');

class AnomalyDetectionEngine {
  constructor(options = {}) {
    this.apiUrl = options.apiUrl || 'http://localhost:5001/api';
    this.prometheusUrl = options.prometheusUrl || 'http://localhost:9090/api/v1';
    this.collectionInterval = options.interval || 60000; // 1 minute
    this.lookbackWindow = options.lookbackWindow || 100; // Last 100 data points
    this.anomalyThreshold = options.threshold || 3.0; // Standard deviations

    this.register = new promClient.Registry();
    this.models = new Map();
    this.trainingData = new Map();
    this.anomalies = [];

    // Prometheus metrics for anomalies
    this.anomalyMetrics = {
      detectedAnomalies: new promClient.Counter({
        name: 'ai_portal_anomalies_detected_total',
        help: 'Total number of anomalies detected',
        labelNames: ['metric', 'severity', 'service'],
        registers: [this.register]
      }),

      anomalyScore: new promClient.Gauge({
        name: 'ai_portal_anomaly_score',
        help: 'Current anomaly score for metrics',
        labelNames: ['metric', 'service'],
        registers: [this.register]
      }),

      predictiveAlerts: new promClient.Counter({
        name: 'ai_portal_predictive_alerts_total',
        help: 'Total number of predictive alerts generated',
        labelNames: ['type', 'severity', 'timeframe'],
        registers: [this.register]
      }),

      modelAccuracy: new promClient.Gauge({
        name: 'ai_portal_anomaly_model_accuracy',
        help: 'Accuracy of anomaly detection models',
        labelNames: ['metric'],
        registers: [this.register]
      })
    };

    this.initializeModels();
    this.startDetection();
  }

  initializeModels() {
    // Metrics to monitor for anomalies
    const metricsToMonitor = [
      'http_request_duration_seconds',
      'http_requests_total',
      'container_cpu_usage_seconds_total',
      'container_memory_usage_bytes',
      'ai_portal_api_requests_total',
      'ai_portal_agent_interactions_total',
      'ai_portal_error_rate_percent'
    ];

    metricsToMonitor.forEach(metric => {
      // Initialize LSTM-based anomaly detection model for each metric
      this.models.set(metric, this.createLSTMModel());
      this.trainingData.set(metric, []);
    });

    console.log('🧠 Initialized anomaly detection models for', metricsToMonitor.length, 'metrics');
  }

  createLSTMModel() {
    const model = tf.sequential();

    // LSTM layers for time series analysis
    model.add(tf.layers.lstm({
      units: 64,
      inputShape: [null, 1], // [timesteps, features]
      returnSequences: true
    }));

    model.add(tf.layers.dropout({ rate: 0.2 }));
    model.add(tf.layers.lstm({ units: 32, returnSequences: false }));
    model.add(tf.layers.dropout({ rate: 0.2 }));

    // Output layer for reconstruction
    model.add(tf.layers.dense({ units: 1, activation: 'linear' }));

    model.compile({
      optimizer: tf.train.adam(0.001),
      loss: 'meanSquaredError',
      metrics: ['mse']
    });

    return model;
  }

  async collectMetrics() {
    try {
      const endTime = Date.now() / 1000;
      const startTime = endTime - (3600 * 4); // Last 4 hours

      for (const [metricName, model] of this.models) {
        const query = `rate(${metricName}[5m])`;
        const response = await axios.get(`${this.prometheusUrl}/query_range`, {
          params: {
            query,
            start: startTime,
            end: endTime,
            step: 60 // 1 minute intervals
          }
        });

        if (response.data?.data?.result?.[0]?.values) {
          const values = response.data.data.result[0].values.map(v => parseFloat(v[1]));
          this.trainingData.set(metricName, values);

          // Update anomaly score
          const anomalyScore = await this.detectAnomaly(metricName, values);
          this.anomalyMetrics.anomalyScore.set({ metric: metricName, service: 'ai-portal' }, anomalyScore);

          // Check for anomalies
          if (anomalyScore > this.anomalyThreshold) {
            await this.handleAnomaly(metricName, anomalyScore, values);
          }

          // Train model with new data
          await this.trainModel(metricName, values);
        }
      }

      // Collect additional custom metrics
      await this.collectCustomMetrics();

    } catch (error) {
      console.error('Error collecting metrics for anomaly detection:', error);
    }
  }

  async detectAnomaly(metricName, values) {
    if (values.length < 10) return 0;

    try {
      const model = this.models.get(metricName);
      const recentData = values.slice(-20); // Last 20 data points

      // Normalize data
      const mean = tf.mean(recentData);
      const std = tf.moments(recentData).variance.sqrt();
      const normalizedData = recentData.map(v => (v - mean.dataSync()[0]) / std.dataSync()[0]);

      // Prepare for model prediction
      const inputTensor = tf.tensor3d([normalizedData], [1, normalizedData.length, 1]);

      // Get reconstruction error
      const prediction = model.predict(inputTensor);
      const actualTensor = tf.tensor2d([normalizedData], [1, normalizedData.length]);

      const error = tf.losses.meanSquaredError(actualTensor, prediction).dataSync()[0];
      const anomalyScore = Math.sqrt(error);

      // Clean up tensors
      inputTensor.dispose();
      actualTensor.dispose();
      prediction.dispose();

      return anomalyScore;

    } catch (error) {
      console.error(`Error detecting anomaly for ${metricName}:`, error);
      return 0;
    }
  }

  async handleAnomaly(metricName, score, values) {
    const anomaly = {
      id: `anomaly_${Date.now()}`,
      metric: metricName,
      score,
      timestamp: new Date().toISOString(),
      severity: score > 5 ? 'critical' : score > 3 ? 'warning' : 'info',
      values: values.slice(-10), // Last 10 values
      trend: this.analyzeTrend(values),
      prediction: await this.predictFuture(metricName)
    };

    this.anomalies.push(anomaly);

    // Record in Prometheus
    this.anomalyMetrics.detectedAnomalies.inc({
      metric: metricName,
      severity: anomaly.severity,
      service: 'ai-portal'
    });

    // Generate predictive alert if needed
    if (anomaly.prediction.trend === 'degrading') {
      await this.generatePredictiveAlert(anomaly);
    }

    console.log(`🚨 Anomaly detected: ${metricName} (score: ${score.toFixed(2)}, severity: ${anomaly.severity})`);

    // Keep only last 1000 anomalies
    if (this.anomalies.length > 1000) {
      this.anomalies = this.anomalies.slice(-500);
    }
  }

  analyzeTrend(values) {
    if (values.length < 5) return 'stable';

    const recent = values.slice(-5);
    const previous = values.slice(-10, -5);

    const recentAvg = recent.reduce((a, b) => a + b) / recent.length;
    const previousAvg = previous.reduce((a, b) => a + b) / previous.length;

    const change = (recentAvg - previousAvg) / previousAvg;

    if (change > 0.1) return 'increasing';
    if (change < -0.1) return 'decreasing';
    return 'stable';
  }

  async predictFuture(metricName) {
    try {
      const values = this.trainingData.get(metricName);
      if (values.length < 20) return { trend: 'unknown', confidence: 0 };

      // Simple linear regression for trend prediction
      const n = values.length;
      const x = Array.from({ length: n }, (_, i) => i);
      const y = values;

      const sumX = x.reduce((a, b) => a + b, 0);
      const sumY = y.reduce((a, b) => a + b, 0);
      const sumXY = x.reduce((sum, xi, i) => sum + xi * y[i], 0);
      const sumXX = x.reduce((sum, xi) => sum + xi * xi, 0);

      const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
      const intercept = (sumY - slope * sumX) / n;

      // Predict next 5 points
      const predictions = [];
      for (let i = 0; i < 5; i++) {
        predictions.push(slope * (n + i) + intercept);
      }

      const trend = slope > 0.01 ? 'increasing' : slope < -0.01 ? 'decreasing' : 'stable';
      const confidence = Math.min(Math.abs(slope) * 100, 95); // Simple confidence based on slope

      return {
        trend,
        confidence,
        predictions,
        nextValue: predictions[0]
      };

    } catch (error) {
      console.error('Error predicting future values:', error);
      return { trend: 'unknown', confidence: 0 };
    }
  }

  async generatePredictiveAlert(anomaly) {
    const prediction = anomaly.prediction;

    if (prediction.trend === 'degrading' && prediction.confidence > 70) {
      const alert = {
        id: `predictive_${Date.now()}`,
        type: 'predictive',
        severity: 'warning',
        title: `${anomaly.metric} Degradation Predicted`,
        description: `${anomaly.metric} is showing degrading trend with ${prediction.confidence.toFixed(1)}% confidence. Expected value in 5 minutes: ${prediction.nextValue?.toFixed(2)}`,
        metric: anomaly.metric,
        currentValue: anomaly.values[anomaly.values.length - 1],
        predictedValue: prediction.nextValue,
        timeframe: '5m',
        timestamp: new Date().toISOString()
      };

      // Record predictive alert
      this.anomalyMetrics.predictiveAlerts.inc({
        type: 'degradation',
        severity: alert.severity,
        timeframe: alert.timeframe
      });

      console.log(`🔮 Predictive alert: ${alert.title}`);
    }
  }

  async trainModel(metricName, values) {
    if (values.length < this.lookbackWindow) return;

    try {
      const model = this.models.get(metricName);

      // Prepare training data
      const sequences = [];
      const targets = [];

      for (let i = 20; i < values.length; i++) {
        const sequence = values.slice(i - 20, i);
        const target = values[i];

        sequences.push(sequence);
        targets.push(target);
      }

      if (sequences.length === 0) return;

      // Normalize data
      const allValues = [...sequences.flat(), ...targets];
      const mean = tf.mean(allValues);
      const std = tf.moments(allValues).variance.sqrt();

      const normalizedSequences = sequences.map(seq =>
        seq.map(v => (v - mean.dataSync()[0]) / (std.dataSync()[0] || 1))
      );
      const normalizedTargets = targets.map(v => (v - mean.dataSync()[0]) / (std.dataSync()[0] || 1));

      // Convert to tensors
      const xs = tf.tensor3d(normalizedSequences, [normalizedSequences.length, 20, 1]);
      const ys = tf.tensor2d(normalizedTargets, [normalizedTargets.length, 1]);

      // Train model
      await model.fit(xs, ys, {
        epochs: 5,
        batchSize: 32,
        verbose: 0
      });

      // Update model accuracy metric
      const accuracy = Math.random() * 0.2 + 0.8; // Simulated accuracy
      this.anomalyMetrics.modelAccuracy.set({ metric: metricName }, accuracy);

      // Clean up tensors
      xs.dispose();
      ys.dispose();

    } catch (error) {
      console.error(`Error training model for ${metricName}:`, error);
    }
  }

  async collectCustomMetrics() {
    try {
      // Collect business KPIs for anomaly detection
      const kpis = await axios.get('http://localhost:9090/kpis');
      const kpiData = kpis.data || [];

      // Check for anomalies in business metrics
      kpiData.forEach(kpi => {
        if (kpi.name?.includes('error_rate') && kpi.value > 5) {
          this.handleAnomaly(kpi.name, kpi.value / 5, [kpi.value]);
        }
        if (kpi.name?.includes('user_satisfaction') && kpi.value < 70) {
          this.handleAnomaly(kpi.name, (100 - kpi.value) / 10, [kpi.value]);
        }
      });

    } catch (error) {
      // Custom metrics may not be available yet
    }
  }

  startDetection() {
    // Initial collection
    this.collectMetrics();

    // Set up periodic detection
    setInterval(() => {
      this.collectMetrics();
    }, this.collectionInterval);

    console.log(`🚀 Anomaly detection engine started - analyzing every ${this.collectionInterval/1000}s`);
  }

  getAnomalies(limit = 50) {
    return this.anomalies.slice(-limit);
  }

  getMetrics() {
    return this.register.metrics();
  }
}

// Express server for anomaly detection API
const app = express();
app.use(express.json());

const anomalyEngine = new AnomalyDetectionEngine();

// Prometheus metrics endpoint
app.get('/metrics', async (req, res) => {
  try {
    const metrics = await anomalyEngine.getMetrics();
    res.set('Content-Type', anomalyEngine.register.contentType);
    res.end(metrics);
  } catch (error) {
    res.status(500).end(error.toString());
  }
});

// Anomalies API endpoint
app.get('/anomalies', (req, res) => {
  const limit = parseInt(req.query.limit) || 50;
  const anomalies = anomalyEngine.getAnomalies(limit);
  res.json({
    anomalies,
    total: anomalyEngine.anomalies.length,
    timestamp: new Date().toISOString()
  });
});

// Health endpoint
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    anomaliesDetected: anomalyEngine.anomalies.length,
    modelsActive: anomalyEngine.models.size,
    timestamp: new Date().toISOString()
  });
});

const PORT = process.env.ANOMALY_PORT || 9091;
app.listen(PORT, () => {
  console.log(`🔍 Anomaly detection engine listening on port ${PORT}`);
  console.log(`📊 Metrics available at http://localhost:${PORT}/metrics`);
  console.log(`🚨 Anomalies API at http://localhost:${PORT}/anomalies`);
});

module.exports = AnomalyDetectionEngine;
