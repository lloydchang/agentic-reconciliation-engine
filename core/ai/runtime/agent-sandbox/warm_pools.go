package agent_sandbox

import (
	"context"
	"fmt"
	"log"
	"time"

	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/util/intstr"
	agentsv1alpha1 "github.com/kubernetes-sigs/agent-sandbox/pkg/apis/agents/v1alpha1"
	agentsclient "github.com/kubernetes-sigs/agent-sandbox/pkg/client/clientset/versioned"
	"github.com/agentic-reconciliation-engine/openswe-orchestrator/pkg/config"
)

// WarmPoolManager manages sandbox warm pools
type WarmPoolManager struct {
	spec         *config.WarmPoolSpec
	config       *config.AgentSandboxConfig
	agentsClient agentsclient.Interface
}

// NewWarmPoolManager creates a new warm pool manager
func NewWarmPoolManager(spec *config.WarmPoolSpec, config *config.AgentSandboxConfig) *WarmPoolManager {
	return &WarmPoolManager{
		spec:   spec,
		config: config,
	}
}

// Create creates the warm pool in Kubernetes
func (wpm *WarmPoolManager) Create(ctx context.Context) error {
	if wpm.config.Kubeconfig == nil {
		return fmt.Errorf("kubeconfig not available")
	}

	agentsClient, err := agentsclient.NewForConfig(wpm.config.Kubeconfig)
	if err != nil {
		return fmt.Errorf("failed to create agents client: %w", err)
	}
	wpm.agentsClient = agentsClient

	// Create SandboxWarmPool
	warmPool := &agentsv1alpha1.SandboxWarmPool{
		ObjectMeta: metav1.ObjectMeta{
			Name:      wpm.spec.Name,
			Namespace: wpm.config.DefaultNamespace,
		},
		Spec: agentsv1alpha1.SandboxWarmPoolSpec{
			Replicas: wpm.spec.Replicas,
			SandboxTemplateRef: agentsv1alpha1.SandboxTemplateRef{
				Name: wpm.spec.TemplateName,
			},
		},
	}

	// Add minReady field if specified
	if wpm.spec.MinReady > 0 {
		warmPool.Spec.MinReady = &wpm.spec.MinReady
	}

	_, err = wpm.agentsClient.AgentsV1alpha1().SandboxWarmPools(wpm.config.DefaultNamespace).Create(ctx, warmPool, metav1.CreateOptions{})
	if err != nil {
		return fmt.Errorf("failed to create SandboxWarmPool %s: %w", wpm.spec.Name, err)
	}

	log.Printf("Created SandboxWarmPool: %s (template: %s, replicas: %d)", 
		wpm.spec.Name, wpm.spec.TemplateName, wpm.spec.Replicas)
	return nil
}

// Update updates the warm pool
func (wpm *WarmPoolManager) Update(ctx context.Context) error {
	if wpm.agentsClient == nil {
		return fmt.Errorf("agents client not initialized")
	}

	// Get existing warm pool
	existing, err := wpm.agentsClient.AgentsV1alpha1().SandboxWarmPools(wpm.config.DefaultNamespace).Get(ctx, wpm.spec.Name, metav1.GetOptions{})
	if err != nil {
		return fmt.Errorf("failed to get existing warm pool: %w", err)
	}

	// Update spec
	existing.Spec.Replicas = wpm.spec.Replicas
	existing.Spec.SandboxTemplateRef.Name = wpm.spec.TemplateName

	if wpm.spec.MinReady > 0 {
		existing.Spec.MinReady = &wpm.spec.MinReady
	}

	_, err = wpm.agentsClient.AgentsV1alpha1().SandboxWarmPools(wpm.config.DefaultNamespace).Update(ctx, existing, metav1.UpdateOptions{})
	if err != nil {
		return fmt.Errorf("failed to update SandboxWarmPool %s: %w", wpm.spec.Name, err)
	}

	log.Printf("Updated SandboxWarmPool: %s", wpm.spec.Name)
	return nil
}

// Delete deletes the warm pool
func (wpm *WarmPoolManager) Delete(ctx context.Context) error {
	if wpm.agentsClient == nil {
		return fmt.Errorf("agents client not initialized")
	}

	err := wpm.agentsClient.AgentsV1alpha1().SandboxWarmPools(wpm.config.DefaultNamespace).Delete(ctx, wpm.spec.Name, metav1.DeleteOptions{})
	if err != nil {
		return fmt.Errorf("failed to delete SandboxWarmPool %s: %w", wpm.spec.Name, err)
	}

	log.Printf("Deleted SandboxWarmPool: %s", wpm.spec.Name)
	return nil
}

// GetStatus returns the status of the warm pool
func (wpm *WarmPoolManager) GetStatus(ctx context.Context) (*WarmPoolStatus, error) {
	if wpm.agentsClient == nil {
		return nil, fmt.Errorf("agents client not initialized")
	}

	warmPool, err := wpm.agentsClient.AgentsV1alpha1().SandboxWarmPools(wpm.config.DefaultNamespace).Get(ctx, wpm.spec.Name, metav1.GetOptions{})
	if err != nil {
		return nil, fmt.Errorf("failed to get warm pool status: %w", err)
	}

	status := &WarmPoolStatus{
		Name:         wpm.spec.Name,
		Template:     wpm.spec.TemplateName,
		Desired:      wpm.spec.Replicas,
		Ready:        0,
		Available:    0,
		LastUpdated:  time.Now(),
	}

	// Extract status information
	if warmPool.Status.ReadyReplicas != nil {
		status.Ready = *warmPool.Status.ReadyReplicas
	}
	if warmPool.Status.AvailableReplicas != nil {
		status.Available = *warmPool.Status.AvailableReplicas
	}

	return status, nil
}

// Scale scales the warm pool to the desired number of replicas
func (wpm *WarmPoolManager) Scale(ctx context.Context, replicas int32) error {
	if wpm.agentsClient == nil {
		return fmt.Errorf("agents client not initialized")
	}

	// Get existing warm pool
	existing, err := wpm.agentsClient.AgentsV1alpha1().SandboxWarmPools(wpm.config.DefaultNamespace).Get(ctx, wpm.spec.Name, metav1.GetOptions{})
	if err != nil {
		return fmt.Errorf("failed to get existing warm pool: %w", err)
	}

	// Update replicas
	existing.Spec.Replicas = replicas

	_, err = wpm.agentsClient.AgentsV1alpha1().SandboxWarmPools(wpm.config.DefaultNamespace).Update(ctx, existing, metav1.UpdateOptions{})
	if err != nil {
		return fmt.Errorf("failed to scale SandboxWarmPool %s: %w", wpm.spec.Name, err)
	}

	log.Printf("Scaled SandboxWarmPool %s to %d replicas", wpm.spec.Name, replicas)
	return nil
}

// WaitForReady waits for the warm pool to be ready
func (wpm *WarmPoolManager) WaitForReady(ctx context.Context, timeout time.Duration) error {
	deadline := time.After(timeout)
	ticker := time.NewTicker(5 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return fmt.Errorf("context cancelled while waiting for warm pool to be ready")
		case <-deadline:
			return fmt.Errorf("timeout waiting for warm pool to be ready")
		case <-ticker.C:
			status, err := wpm.GetStatus(ctx)
			if err != nil {
				log.Printf("Error getting warm pool status: %v", err)
				continue
			}

			if status.Ready >= wpm.spec.MinReady {
				log.Printf("Warm pool %s is ready with %d/%d replicas", 
					wpm.spec.Name, status.Ready, wpm.spec.Replicas)
				return nil
			}

			log.Printf("Warm pool %s status: %d/%d ready", 
				wpm.spec.Name, status.Ready, wpm.spec.Replicas)
		}
	}
}

// GetSpec returns the warm pool specification
func (wpm *WarmPoolManager) GetSpec() *config.WarmPoolSpec {
	return wpm.spec
}

// WarmPoolStatus represents the status of a warm pool
type WarmPoolStatus struct {
	Name        string    `json:"name"`
	Template    string    `json:"template"`
	Desired     int32     `json:"desired"`
	Ready       int32     `json:"ready"`
	Available   int32     `json:"available"`
	LastUpdated time.Time `json:"last_updated"`
}

// Cleanup cleans up the warm pool manager
func (wpm *WarmPoolManager) Cleanup(ctx context.Context) error {
	if wpm.agentsClient != nil {
		return wpm.Delete(ctx)
	}
	return nil
}
