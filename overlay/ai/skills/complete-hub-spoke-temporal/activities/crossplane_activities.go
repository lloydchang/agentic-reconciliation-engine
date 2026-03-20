package activities

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"go.temporal.io/sdk/activity"
	"go.temporal.io/sdk/temporal"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/rest"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
)

// CrossplaneActivityConfig holds configuration for Crossplane activities
type CrossplaneActivityConfig struct {
	Namespace    string `json:"namespace"`
	APIGroup     string `json:"apiGroup"`
	APIVersion   string `json:"apiVersion"`
	Kubeconfig   string `json:"kubeconfig,omitempty"`
}

// CrossplaneResourceRequest represents a request to create Crossplane resources
type CrossplaneResourceRequest struct {
	ResourceType string                 `json:"resourceType"` // network, compute, storage, database
	Name        string                 `json:"name"`
	Provider    string                 `json:"provider"`    // aws, azure, gcp
	Spec        map[string]interface{}  `json:"spec"`
	Labels      map[string]string       `json:"labels,omitempty"`
}

// CrossplaneResourceResponse represents the response from Crossplane operations
type CrossplaneResourceResponse struct {
	Status    string                 `json:"status"`    // success, error, pending
	ResourceID string                 `json:"resourceId"`
	Message    string                 `json:"message"`
	Data       map[string]interface{}  `json:"data,omitempty"`
	Error      string                 `json:"error,omitempty"`
}

// CrossplaneActivities implements Crossplane-related Temporal activities
type CrossplaneActivities struct {
	config CrossplaneActivityConfig
	client *kubernetes.Clientset
}

// NewCrossplaneActivities creates a new CrossplaneActivities instance
func NewCrossplaneActivities(config CrossplaneActivityConfig) (*CrossplaneActivities, error) {
	// Initialize Kubernetes client
	var kubeConfig *rest.Config
	var err error
	
	if config.Kubeconfig != "" {
		kubeConfig, err = client.BuildConfigFromFlags("", config.Kubeconfig)
	} else {
		kubeConfig, err = rest.InClusterConfig()
	}
	
	if err != nil {
		return nil, fmt.Errorf("failed to create Kubernetes config: %w", err)
	}
	
	clientset, err := kubernetes.NewForConfig(kubeConfig)
	if err != nil {
		return nil, fmt.Errorf("failed to create Kubernetes client: %w", err)
	}
	
	return &CrossplaneActivities{
		config: config,
		client: clientset,
	}, nil
}

// ExecuteCrossplaneOperationActivity executes Crossplane operations
func (a *CrossplaneActivities) ExecuteCrossplaneOperationActivity(ctx context.Context, request CrossplaneResourceRequest) (CrossplaneResourceResponse, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Executing Crossplane operation",
		"resourceType", request.ResourceType,
		"name", request.Name,
		"provider", request.Provider,
	)

	// Determine resource kind and plural
	kind, plural := getResourceKindAndPlural(request.ResourceType)
	if kind == "" {
		return CrossplaneResourceResponse{
			Status: "error",
			Error:  fmt.Sprintf("unknown resource type: %s", request.ResourceType),
		}, nil
	}

	// Create the Crossplane resource manifest
	resource := &unstructured.Unstructured{
		Object: map[string]interface{}{
			"apiVersion": fmt.Sprintf("%s/%s", a.config.APIGroup, a.config.APIVersion),
			"kind":       kind,
			"metadata": map[string]interface{}{
				"name":   request.Name,
				"labels": request.Labels,
			},
			"spec": request.Spec,
		},
	}

	// Apply the resource using dynamic client
	dynamicClient, err := a.client.Discovery().RESTClient().(*rest.RESTClient).APIVersion().New(a.config.APIGroup)
	if err != nil {
		return CrossplaneResourceResponse{
			Status: "error",
			Error:  fmt.Sprintf("failed to create dynamic client: %v", err),
		}, nil
	}

	// Create the resource
	result, err := dynamicClient.Resource(
		&metav1.APIResource{
			Name:    plural,
			Group:   a.config.APIGroup,
			Version: a.config.APIVersion,
		},
		a.config.Namespace,
	).Create(ctx, resource, metav1.CreateOptions{})

	if err != nil {
		logger.Error("Failed to create Crossplane resource", "error", err)
		return CrossplaneResourceResponse{
			Status: "error",
			Error:  fmt.Sprintf("failed to create %s: %v", request.ResourceType, err),
		}, nil
	}

	logger.Info("Successfully created Crossplane resource",
		"resourceType", request.ResourceType,
		"name", request.Name,
		"resourceId", result.GetName(),
	)

	return CrossplaneResourceResponse{
		Status:     "success",
		ResourceID: result.GetName(),
		Message:    fmt.Sprintf("%s %s created successfully", kind, request.Name),
		Data: map[string]interface{}{
			"name":      result.GetName(),
			"namespace": result.GetNamespace(),
			"uid":       result.GetUID(),
		},
	}, nil
}

// GetCrossplaneResourceStatusActivity gets the status of a Crossplane resource
func (a *CrossplaneActivities) GetCrossplaneResourceStatusActivity(ctx context.Context, resourceType, resourceName string) (CrossplaneResourceResponse, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Getting Crossplane resource status",
		"resourceType", resourceType,
		"name", resourceName,
	)

	kind, plural := getResourceKindAndPlural(resourceType)
	if kind == "" {
		return CrossplaneResourceResponse{
			Status: "error",
			Error:  fmt.Sprintf("unknown resource type: %s", resourceType),
		}, nil
	}

	dynamicClient, err := a.client.Discovery().RESTClient().(*rest.RESTClient).APIVersion().New(a.config.APIGroup)
	if err != nil {
		return CrossplaneResourceResponse{
			Status: "error",
			Error:  fmt.Sprintf("failed to create dynamic client: %v", err),
		}, nil
	}

	// Get the resource
	result, err := dynamicClient.Resource(
		&metav1.APIResource{
			Name:    plural,
			Group:   a.config.APIGroup,
			Version: a.config.APIVersion,
		},
		a.config.Namespace,
	).Get(ctx, resourceName, metav1.GetOptions{})

	if err != nil {
		logger.Error("Failed to get Crossplane resource", "error", err)
		return CrossplaneResourceResponse{
			Status: "error",
			Error:  fmt.Sprintf("failed to get %s %s: %v", resourceType, resourceName, err),
		}, nil
	}

	// Extract status information
	status, found, err := unstructured.NestedFieldCopy(result.Object, "status")
	if err != nil || !found {
		status = map[string]interface{}{}
	}

	logger.Info("Successfully retrieved Crossplane resource status",
		"resourceType", resourceType,
		"name", resourceName,
		"ready", isResourceReady(status),
	)

	return CrossplaneResourceResponse{
		Status: "success",
		Data: map[string]interface{}{
			"name":   result.GetName(),
			"status": status,
			"ready":  isResourceReady(status),
		},
		Message: fmt.Sprintf("Retrieved status for %s %s", kind, resourceName),
	}, nil
}

// DeleteCrossplaneResourceActivity deletes a Crossplane resource
func (a *CrossplaneActivities) DeleteCrossplaneResourceActivity(ctx context.Context, resourceType, resourceName string) (CrossplaneResourceResponse, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Deleting Crossplane resource",
		"resourceType", resourceType,
		"name", resourceName,
	)

	kind, plural := getResourceKindAndPlural(resourceType)
	if kind == "" {
		return CrossplaneResourceResponse{
			Status: "error",
			Error:  fmt.Sprintf("unknown resource type: %s", resourceType),
		}, nil
	}

	dynamicClient, err := a.client.Discovery().RESTClient().(*rest.RESTClient).APIVersion().New(a.config.APIGroup)
	if err != nil {
		return CrossplaneResourceResponse{
			Status: "error",
			Error:  fmt.Sprintf("failed to create dynamic client: %v", err),
		}, nil
	}

	// Delete the resource
	err = dynamicClient.Resource(
		&metav1.APIResource{
			Name:    plural,
			Group:   a.config.APIGroup,
			Version: a.config.APIVersion,
		},
		a.config.Namespace,
	).Delete(ctx, resourceName, metav1.DeleteOptions{})

	if err != nil {
		logger.Error("Failed to delete Crossplane resource", "error", err)
		return CrossplaneResourceResponse{
			Status: "error",
			Error:  fmt.Sprintf("failed to delete %s %s: %v", resourceType, resourceName, err),
		}, nil
	}

	logger.Info("Successfully deleted Crossplane resource",
		"resourceType", resourceType,
		"name", resourceName,
	)

	return CrossplaneResourceResponse{
		Status:  "success",
		Message: fmt.Sprintf("%s %s deleted successfully", kind, resourceName),
	}, nil
}

// ListCrossplaneResourcesActivity lists Crossplane resources of a specific type
func (a *CrossplaneActivities) ListCrossplaneResourcesActivity(ctx context.Context, resourceType string) (CrossplaneResourceResponse, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Listing Crossplane resources",
		"resourceType", resourceType,
	)

	kind, plural := getResourceKindAndPlural(resourceType)
	if kind == "" {
		return CrossplaneResourceResponse{
			Status: "error",
			Error:  fmt.Sprintf("unknown resource type: %s", resourceType),
		}, nil
	}

	dynamicClient, err := a.client.Discovery().RESTClient().(*rest.RESTClient).APIVersion().New(a.config.APIGroup)
	if err != nil {
		return CrossplaneResourceResponse{
			Status: "error",
			Error:  fmt.Sprintf("failed to create dynamic client: %v", err),
		}, nil
	}

	// List the resources
	result, err := dynamicClient.Resource(
		&metav1.APIResource{
			Name:    plural,
			Group:   a.config.APIGroup,
			Version: a.config.APIVersion,
		},
		a.config.Namespace,
	).List(ctx, metav1.ListOptions{})

	if err != nil {
		logger.Error("Failed to list Crossplane resources", "error", err)
		return CrossplaneResourceResponse{
			Status: "error",
			Error:  fmt.Sprintf("failed to list %s: %v", resourceType, err),
		}, nil
	}

	// Convert items to a more readable format
	items := make([]map[string]interface{}, len(result.Items))
	for i, item := range result.Items {
		items[i] = item.Object
	}

	logger.Info("Successfully listed Crossplane resources",
		"resourceType", resourceType,
		"count", len(result.Items),
	)

	return CrossplaneResourceResponse{
		Status: "success",
		Data: map[string]interface{}{
			"items": items,
			"count": len(result.Items),
		},
		Message: fmt.Sprintf("Listed %d %s resources", len(result.Items), resourceType),
	}, nil
}

// Helper functions

// getResourceKindAndPlural returns the Kubernetes kind and plural for a resource type
func getResourceKindAndPlural(resourceType string) (kind, plural string) {
	switch resourceType {
	case "network":
		return "XNetwork", "xnetworks"
	case "compute":
		return "XCompute", "xcomputes"
	case "storage":
		return "XStorage", "xstorages"
	case "database":
		return "XDatabase", "xdatabases"
	default:
		return "", ""
	}
}

// isResourceReady checks if a Crossplane resource is ready based on its status
func isResourceReady(status interface{}) bool {
	statusMap, ok := status.(map[string]interface{})
	if !ok {
		return false
	}

	ready, found := statusMap["ready"]
	if !found {
		return false
	}

	readyBool, ok := ready.(bool)
	return ok && readyBool
}

// WaitForCrossplaneResourceReadyActivity waits for a Crossplane resource to become ready
func (a *CrossplaneActivities) WaitForCrossplaneResourceReadyActivity(ctx context.Context, resourceType, resourceName string, timeout time.Duration) (CrossplaneResourceResponse, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Waiting for Crossplane resource to become ready",
		"resourceType", resourceType,
		"name", resourceName,
		"timeout", timeout,
	)

	deadline := time.Now().Add(timeout)
	ticker := time.NewTicker(10 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return CrossplaneResourceResponse{
				Status: "error",
				Error:  "context cancelled while waiting for resource to become ready",
			}, ctx.Err()
		case <-ticker.C:
			// Check resource status
			response, err := a.GetCrossplaneResourceStatusActivity(ctx, resourceType, resourceName)
			if err != nil {
				return CrossplaneResourceResponse{
					Status: "error",
					Error:  fmt.Sprintf("failed to check resource status: %v", err),
				}, nil
			}

			if response.Status == "success" {
				if ready, ok := response.Data["ready"].(bool); ok && ready {
					logger.Info("Crossplane resource is ready",
						"resourceType", resourceType,
						"name", resourceName,
					)
					return CrossplaneResourceResponse{
						Status:  "success",
						Message: fmt.Sprintf("%s %s is ready", resourceType, resourceName),
						Data:    response.Data,
					}, nil
				}
			}

			// Check timeout
			if time.Now().After(deadline) {
				return CrossplaneResourceResponse{
					Status: "error",
					Error:  fmt.Sprintf("timeout waiting for %s %s to become ready", resourceType, resourceName),
				}, nil
			}
		}
	}
}
