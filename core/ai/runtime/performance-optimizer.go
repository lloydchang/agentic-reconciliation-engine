package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"strconv"
	"time"

	"github.com/go-redis/redis/v8"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

type CacheManager struct {
	redis  *redis.Client
	ttl    time.Duration
	hits   prometheus.Counter
	misses prometheus.Counter
}

type CacheEntry struct {
	Data      interface{} `json:"data"`
	Timestamp time.Time   `json:"timestamp"`
	Version   string      `json:"version"`
}

func NewCacheManager(redisAddr string, ttl time.Duration) *CacheManager {
	rdb := redis.NewClient(&redis.Options{
		Addr: redisAddr,
	})

	// Test connection
	ctx := context.Background()
	_, err := rdb.Ping(ctx).Result()
	if err != nil {
		log.Printf("Failed to connect to Redis: %v", err)
		return nil
	}

	hits := prometheus.NewCounter(prometheus.CounterOpts{
		Name: "cache_hits_total",
		Help: "Total number of cache hits",
	})

	misses := prometheus.NewCounter(prometheus.CounterOpts{
		Name: "cache_misses_total",
		Help: "Total number of cache misses",
	})

	prometheus.MustRegister(hits, misses)

	return &CacheManager{
		redis:  rdb,
		ttl:    ttl,
		hits:   hits,
		misses: misses,
	}
}

func (cm *CacheManager) Get(ctx context.Context, key string) (interface{}, bool) {
	val, err := cm.redis.Get(ctx, key).Result()
	if err == redis.Nil {
		cm.misses.Inc()
		return nil, false
	} else if err != nil {
		log.Printf("Cache get error: %v", err)
		return nil, false
	}

	var entry CacheEntry
	if err := json.Unmarshal([]byte(val), &entry); err != nil {
		log.Printf("Cache unmarshal error: %v", err)
		return nil, false
	}

	// Check if entry is expired
	if time.Since(entry.Timestamp) > cm.ttl {
		cm.redis.Del(ctx, key)
		cm.misses.Inc()
		return nil, false
	}

	cm.hits.Inc()
	return entry.Data, true
}

func (cm *CacheManager) Set(ctx context.Context, key string, value interface{}) error {
	entry := CacheEntry{
		Data:      value,
		Timestamp: time.Now(),
		Version:   "1.0",
	}

	data, err := json.Marshal(entry)
	if err != nil {
		return fmt.Errorf("failed to marshal cache entry: %w", err)
	}

	return cm.redis.Set(ctx, key, data, cm.ttl).Err()
}

func (cm *CacheManager) InvalidatePattern(ctx context.Context, pattern string) error {
	keys, err := cm.redis.Keys(ctx, pattern).Result()
	if err != nil {
		return fmt.Errorf("failed to get keys for pattern %s: %w", pattern, err)
	}

	if len(keys) > 0 {
		return cm.redis.Del(ctx, keys...).Err()
	}

	return nil
}

func (cm *CacheManager) Health() error {
	ctx := context.Background()
	return cm.redis.Ping(ctx).Err()
}

type PerformanceOptimizer struct {
	cache   *CacheManager
	metrics *PerformanceMetrics
}

type PerformanceMetrics struct {
	RequestDuration prometheus.Histogram
	RequestCount    prometheus.Counter
	ErrorCount      prometheus.Counter
	ResourceUsage   prometheus.Gauge
}

func NewPerformanceOptimizer(redisAddr string) *PerformanceOptimizer {
	cache := NewCacheManager(redisAddr, 30*time.Minute)

	requestDuration := prometheus.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "http_request_duration_seconds",
			Help:    "Duration of HTTP requests in seconds",
			Buckets: prometheus.DefBuckets,
		},
		[]string{"method", "endpoint", "status"},
	)

	requestCount := prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "http_requests_total",
			Help: "Total number of HTTP requests",
		},
		[]string{"method", "endpoint", "status"},
	)

	errorCount := prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "http_errors_total",
			Help: "Total number of HTTP errors",
		},
		[]string{"method", "endpoint", "error_type"},
	)

	resourceUsage := prometheus.NewGaugeVec(
		prometheus.GaugeOpts{
			Name: "resource_usage_percent",
			Help: "Resource usage percentage",
		},
		[]string{"resource_type"},
	)

	prometheus.MustRegister(requestDuration, requestCount, errorCount, resourceUsage)

	metrics := &PerformanceMetrics{
		RequestDuration: requestDuration,
		RequestCount:    requestCount,
		ErrorCount:      errorCount,
		ResourceUsage:   resourceUsage,
	}

	return &PerformanceOptimizer{
		cache:   cache,
		metrics: metrics,
	}
}

func (po *PerformanceOptimizer) CachedHandler(cacheKey string, handler func() (interface{}, error)) (interface{}, error) {
	ctx := context.Background()

	// Try to get from cache first
	if cached, found := po.cache.Get(ctx, cacheKey); found {
		return cached, nil
	}

	// Execute handler
	result, err := handler()
	if err != nil {
		return nil, err
	}

	// Cache the result
	if cacheErr := po.cache.Set(ctx, cacheKey, result); cacheErr != nil {
		log.Printf("Failed to cache result for key %s: %v", cacheKey, cacheErr)
	}

	return result, nil
}

func (po *PerformanceOptimizer) InstrumentHandler(method, endpoint string, handler http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()

		// Create a response writer wrapper to capture status code
		rw := &responseWriter{ResponseWriter: w, statusCode: http.StatusOK}

		// Call the original handler
		handler(rw, r)

		duration := time.Since(start)

		// Record metrics
		statusStr := strconv.Itoa(rw.statusCode)
		po.metrics.RequestDuration.WithLabelValues(method, endpoint, statusStr).Observe(duration.Seconds())
		po.metrics.RequestCount.WithLabelValues(method, endpoint, statusStr).Inc()

		if rw.statusCode >= 400 {
			errorType := "client_error"
			if rw.statusCode >= 500 {
				errorType = "server_error"
			}
			po.metrics.ErrorCount.WithLabelValues(method, endpoint, errorType).Inc()
		}
	}
}

type responseWriter struct {
	http.ResponseWriter
	statusCode int
}

func (rw *responseWriter) WriteHeader(code int) {
	rw.statusCode = code
	rw.ResponseWriter.WriteHeader(code)
}

func main() {
	redisAddr := os.Getenv("REDIS_ADDR")
	if redisAddr == "" {
		redisAddr = "localhost:6379"
	}

	optimizer := NewPerformanceOptimizer(redisAddr)

	http.HandleFunc("/health", optimizer.InstrumentHandler("GET", "/health", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("OK"))
	}))

	http.HandleFunc("/metrics", optimizer.InstrumentHandler("GET", "/metrics", promhttp.Handler().ServeHTTP))

	// Example cached endpoint
	http.HandleFunc("/cached-data", optimizer.InstrumentHandler("GET", "/cached-data", func(w http.ResponseWriter, r *http.Request) {
		result, err := optimizer.CachedHandler("example-data", func() (interface{}, error) {
			// Simulate expensive operation
			time.Sleep(100 * time.Millisecond)
			return map[string]string{"data": "cached value", "timestamp": time.Now().Format(time.RFC3339)}, nil
		})

		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(result)
	}))

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	log.Printf("Starting performance optimizer on port %s", port)
	log.Fatal(http.ListenAndServe(":"+port, nil))
}
