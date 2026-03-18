package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"math"
	"sort"
	"sync"
	"time"

	"go.temporal.io/sdk/workflow"
)

// MetricType represents different types of metrics
type MetricType string

const (
	MetricTypeCounter   MetricType = "counter"
	MetricTypeGauge     MetricType = "gauge"
	MetricTypeHistogram MetricType = "histogram"
	MetricTypeSummary   MetricType = "summary"
)

// Metric represents a single metric measurement
type Metric struct {
	Name      string                 `json:"name"`
	Type      MetricType             `json:"type"`
	Value     float64                `json:"value"`
	Labels    map[string]string      `json:"labels,omitempty"`
	Timestamp time.Time              `json:"timestamp"`
	Metadata  map[string]interface{} `json:"metadata,omitempty"`
}

// TimeSeriesData represents time series data for analysis
type TimeSeriesData struct {
	MetricName string    `json:"metric_name"`
	Labels     map[string]string `json:"labels,omitempty"`
	DataPoints []DataPoint `json:"data_points"`
}

// DataPoint represents a single data point in time series
type DataPoint struct {
	Timestamp time.Time `json:"timestamp"`
	Value     float64   `json:"value"`
}

// Anomaly represents a detected anomaly
type Anomaly struct {
	ID          string                 `json:"id"`
	MetricName  string                 `json:"metric_name"`
	Type        string                 `json:"type"` // "spike", "drop", "trend_change", "seasonal"
	Severity    string                 `json:"severity"` // "low", "medium", "high", "critical"
	Timestamp   time.Time              `json:"timestamp"`
	Value       float64                `json:"value"`
	ExpectedValue float64              `json:"expected_value"`
	Deviation   float64                `json:"deviation"`
	Description string                 `json:"description"`
	Labels      map[string]string      `json:"labels,omitempty"`
	Metadata    map[string]interface{} `json:"metadata,omitempty"`
}

// Trend represents a detected trend
type Trend struct {
	ID            string            `json:"id"`
	MetricName    string            `json:"metric_name"`
	Type          string            `json:"type"` // "increasing", "decreasing", "stable", "volatile"
	Direction     string            `json:"direction"` // "up", "down", "flat"
	Slope         float64           `json:"slope"`
	R2            float64           `json:"r_squared"`
	Confidence    float64           `json:"confidence"`
	StartTime     time.Time         `json:"start_time"`
	EndTime       time.Time         `json:"end_time"`
	DataPoints    int               `json:"data_points"`
	Description   string            `json:"description"`
	Labels        map[string]string `json:"labels,omitempty"`
}

// Insight represents an automated insight
type Insight struct {
	ID          string                 `json:"id"`
	Type        string                 `json:"type"` // "anomaly", "trend", "correlation", "prediction"
	Title       string                 `json:"title"`
	Description string                 `json:"description"`
	Severity    string                 `json:"severity"` // "info", "warning", "critical"
	Timestamp   time.Time              `json:"timestamp"`
	RelatedMetrics []string            `json:"related_metrics"`
	Recommendations []string           `json:"recommendations,omitempty"`
	Data        map[string]interface{} `json:"data,omitempty"`
	Metadata    map[string]interface{} `json:"metadata,omitempty"`
}

// AnalyticsEngine provides advanced analytics capabilities
type AnalyticsEngine struct {
	metrics       map[string]*TimeSeriesData
	anomalies     []*Anomaly
	trends        []*Trend
	insights      []*Insight
	mutex         sync.RWMutex
	windowSize    time.Duration
	anomalyThreshold float64
	trendWindow   time.Duration
}

// NewAnalyticsEngine creates a new analytics engine
func NewAnalyticsEngine(windowSize time.Duration) *AnalyticsEngine {
	return &AnalyticsEngine{
		metrics:          make(map[string]*TimeSeriesData),
		anomalies:        make([]*Anomaly, 0),
		trends:           make([]*Trend, 0),
		insights:         make([]*Insight, 0),
		windowSize:       windowSize,
		anomalyThreshold: 3.0, // 3 standard deviations
		trendWindow:      24 * time.Hour,
	}
}

// RecordMetric records a new metric measurement
func (ae *AnalyticsEngine) RecordMetric(metric *Metric) {
	ae.mutex.Lock()
	defer ae.mutex.Unlock()

	key := ae.getMetricKey(metric.Name, metric.Labels)

	if _, exists := ae.metrics[key]; !exists {
		ae.metrics[key] = &TimeSeriesData{
			MetricName: metric.Name,
			Labels:     metric.Labels,
			DataPoints: make([]DataPoint, 0),
		}
	}

	// Add data point
	dataPoint := DataPoint{
		Timestamp: metric.Timestamp,
		Value:     metric.Value,
	}
	ae.metrics[key].DataPoints = append(ae.metrics[key].DataPoints, dataPoint)

	// Clean old data points outside the window
	ae.cleanOldDataPoints(key)

	// Analyze for anomalies and trends
	ae.analyzeMetric(key)
}

// getMetricKey generates a unique key for a metric
func (ae *AnalyticsEngine) getMetricKey(name string, labels map[string]string) string {
	key := name
	if len(labels) > 0 {
		// Sort labels for consistent key generation
		var sortedLabels []string
		for k, v := range labels {
			sortedLabels = append(sortedLabels, fmt.Sprintf("%s=%s", k, v))
		}
		sort.Strings(sortedLabels)
		key += "{" + strings.Join(sortedLabels, ",") + "}"
	}
	return key
}

// cleanOldDataPoints removes data points older than the window size
func (ae *AnalyticsEngine) cleanOldDataPoints(key string) {
	metric := ae.metrics[key]
	cutoff := time.Now().Add(-ae.windowSize)

	validPoints := make([]DataPoint, 0)
	for _, point := range metric.DataPoints {
		if point.Timestamp.After(cutoff) {
			validPoints = append(validPoints, point)
		}
	}
	metric.DataPoints = validPoints
}

// analyzeMetric performs anomaly detection and trend analysis on a metric
func (ae *AnalyticsEngine) analyzeMetric(key string) {
	metric := ae.metrics[key]
	if len(metric.DataPoints) < 10 { // Need minimum data points for analysis
		return
	}

	// Detect anomalies
	anomalies := ae.detectAnomalies(metric)
	for _, anomaly := range anomalies {
		ae.anomalies = append(ae.anomalies, anomaly)
		ae.generateAnomalyInsight(anomaly)
	}

	// Detect trends
	if len(metric.DataPoints) >= 20 { // Need more points for trend analysis
		trend := ae.detectTrend(metric)
		if trend != nil {
			ae.trends = append(ae.trends, trend)
			ae.generateTrendInsight(trend)
		}
	}

	// Clean old anomalies and trends
	ae.cleanOldAnalysis()
}

// detectAnomalies detects statistical anomalies in time series data
func (ae *AnalyticsEngine) detectAnomalies(data *TimeSeriesData) []*Anomaly {
	if len(data.DataPoints) < 10 {
		return nil
	}

	// Calculate rolling statistics
	values := make([]float64, len(data.DataPoints))
	for i, point := range data.DataPoints {
		values[i] = point.Value
	}

	mean, std := ae.calculateMeanStd(values)

	anomalies := make([]*Anomaly, 0)

	// Check recent points for anomalies
	recentPoints := 5
	if len(values) < recentPoints {
		recentPoints = len(values)
	}

	for i := len(values) - recentPoints; i < len(values); i++ {
		value := values[i]
		timestamp := data.DataPoints[i].Timestamp

		zScore := math.Abs((value - mean) / std)
		if zScore > ae.anomalyThreshold {
			anomalyType := "spike"
			if value < mean {
				anomalyType = "drop"
			}

			anomaly := &Anomaly{
				ID:            fmt.Sprintf("anomaly-%s-%d", data.MetricName, timestamp.Unix()),
				MetricName:    data.MetricName,
				Type:          anomalyType,
				Severity:      ae.calculateSeverity(zScore),
				Timestamp:     timestamp,
				Value:         value,
				ExpectedValue: mean,
				Deviation:     zScore,
				Description:   fmt.Sprintf("%s detected: %.2f (expected: %.2f, z-score: %.2f)", anomalyType, value, mean, zScore),
				Labels:        data.Labels,
			}
			anomalies = append(anomalies, anomaly)
		}
	}

	return anomalies
}

// calculateMeanStd calculates mean and standard deviation
func (ae *AnalyticsEngine) calculateMeanStd(values []float64) (float64, float64) {
	if len(values) == 0 {
		return 0, 0
	}

	sum := 0.0
	for _, v := range values {
		sum += v
	}
	mean := sum / float64(len(values))

	sumSq := 0.0
	for _, v := range values {
		sumSq += (v - mean) * (v - mean)
	}
	std := math.Sqrt(sumSq / float64(len(values)))

	return mean, std
}

// calculateSeverity determines anomaly severity based on z-score
func (ae *AnalyticsEngine) calculateSeverity(zScore float64) string {
	switch {
	case zScore >= 5.0:
		return "critical"
	case zScore >= 3.5:
		return "high"
	case zScore >= 2.5:
		return "medium"
	default:
		return "low"
	}
}

// detectTrend detects linear trends in time series data
func (ae *AnalyticsEngine) detectTrend(data *TimeSeriesData) *Trend {
	if len(data.DataPoints) < 20 {
		return nil
	}

	// Simple linear regression
	n := float64(len(data.DataPoints))
	sumX, sumY, sumXY, sumX2 := 0.0, 0.0, 0.0, 0.0

	startTime := data.DataPoints[0].Timestamp.Unix()
	for i, point := range data.DataPoints {
		x := float64(point.Timestamp.Unix() - startTime)
		y := point.Value

		sumX += x
		sumY += y
		sumXY += x * y
		sumX2 += x * x
	}

	// Calculate slope and intercept
	slope := (n*sumXY - sumX*sumY) / (n*sumX2 - sumX*sumX)
	intercept := (sumY - slope*sumX) / n

	// Calculate R-squared
	yMean := sumY / n
	ssRes, ssTot := 0.0, 0.0
	for i, point := range data.DataPoints {
		x := float64(point.Timestamp.Unix() - startTime)
		y := point.Value
		predicted := slope*x + intercept

		ssRes += (y - predicted) * (y - predicted)
		ssTot += (y - yMean) * (y - yMean)
	}
	r2 := 1.0 - (ssRes / ssTot)

	// Determine trend type and direction
	trendType := "stable"
	direction := "flat"
	confidence := r2

	if math.Abs(slope) > 0.01 { // Significant slope
		if slope > 0 {
			trendType = "increasing"
			direction = "up"
		} else {
			trendType = "decreasing"
			direction = "down"
		}
	}

	// Only return significant trends
	if r2 < 0.5 { // R-squared threshold
		return nil
	}

	return &Trend{
		ID:          fmt.Sprintf("trend-%s-%d", data.MetricName, time.Now().Unix()),
		MetricName:  data.MetricName,
		Type:        trendType,
		Direction:   direction,
		Slope:       slope,
		R2:          r2,
		Confidence:  confidence,
		StartTime:   data.DataPoints[0].Timestamp,
		EndTime:     data.DataPoints[len(data.DataPoints)-1].Timestamp,
		DataPoints:  len(data.DataPoints),
		Description: fmt.Sprintf("%s trend detected (slope: %.4f, R²: %.2f)", trendType, slope, r2),
		Labels:      data.Labels,
	}
}

// cleanOldAnalysis removes old anomalies and trends
func (ae *AnalyticsEngine) cleanOldAnalysis() {
	cutoff := time.Now().Add(-ae.windowSize)

	// Clean old anomalies
	validAnomalies := make([]*Anomaly, 0)
	for _, anomaly := range ae.anomalies {
		if anomaly.Timestamp.After(cutoff) {
			validAnomalies = append(validAnomalies, anomaly)
		}
	}
	ae.anomalies = validAnomalies

	// Clean old trends
	validTrends := make([]*Trend, 0)
	for _, trend := range ae.trends {
		if trend.EndTime.After(cutoff) {
			validTrends = append(validTrends, trend)
		}
	}
	ae.trends = validTrends

	// Clean old insights
	validInsights := make([]*Insight, 0)
	for _, insight := range ae.insights {
		if insight.Timestamp.After(cutoff) {
			validInsights = append(validInsights, insight)
		}
	}
	ae.insights = validInsights
}

// generateAnomalyInsight creates an insight from an anomaly
func (ae *AnalyticsEngine) generateAnomalyInsight(anomaly *Anomaly) {
	insight := &Insight{
		ID:             fmt.Sprintf("insight-%s", anomaly.ID),
		Type:           "anomaly",
		Title:          fmt.Sprintf("Anomaly Detected: %s", anomaly.MetricName),
		Description:    anomaly.Description,
		Severity:       anomaly.Severity,
		Timestamp:      anomaly.Timestamp,
		RelatedMetrics: []string{anomaly.MetricName},
		Data: map[string]interface{}{
			"anomaly": anomaly,
		},
	}

	// Add recommendations based on anomaly type
	switch anomaly.Type {
	case "spike":
		insight.Recommendations = []string{
			"Investigate potential resource exhaustion",
			"Check for configuration changes",
			"Review recent deployments",
		}
	case "drop":
		insight.Recommendations = []string{
			"Verify service health",
			"Check network connectivity",
			"Review error logs",
		}
	}

	ae.insights = append(ae.insights, insight)
}

// generateTrendInsight creates an insight from a trend
func (ae *AnalyticsEngine) generateTrendInsight(trend *Trend) {
	insight := &Insight{
		ID:             fmt.Sprintf("insight-%s", trend.ID),
		Type:           "trend",
		Title:          fmt.Sprintf("Trend Detected: %s", trend.MetricName),
		Description:    trend.Description,
		Severity:       "info",
		Timestamp:      time.Now(),
		RelatedMetrics: []string{trend.MetricName},
		Data: map[string]interface{}{
			"trend": trend,
		},
	}

	// Add recommendations based on trend type
	switch trend.Type {
	case "increasing":
		if strings.Contains(trend.MetricName, "error") || strings.Contains(trend.MetricName, "failure") {
			insight.Severity = "warning"
			insight.Recommendations = []string{
				"Monitor error rate closely",
				"Investigate root cause",
				"Consider scaling resources",
			}
		} else if strings.Contains(trend.MetricName, "cpu") || strings.Contains(trend.MetricName, "memory") {
			insight.Recommendations = []string{
				"Consider resource optimization",
				"Review workload patterns",
				"Plan capacity upgrades",
			}
		}
	case "decreasing":
		if strings.Contains(trend.MetricName, "performance") || strings.Contains(trend.MetricName, "throughput") {
			insight.Severity = "warning"
			insight.Recommendations = []string{
				"Investigate performance degradation",
				"Check resource utilization",
				"Review recent changes",
			}
		}
	}

	ae.insights = append(ae.insights, insight)
}

// GetMetrics returns time series data for a metric
func (ae *AnalyticsEngine) GetMetrics(metricName string, labels map[string]string, duration time.Duration) *TimeSeriesData {
	ae.mutex.RLock()
	defer ae.mutex.RUnlock()

	key := ae.getMetricKey(metricName, labels)
	metric, exists := ae.metrics[key]
	if !exists {
		return nil
	}

	// Filter by time range
	cutoff := time.Now().Add(-duration)
	filteredPoints := make([]DataPoint, 0)
	for _, point := range metric.DataPoints {
		if point.Timestamp.After(cutoff) {
			filteredPoints = append(filteredPoints, point)
		}
	}

	return &TimeSeriesData{
		MetricName: metricName,
		Labels:     labels,
		DataPoints: filteredPoints,
	}
}

// GetAnomalies returns detected anomalies
func (ae *AnalyticsEngine) GetAnomalies(severity string, duration time.Duration) []*Anomaly {
	ae.mutex.RLock()
	defer ae.mutex.RUnlock()

	cutoff := time.Now().Add(-duration)
	anomalies := make([]*Anomaly, 0)

	for _, anomaly := range ae.anomalies {
		if anomaly.Timestamp.After(cutoff) {
			if severity == "" || anomaly.Severity == severity {
				anomalies = append(anomalies, anomaly)
			}
		}
	}

	return anomalies
}

// GetTrends returns detected trends
func (ae *AnalyticsEngine) GetTrends(duration time.Duration) []*Trend {
	ae.mutex.RLock()
	defer ae.mutex.RUnlock()

	cutoff := time.Now().Add(-duration)
	trends := make([]*Trend, 0)

	for _, trend := range ae.trends {
		if trend.EndTime.After(cutoff) {
			trends = append(trends, trend)
		}
	}

	return trends
}

// GetInsights returns generated insights
func (ae *AnalyticsEngine) GetInsights(insightType string, severity string, duration time.Duration) []*Insight {
	ae.mutex.RLock()
	defer ae.mutex.RUnlock()

	cutoff := time.Now().Add(-duration)
	insights := make([]*Insight, 0)

	for _, insight := range ae.insights {
		if insight.Timestamp.After(cutoff) {
			if (insightType == "" || insight.Type == insightType) &&
			   (severity == "" || insight.Severity == severity) {
				insights = append(insights, insight)
			}
		}
	}

	return insights
}

// GeneratePredictiveInsights generates predictive analytics insights
func (ae *AnalyticsEngine) GeneratePredictiveInsights() []*Insight {
	ae.mutex.Lock()
	defer ae.mutex.Unlock()

	insights := make([]*Insight, 0)

	// Analyze patterns across all metrics for predictive insights
	for key, metric := range ae.metrics {
		if len(metric.DataPoints) < 30 { // Need sufficient data for prediction
			continue
		}

		// Simple trend extrapolation for prediction
		if trend := ae.detectTrend(metric); trend != nil && trend.Confidence > 0.7 {
			prediction := ae.generatePrediction(trend, metric)
			if prediction != nil {
				insights = append(insights, prediction)
			}
		}

		// Detect seasonal patterns
		if seasonal := ae.detectSeasonalPattern(metric); seasonal != nil {
			insights = append(insights, seasonal)
		}
	}

	// Cross-metric correlation analysis
	correlationInsights := ae.analyzeCorrelations()
	insights = append(insights, correlationInsights...)

	return insights
}

// generatePrediction generates a predictive insight based on trend
func (ae *AnalyticsEngine) generatePrediction(trend *Trend, metric *TimeSeriesData) *Insight {
	if len(metric.DataPoints) < 10 {
		return nil
	}

	// Extrapolate next value based on trend
	lastPoint := metric.DataPoints[len(metric.DataPoints)-1]
	timeDiff := trend.EndTime.Sub(trend.StartTime)
	avgInterval := timeDiff / time.Duration(len(metric.DataPoints)-1)

	nextTimestamp := lastPoint.Timestamp.Add(avgInterval)
	nextValue := lastPoint.Value + trend.Slope*avgInterval.Hours()

	insight := &Insight{
		ID:             fmt.Sprintf("prediction-%s-%d", trend.MetricName, time.Now().Unix()),
		Type:           "prediction",
		Title:          fmt.Sprintf("Predicted Value: %s", trend.MetricName),
		Description:    fmt.Sprintf("Based on current %s trend, predicted value at %s: %.2f", trend.Type, nextTimestamp.Format("2006-01-02 15:04:05"), nextValue),
		Severity:       "info",
		Timestamp:      time.Now(),
		RelatedMetrics: []string{trend.MetricName},
		Data: map[string]interface{}{
			"predicted_timestamp": nextTimestamp,
			"predicted_value":     nextValue,
			"trend":              trend,
		},
	}

	// Add recommendations based on prediction
	if strings.Contains(trend.MetricName, "cpu") && nextValue > 80.0 {
		insight.Severity = "warning"
		insight.Recommendations = []string{
			"Monitor CPU usage closely",
			"Consider horizontal scaling",
			"Optimize resource allocation",
		}
	}

	return insight
}

// detectSeasonalPattern detects simple seasonal patterns (daily/weekly)
func (ae *AnalyticsEngine) detectSeasonalPattern(metric *TimeSeriesData) *Insight {
	if len(metric.DataPoints) < 48 { // Need at least 2 days of hourly data
		return nil
	}

	// Simple autocorrelation analysis for daily patterns
	values := make([]float64, len(metric.DataPoints))
	for i, point := range metric.DataPoints {
		values[i] = point.Value
	}

	// Check for 24-hour pattern (assuming hourly data)
	period := 24
	if len(values) >= period*2 {
		correlation := ae.calculateAutocorrelation(values, period)
		if correlation > 0.6 { // Strong correlation
			return &Insight{
				ID:             fmt.Sprintf("seasonal-%s-%d", metric.MetricName, time.Now().Unix()),
				Type:           "correlation",
				Title:          fmt.Sprintf("Seasonal Pattern Detected: %s", metric.MetricName),
				Description:    fmt.Sprintf("Daily seasonal pattern detected (autocorrelation: %.2f)", correlation),
				Severity:       "info",
				Timestamp:      time.Now(),
				RelatedMetrics: []string{metric.MetricName},
				Data: map[string]interface{}{
					"pattern_type":    "daily",
					"autocorrelation": correlation,
					"period_hours":    period,
				},
			}
		}
	}

	return nil
}

// calculateAutocorrelation calculates autocorrelation for a given lag
func (ae *AnalyticsEngine) calculateAutocorrelation(values []float64, lag int) float64 {
	if len(values) < lag*2 {
		return 0
	}

	n := len(values) - lag
	sumXY, sumX, sumY, sumX2, sumY2 := 0.0, 0.0, 0.0, 0.0, 0.0

	for i := 0; i < n; i++ {
		x := values[i]
		y := values[i+lag]

		sumXY += x * y
		sumX += x
		sumY += y
		sumX2 += x * x
		sumY2 += y * y
	}

	numerator := n*sumXY - sumX*sumY
	denominator := math.Sqrt((n*sumX2 - sumX*sumX) * (n*sumY2 - sumY*sumY))

	if denominator == 0 {
		return 0
	}

	return numerator / denominator
}

// analyzeCorrelations analyzes correlations between different metrics
func (ae *AnalyticsEngine) analyzeCorrelations() []*Insight {
	insights := make([]*Insight, 0)

	// Get all metric keys
	var metricKeys []string
	for key := range ae.metrics {
		metricKeys = append(metricKeys, key)
	}

	// Calculate correlations between pairs of metrics
	for i := 0; i < len(metricKeys)-1; i++ {
		for j := i + 1; j < len(metricKeys); j++ {
			key1, key2 := metricKeys[i], metricKeys[j]
			metric1, metric2 := ae.metrics[key1], ae.metrics[key2]

			if len(metric1.DataPoints) < 10 || len(metric2.DataPoints) < 10 {
				continue
			}

			correlation := ae.calculateCorrelation(metric1.DataPoints, metric2.DataPoints)
			if math.Abs(correlation) > 0.7 { // Strong correlation
				correlationType := "positive"
				if correlation < 0 {
					correlationType = "negative"
				}

				insight := &Insight{
					ID:             fmt.Sprintf("correlation-%s-%s-%d", key1, key2, time.Now().Unix()),
					Type:           "correlation",
					Title:          fmt.Sprintf("Strong %s correlation detected", correlationType),
					Description:    fmt.Sprintf("Strong %s correlation (%.2f) between %s and %s", correlationType, correlation, metric1.MetricName, metric2.MetricName),
					Severity:       "info",
					Timestamp:      time.Now(),
					RelatedMetrics: []string{metric1.MetricName, metric2.MetricName},
					Data: map[string]interface{}{
						"correlation_coefficient": correlation,
						"correlation_type":        correlationType,
					},
				}

				insights = append(insights, insight)
			}
		}
	}

	return insights
}

// calculateCorrelation calculates Pearson correlation coefficient between two time series
func (ae *AnalyticsEngine) calculateCorrelation(data1, data2 []DataPoint) float64 {
	if len(data1) != len(data2) || len(data1) < 2 {
		return 0
	}

	// Simple approach: align by time and calculate correlation
	values1 := make([]float64, 0, len(data1))
	values2 := make([]float64, 0, len(data2))

	// For simplicity, assume same timestamps and equal length
	for i := 0; i < len(data1) && i < len(data2); i++ {
		values1 = append(values1, data1[i].Value)
		values2 = append(values2, data2[i].Value)
	}

	return ae.calculatePearsonCorrelation(values1, values2)
}

// calculatePearsonCorrelation calculates Pearson correlation coefficient
func (ae *AnalyticsEngine) calculatePearsonCorrelation(x, y []float64) float64 {
	if len(x) != len(y) || len(x) < 2 {
		return 0
	}

	n := float64(len(x))
	sumX, sumY, sumXY, sumX2, sumY2 := 0.0, 0.0, 0.0, 0.0, 0.0

	for i := 0; i < len(x); i++ {
		sumX += x[i]
		sumY += y[i]
		sumXY += x[i] * y[i]
		sumX2 += x[i] * x[i]
		sumY2 += y[i] * y[i]
	}

	numerator := n*sumXY - sumX*sumY
	denominator := math.Sqrt((n*sumX2 - sumX*sumX) * (n*sumY2 - sumY*sumY))

	if denominator == 0 {
		return 0
	}

	return numerator / denominator
}

// AnalyticsActivity is a Temporal activity for analytics operations
func AnalyticsActivity(ctx context.Context, operation string, parameters map[string]interface{}) (interface{}, error) {
	switch operation {
	case "record_metric":
		metric := &Metric{}
		if data, ok := parameters["metric"].(map[string]interface{}); ok {
			metric.Name = data["name"].(string)
			metric.Type = MetricType(data["type"].(string))
			metric.Value = data["value"].(float64)
			if labels, ok := data["labels"].(map[string]interface{}); ok {
				metric.Labels = make(map[string]string)
				for k, v := range labels {
					metric.Labels[k] = v.(string)
				}
			}
			metric.Timestamp = time.Now()
		}
		GlobalAnalyticsEngine.RecordMetric(metric)
		return "metric recorded", nil

	case "get_anomalies":
		duration := 24 * time.Hour
		if d, ok := parameters["duration_hours"].(float64); ok {
			duration = time.Duration(d) * time.Hour
		}
		severity := ""
		if s, ok := parameters["severity"].(string); ok {
			severity = s
		}
		anomalies := GlobalAnalyticsEngine.GetAnomalies(severity, duration)
		return anomalies, nil

	case "get_insights":
		duration := 24 * time.Hour
		if d, ok := parameters["duration_hours"].(float64); ok {
			duration = time.Duration(d) * time.Hour
		}
		insightType := ""
		if t, ok := parameters["type"].(string); ok {
			insightType = t
		}
		severity := ""
		if s, ok := parameters["severity"].(string); ok {
			severity = s
		}
		insights := GlobalAnalyticsEngine.GetInsights(insightType, severity, duration)
		return insights, nil

	case "generate_predictions":
		predictions := GlobalAnalyticsEngine.GeneratePredictiveInsights()
		return predictions, nil

	default:
		return nil, fmt.Errorf("unknown analytics operation: %s", operation)
	}
}

// AdvancedAnalyticsWorkflow is a Temporal workflow for advanced analytics
func AdvancedAnalyticsWorkflow(ctx workflow.Context, operation string, parameters map[string]interface{}) (interface{}, error) {
	ao := workflow.ActivityOptions{
		StartToCloseTimeout: 120 * time.Second,
		RetryPolicy: &temporal.RetryPolicy{
			InitialInterval:    time.Second,
			BackoffCoefficient: 2.0,
			MaximumInterval:    30 * time.Second,
			MaximumAttempts:    3,
		},
	}
	ctx = workflow.WithActivityOptions(ctx, ao)

	var result interface{}
	err := workflow.ExecuteActivity(ctx, AnalyticsActivity, operation, parameters).Get(ctx, &result)
	if err != nil {
		return nil, err
	}

	workflow.GetLogger(ctx).Info("Analytics operation completed",
		"operation", operation,
		"result_type", fmt.Sprintf("%T", result))

	return result, nil
}

// Global analytics engine instance
var GlobalAnalyticsEngine *AnalyticsEngine

// InitAnalyticsEngine initializes the global analytics engine
func InitAnalyticsEngine(windowSize time.Duration) error {
	GlobalAnalyticsEngine = NewAnalyticsEngine(windowSize)
	return nil
}

// RecordMetric provides a simple interface for recording metrics
func RecordMetric(name string, value float64, labels map[string]string) {
	if GlobalAnalyticsEngine == nil {
		log.Printf("Analytics engine not initialized")
		return
	}

	metric := &Metric{
		Name:      name,
		Type:      MetricTypeGauge,
		Value:     value,
		Labels:    labels,
		Timestamp: time.Now(),
	}

	GlobalAnalyticsEngine.RecordMetric(metric)
}

// GetAnalyticsReport generates a comprehensive analytics report
func GetAnalyticsReport(duration time.Duration) map[string]interface{} {
	if GlobalAnalyticsEngine == nil {
		return nil
	}

	report := map[string]interface{}{
		"timestamp": time.Now(),
		"period":    duration.String(),
		"summary": map[string]interface{}{
			"total_metrics":    len(GlobalAnalyticsEngine.metrics),
			"total_anomalies":  len(GlobalAnalyticsEngine.anomalies),
			"total_trends":     len(GlobalAnalyticsEngine.trends),
			"total_insights":   len(GlobalAnalyticsEngine.insights),
		},
		"anomalies": GlobalAnalyticsEngine.GetAnomalies("", duration),
		"trends":    GlobalAnalyticsEngine.GetTrends(duration),
		"insights":  GlobalAnalyticsEngine.GetInsights("", "", duration),
	}

	// Generate predictive insights
	predictions := GlobalAnalyticsEngine.GeneratePredictiveInsights()
	report["predictions"] = predictions

	return report
}
