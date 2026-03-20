package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"strings"
	"time"

	"github.com/gorilla/mux"
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/rest"
)

// AgentInfo represents information about a discovered agent
type AgentInfo struct {
	Name         string            `json:"name"`
	Service      string            `json:"service"`
	Port         int               `json:"port"`
	Endpoints    []string          `json:"endpoints"`
	Capabilities []string          `json:"capabilities"`
	Labels       map[string]string `json:"labels"`
	Status       string            `json:"status"`
	LastSeen     time.Time         `json:"last_seen"`
}

// ServiceMeshDiscovery handles agent discovery and service mesh coordination
type ServiceMeshDiscovery struct {
	k8sClient *kubernetes.Clientset
	agents     map[string]*AgentInfo
	config     *ServiceMeshConfig
}

// ServiceMeshConfig holds service mesh configuration
type ServiceMeshConfig struct {
	Discovery struct {
		Type           string `yaml:"type"`
		Namespace      string `yaml:"namespace"`
		LabelSelector  string `yaml:"label_selector"`
		Port           int    `yaml:"port"`
		HealthCheck     struct {
			Path     string `yaml:"path"`
			Interval string `yaml:"interval"`
			Timeout  string `yaml:"timeout"`
		} `yaml:"health_check"`
	} `yaml:"discovery"`
}

func main() {
	// Load configuration
	config, err := loadConfig()
	if err != nil {
		log.Fatalf("Failed to load config: %v", err)
	}

	// Initialize Kubernetes client
	k8sConfig, err := rest.InClusterConfig()
	if err != nil {
		log.Fatalf("Failed to get in-cluster config: %v", err)
	}

	k8sClient, err := kubernetes.NewForConfig(k8sConfig)
	if err != nil {
		log.Fatalf("Failed to create kubernetes client: %v", err)
	}

	// Initialize service mesh discovery
	smd := &ServiceMeshDiscovery{
		k8sClient: k8sClient,
		agents:     make(map[string]*AgentInfo),
		config:     config,
	}

	// Start background discovery
	go smd.startDiscovery()

	// Setup HTTP server
	router := mux.NewRouter()
	
	// Health check endpoint
	router.HandleFunc("/health", smd.healthHandler).Methods("GET")
	router.HandleFunc("/ready", smd.readyHandler).Methods("GET")
	
	// Discovery endpoints
	router.HandleFunc("/api/v1/agents", smd.listAgentsHandler).Methods("GET")
	router.HandleFunc("/api/v1/agents/{name}", smd.getAgentHandler).Methods("GET")
	router.HandleFunc("/api/v1/discover", smd.discoverHandler).Methods("POST")
	
	// Metrics endpoint
	router.HandleFunc("/metrics", smd.metricsHandler).Methods("GET")

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	log.Printf("Starting service mesh discovery on port %s", port)
	log.Fatal(http.ListenAndServe(":"+port, router))
}

func loadConfig() (*ServiceMeshConfig, error) {
	configPath := "/etc/service-mesh/config.yaml"
	if _, err := os.Stat(configPath); os.IsNotExist(err) {
		// Return default config if file doesn't exist
		return &ServiceMeshConfig{
			Discovery: struct {
				Type           string `yaml:"type"`
				Namespace      string `yaml:"namespace"`
				LabelSelector  string `yaml:"label_selector"`
				Port           int    `yaml:"port"`
				HealthCheck     struct {
					Path     string `yaml:"path"`
					Interval string `yaml:"interval"`
					Timeout  string `yaml:"timeout"`
				} `yaml:"health_check"`
			}{
				Type:          "kubernetes",
				Namespace:     "ai-infrastructure",
				LabelSelector: "app.kubernetes.io/part-of=agent",
				Port:          8080,
				HealthCheck: struct {
					Path     string `yaml:"path"`
					Interval string `yaml:"interval"`
					Timeout  string `yaml:"timeout"`
				}{
					Path:     "/health",
					Interval: "30s",
					Timeout:  "5s",
				},
			},
		}, nil
	}

	// TODO: Parse YAML config file
	return &ServiceMeshConfig{}, nil
}

func (smd *ServiceMeshDiscovery) startDiscovery() {
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()

	for range ticker.C {
		smd.discoverAgents()
	}
}

func (smd *ServiceMeshDiscovery) discoverAgents() {
	services, err := smd.k8sClient.CoreV1().Services(smd.config.Discovery.Namespace).List(context.TODO(), metav1.ListOptions{
		LabelSelector: smd.config.Discovery.LabelSelector,
	})
	if err != nil {
		log.Printf("Failed to list services: %v", err)
		return
	}

	for _, svc := range services.Items {
		if strings.HasPrefix(svc.Name, "service-mesh") {
			continue // Skip service mesh services
		}

		agentInfo := &AgentInfo{
			Name:      svc.Name,
			Service:   svc.Name,
			Port:      int(svc.Spec.Ports[0].Port),
			Labels:    svc.Labels,
			Status:    "discovered",
			LastSeen:  time.Now(),
		}

		// Get endpoints for more detailed info
		endpoints, err := smd.k8sClient.CoreV1().Endpoints(smd.config.Discovery.Namespace).Get(context.TODO(), svc.Name, metav1.GetOptions{})
		if err == nil && len(endpoints.Subsets) > 0 {
			agentInfo.Status = "healthy"
		}

		smd.agents[svc.Name] = agentInfo
		log.Printf("Discovered agent: %s at %s:%d", svc.Name, svc.Spec.ClusterIP, agentInfo.Port)
	}
}

func (smd *ServiceMeshDiscovery) healthHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "healthy"})
}

func (smd *ServiceMeshDiscovery) readyHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "ready"})
}

func (smd *ServiceMeshDiscovery) listAgentsHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	
	agents := make([]*AgentInfo, 0, len(smd.agents))
	for _, agent := range smd.agents {
		agents = append(agents, agent)
	}
	
	json.NewEncoder(w).Encode(agents)
}

func (smd *ServiceMeshDiscovery) getAgentHandler(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	name := vars["name"]
	
	agent, exists := smd.agents[name]
	if !exists {
		http.NotFound(w, r)
		return
	}
	
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(agent)
}

func (smd *ServiceMeshDiscovery) discoverHandler(w http.ResponseWriter, r *http.Request) {
	// Trigger immediate discovery
	smd.discoverAgents()
	
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "discovery_triggered"})
}

func (smd *ServiceMeshDiscovery) metricsHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "text/plain")
	
	metrics := fmt.Sprintf(`
# HELP service_mesh_agents_total Total number of discovered agents
# TYPE service_mesh_agents_total gauge
service_mesh_agents_total %d

# HELP service_mesh_discovery_last_success_timestamp Last successful discovery timestamp
# TYPE service_mesh_discovery_last_success_timestamp gauge
service_mesh_discovery_last_success_timestamp %d
`, len(smd.agents), time.Now().Unix())

	w.Write([]byte(metrics))
}
