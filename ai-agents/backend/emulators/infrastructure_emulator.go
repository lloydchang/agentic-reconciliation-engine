package emulators

import (
	"context"
	"fmt"
	"math/rand"
	"sync"
	"time"
)

// InfrastructureEmulator provides safe simulation of cloud resources
type InfrastructureEmulator struct {
	resources map[string]*EmulatedResource
	mu        sync.RWMutex
}

type EmulatedResource struct {
	ID           string                 `json:"id"`
	Type         string                 `json:"type"`
	Name         string                 `json:"name"`
	Region       string                 `json:"region"`
	Status       string                 `json:"status"`
	Properties   map[string]interface{} `json:"properties"`
	Tags         map[string]string      `json:"tags"`
	CreatedAt    time.Time              `json:"createdAt"`
	UpdatedAt    time.Time              `json:"updatedAt"`
	Metrics      ResourceMetrics        `json:"metrics"`
}

type ResourceMetrics struct {
	CPUUtilization    float64 `json:"cpuUtilization"`
	MemoryUtilization float64 `json:"memoryUtilization"`
	DiskUtilization   float64 `json:"diskUtilization"`
	NetworkIn         float64 `json:"networkIn"`
	NetworkOut        float64 `json:"networkOut"`
	LastUpdated       time.Time `json:"lastUpdated"`
}

type CloudProvider string

const (
	AWS   CloudProvider = "aws"
	Azure CloudProvider = "azure"
	GCP   CloudProvider = "gcp"
)

type EmulatorConfig struct {
	Provider    CloudProvider `json:"provider"`
	Region      string        `json:"region"`
	Environment string        `json:"environment"`
}

// NewInfrastructureEmulator creates a new emulator instance
func NewInfrastructureEmulator(config EmulatorConfig) *InfrastructureEmulator {
	emulator := &InfrastructureEmulator{
		resources: make(map[string]*EmulatedResource),
	}
	
	// Initialize with some sample resources
	emulator.initializeSampleResources(config)
	
	return emulator
}

// Initialize sample resources for demonstration
func (e *InfrastructureEmulator) initializeSampleResources(config EmulatorConfig) {
	sampleResources := []EmulatedResource{
		{
			ID:     "vm-web-server-001",
			Type:   "VirtualMachine",
			Name:   "web-server-prod-001",
			Region: config.Region,
			Status: "Running",
			Properties: map[string]interface{}{
				"cpu":    4,
				"memory": 16,
				"storage": 100,
				"os":      "ubuntu-20.04",
			},
			Tags: map[string]string{
				"environment": "production",
				"owner":       "web-team",
				"cost-center": "engineering",
			},
			CreatedAt: time.Now().Add(-24 * time.Hour),
			UpdatedAt: time.Now(),
		},
		{
			ID:     "db-postgres-001",
			Type:   "Database",
			Name:   "postgres-prod-001",
			Region: config.Region,
			Status: "Running",
			Properties: map[string]interface{}{
				"engine":      "postgresql",
				"version":     "13.7",
				"storage":     500,
				"instanceType": "db.m5.large",
			},
			Tags: map[string]string{
				"environment": "production",
				"owner":       "data-team",
				"backup":      "enabled",
			},
			CreatedAt: time.Now().Add(-48 * time.Hour),
			UpdatedAt: time.Now(),
		},
		{
			ID:     "storage-bucket-001",
			Type:   "Storage",
			Name:   "app-assets-prod",
			Region: config.Region,
			Status: "Active",
			Properties: map[string]interface{}{
				"storageClass": "standard",
				"size":         250.5,
				"objects":      15420,
				"versioning":   true,
			},
			Tags: map[string]string{
				"environment": "production",
				"owner":       "platform-team",
				"retention":   "30-days",
			},
			CreatedAt: time.Now().Add(-72 * time.Hour),
			UpdatedAt: time.Now(),
		},
	}

	for i := range sampleResources {
		sampleResources[i].Metrics = e.generateRandomMetrics()
		e.resources[sampleResources[i].ID] = &sampleResources[i]
	}
}

// Generate random metrics for realistic simulation
func (e *InfrastructureEmulator) generateRandomMetrics() ResourceMetrics {
	return ResourceMetrics{
		CPUUtilization:    20.0 + rand.Float64()*60.0, // 20-80%
		MemoryUtilization: 30.0 + rand.Float64()*50.0, // 30-80%
		DiskUtilization:   10.0 + rand.Float64()*70.0, // 10-80%
		NetworkIn:         rand.Float64() * 1000.0,    // 0-1000 MB/s
		NetworkOut:        rand.Float64() * 800.0,     // 0-800 MB/s
		LastUpdated:       time.Now(),
	}
}

// Emulator Activities

func (e *InfrastructureEmulator) ListResources(ctx context.Context, resourceType string) ([]EmulatedResource, error) {
	e.mu.RLock()
	defer e.mu.RUnlock()

	var resources []EmulatedResource
	for _, resource := range e.resources {
		if resourceType == "" || resource.Type == resourceType {
			resources = append(resources, *resource)
		}
	}

	return resources, nil
}

func (e *InfrastructureEmulator) GetResource(ctx context.Context, resourceID string) (*EmulatedResource, error) {
	e.mu.RLock()
	defer e.mu.RUnlock()

	resource, exists := e.resources[resourceID]
	if !exists {
		return nil, fmt.Errorf("resource %s not found", resourceID)
	}

	// Update metrics for realistic simulation
	resource.Metrics = e.generateRandomMetrics()
	resource.UpdatedAt = time.Now()

	return resource, nil
}

func (e *InfrastructureEmulator) CreateResource(ctx context.Context, resource EmulatedResource) (*EmulatedResource, error) {
	e.mu.Lock()
	defer e.mu.Unlock()

	// Check if resource already exists
	if _, exists := e.resources[resource.ID]; exists {
		return nil, fmt.Errorf("resource %s already exists", resource.ID)
	}

	// Set timestamps and initial state
	resource.CreatedAt = time.Now()
	resource.UpdatedAt = time.Now()
	resource.Status = "Creating"
	resource.Metrics = e.generateRandomMetrics()

	// Simulate resource creation time
	go func() {
		time.Sleep(time.Second * 3)
		e.mu.Lock()
		if existing, exists := e.resources[resource.ID]; exists {
			existing.Status = "Running"
			existing.UpdatedAt = time.Now()
		}
		e.mu.Unlock()
	}()

	e.resources[resource.ID] = &resource
	return &resource, nil
}

func (e *InfrastructureEmulator) UpdateResource(ctx context.Context, resourceID string, updates map[string]interface{}) (*EmulatedResource, error) {
	e.mu.Lock()
	defer e.mu.Unlock()

	resource, exists := e.resources[resourceID]
	if !exists {
		return nil, fmt.Errorf("resource %s not found", resourceID)
	}

	// Apply updates
	for key, value := range updates {
		switch key {
		case "status":
			resource.Status = value.(string)
		case "properties":
			if props, ok := value.(map[string]interface{}); ok {
				for k, v := range props {
					resource.Properties[k] = v
				}
			}
		case "tags":
			if tags, ok := value.(map[string]string); ok {
				for k, v := range tags {
					resource.Tags[k] = v
				}
			}
		}
	}

	resource.UpdatedAt = time.Now()
	resource.Metrics = e.generateRandomMetrics()

	return resource, nil
}

func (e *InfrastructureEmulator) DeleteResource(ctx context.Context, resourceID string) error {
	e.mu.Lock()
	defer e.mu.Unlock()

	resource, exists := e.resources[resourceID]
	if !exists {
		return fmt.Errorf("resource %s not found", resourceID)
	}

	// Simulate deletion process
	resource.Status = "Deleting"
	resource.UpdatedAt = time.Now()

	// Actually delete after delay
	go func() {
		time.Sleep(time.Second * 2)
		e.mu.Lock()
		delete(e.resources, resourceID)
		e.mu.Unlock()
	}()

	return nil
}

// Security and Compliance Emulation

func (e *InfrastructureEmulator) GetSecurityPosture(ctx context.Context, resourceID string) (SecurityPosture, error) {
	resource, err := e.GetResource(ctx, resourceID)
	if err != nil {
		return SecurityPosture{}, err
	}

	posture := SecurityPosture{
		ResourceID:    resourceID,
		OverallScore:  75.0 + rand.Float64()*20.0, // 75-95
		ScanDate:      time.Now(),
		Findings:      []SecurityFinding{},
	}

	// Generate realistic security findings
	if resource.Properties["cpu"].(float64) > 8 {
		posture.Findings = append(posture.Findings, SecurityFinding{
			Severity:    "Medium",
			Category:     "Resource Configuration",
			Description:  "High CPU resources may indicate over-provisioning",
			Recommendation: "Consider right-sizing resources",
		})
	}

	if _, hasEncryption := resource.Tags["encryption"]; !hasEncryption {
		posture.Findings = append(posture.Findings, SecurityFinding{
			Severity:    "High",
			Category:     "Data Protection",
			Description:  "Encryption not explicitly configured",
			Recommendation: "Enable encryption at rest and in transit",
		})
	}

	return posture, nil
}

func (e *InfrastructureEmulator) GetComplianceStatus(ctx context.Context, resourceID string, standards []string) (ComplianceStatus, error) {
	_, err := e.GetResource(ctx, resourceID)
	if err != nil {
		return ComplianceStatus{}, err
	}

	status := ComplianceStatus{
		ResourceID: resourceID,
		Standards:  make(map[string]ComplianceResult),
		ScanDate:   time.Now(),
	}

	// Check compliance against each standard
	for _, standard := range standards {
		result := ComplianceResult{
			Standard:     standard,
			Status:       "Compliant",
			Score:        80.0 + rand.Float64()*15.0, // 80-95
			ControlsChecked: rand.Intn(50) + 20,      // 20-70 controls
			Exceptions:   []string{},
		}

		// Add some realistic exceptions
		if rand.Float32() > 0.7 {
			result.Exceptions = append(result.Exceptions, fmt.Sprintf("Control %s-001 requires manual verification", standard))
			result.Status = "Partially Compliant"
		}

		status.Standards[standard] = result
	}

	return status, nil
}

// Data Structures

type SecurityPosture struct {
	ResourceID   string            `json:"resourceId"`
	OverallScore float64           `json:"overallScore"`
	ScanDate     time.Time         `json:"scanDate"`
	Findings     []SecurityFinding `json:"findings"`
}

type SecurityFinding struct {
	Severity       string `json:"severity"`
	Category       string `json:"category"`
	Description    string `json:"description"`
	Recommendation string `json:"recommendation"`
}

type ComplianceStatus struct {
	ResourceID string                      `json:"resourceId"`
	Standards  map[string]ComplianceResult `json:"standards"`
	ScanDate   time.Time                   `json:"scanDate"`
}

type ComplianceResult struct {
	Standard       string   `json:"standard"`
	Status         string   `json:"status"`
	Score          float64  `json:"score"`
	ControlsChecked int     `json:"controlsChecked"`
	Exceptions     []string `json:"exceptions"`
}

// Global emulator instance
var globalEmulator *InfrastructureEmulator

// GetGlobalEmulator returns the singleton emulator instance
func GetGlobalEmulator() *InfrastructureEmulator {
	if globalEmulator == nil {
		config := EmulatorConfig{
			Provider:    AWS,
			Region:      "us-west-2",
			Environment: "development",
		}
		globalEmulator = NewInfrastructureEmulator(config)
	}
	return globalEmulator
}
