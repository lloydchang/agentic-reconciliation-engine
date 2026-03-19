package agent_sandbox

import (
	"context"
	"fmt"
	"log"

	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/rest"
	agentsv1alpha1 "github.com/kubernetes-sigs/agent-sandbox/pkg/apis/agents/v1alpha1"
	agentsclient "github.com/kubernetes-sigs/agent-sandbox/pkg/client/clientset/versioned"
	"github.com/agentic-reconciliation-engine/openswe-orchestrator/pkg/config"
)

// TemplateManager manages sandbox templates
type TemplateManager struct {
	spec         *config.TemplateSpec
	config       *config.AgentSandboxConfig
	agentsClient agentsclient.Interface
}

// NewTemplateManager creates a new template manager
func NewTemplateManager(spec *config.TemplateSpec, config *config.AgentSandboxConfig) *TemplateManager {
	return &TemplateManager{
		spec:   spec,
		config: config,
	}
}

// Create creates the sandbox template in Kubernetes
func (tm *TemplateManager) Create(ctx context.Context) error {
	if tm.config.Kubeconfig == nil {
		return fmt.Errorf("kubeconfig not available")
	}

	agentsClient, err := agentsclient.NewForConfig(tm.config.Kubeconfig)
	if err != nil {
		return fmt.Errorf("failed to create agents client: %w", err)
	}
	tm.agentsClient = agentsClient

	// Create SandboxTemplate
	template := &agentsv1alpha1.SandboxTemplate{
		ObjectMeta: metav1.ObjectMeta{
			Name:        tm.spec.Name,
			Namespace:   tm.config.DefaultNamespace,
			Labels:      tm.spec.Labels,
			Annotations: tm.spec.Annotations,
		},
		Spec: agentsv1alpha1.SandboxTemplateSpec{
			PodTemplate: tm.createPodTemplate(),
		},
	}

	_, err = tm.agentsClient.AgentsV1alpha1().SandboxTemplates(tm.config.DefaultNamespace).Create(ctx, template, metav1.CreateOptions{})
	if err != nil {
		return fmt.Errorf("failed to create SandboxTemplate %s: %w", tm.spec.Name, err)
	}

	log.Printf("Created SandboxTemplate: %s", tm.spec.Name)
	return nil
}

// Update updates the sandbox template
func (tm *TemplateManager) Update(ctx context.Context) error {
	if tm.agentsClient == nil {
		return fmt.Errorf("agents client not initialized")
	}

	// Get existing template
	existing, err := tm.agentsClient.AgentsV1alpha1().SandboxTemplates(tm.config.DefaultNamespace).Get(ctx, tm.spec.Name, metav1.GetOptions{})
	if err != nil {
		return fmt.Errorf("failed to get existing template: %w", err)
	}

	// Update spec
	existing.Spec.PodTemplate = tm.createPodTemplate()
	existing.Labels = tm.spec.Labels
	existing.Annotations = tm.spec.Annotations

	_, err = tm.agentsClient.AgentsV1alpha1().SandboxTemplates(tm.config.DefaultNamespace).Update(ctx, existing, metav1.UpdateOptions{})
	if err != nil {
		return fmt.Errorf("failed to update SandboxTemplate %s: %w", tm.spec.Name, err)
	}

	log.Printf("Updated SandboxTemplate: %s", tm.spec.Name)
	return nil
}

// Delete deletes the sandbox template
func (tm *TemplateManager) Delete(ctx context.Context) error {
	if tm.agentsClient == nil {
		return fmt.Errorf("agents client not initialized")
	}

	err := tm.agentsClient.AgentsV1alpha1().SandboxTemplates(tm.config.DefaultNamespace).Delete(ctx, tm.spec.Name, metav1.DeleteOptions{})
	if err != nil {
		return fmt.Errorf("failed to delete SandboxTemplate %s: %w", tm.spec.Name, err)
	}

	log.Printf("Deleted SandboxTemplate: %s", tm.spec.Name)
	return nil
}

// Exists checks if the template exists
func (tm *TemplateManager) Exists(ctx context.Context) (bool, error) {
	if tm.agentsClient == nil {
		return false, fmt.Errorf("agents client not initialized")
	}

	_, err := tm.agentsClient.AgentsV1alpha1().SandboxTemplates(tm.config.DefaultNamespace).Get(ctx, tm.spec.Name, metav1.GetOptions{})
	if err != nil {
		return false, nil // Not found
	}

	return true, nil
}

// GetSpec returns the template specification
func (tm *TemplateManager) GetSpec() *config.TemplateSpec {
	return tm.spec
}

// GetImage returns the container image
func (tm *TemplateManager) GetImage() string {
	return tm.spec.Image
}

// GetEnvironment returns the environment variables
func (tm *TemplateManager) GetEnvironment() map[string]string {
	return tm.spec.Environment
}

// createPodTemplate creates the pod template spec
func (tm *TemplateManager) createPodTemplate() agentsv1alpha1.PodTemplateSpec {
	podTemplate := agentsv1alpha1.PodTemplateSpec{
		Spec: tm.createPodSpec(),
	}

	// Add metadata if labels are specified
	if len(tm.spec.Labels) > 0 {
		podTemplate.Metadata = &agentsv1alpha1.PodMetadata{
			Labels: tm.spec.Labels,
		}
	}

	return podTemplate
}

// createPodSpec creates the pod specification
func (tm *TemplateManager) createPodSpec() agentsv1alpha1.PodSpec {
	podSpec := agentsv1alpha1.PodSpec{
		Containers: []agentsv1alpha1.Container{
			tm.createContainer(),
		},
		RestartPolicy: "OnFailure",
	}

	// Set runtime class if specified
	if tm.spec.RuntimeClass != "" {
		podSpec.RuntimeClassName = &tm.spec.RuntimeClass
	}

	return podSpec
}

// createContainer creates the container specification
func (tm *TemplateManager) createContainer() agentsv1alpha1.Container {
	container := agentsv1alpha1.Container{
		Name:    "sandbox-container",
		Image:   tm.spec.Image,
		Command: tm.spec.Command,
		Args:    tm.spec.Args,
	}

	// Add resource requirements
	if tm.spec.Resources.CPU != "" || tm.spec.Resources.Memory != "" {
		container.Resources = &agentsv1alpha1.ResourceRequirements{
			Requests: tm.createResourceList(),
		}
	}

	// Add environment variables
	if len(tm.spec.Environment) > 0 {
		env := make([]agentsv1alpha1.EnvVar, 0, len(tm.spec.Environment))
		for k, v := range tm.spec.Environment {
			env = append(env, agentsv1alpha1.EnvVar{
				Name:  k,
				Value: v,
			})
		}
		container.Env = env
	}

	// Add security context
	container.SecurityContext = tm.createSecurityContext()

	return container
}

// createResourceList creates resource requirements
func (tm *TemplateManager) createResourceList() agentsv1alpha1.ResourceList {
	resources := make(agentsv1alpha1.ResourceList)

	if tm.spec.Resources.CPU != "" {
		resources["cpu"] = tm.spec.Resources.CPU
	}
	if tm.spec.Resources.Memory != "" {
		resources["memory"] = tm.spec.Resources.Memory
	}
	if tm.spec.Resources.GPU != "" {
		resources["gpu"] = tm.spec.Resources.GPU
	}
	if tm.spec.Resources.Disk != "" {
		resources["ephemeral-storage"] = tm.spec.Resources.Disk
	}

	return resources
}

// createSecurityContext creates security context
func (tm *TemplateManager) createSecurityContext() *agentsv1alpha1.SecurityContext {
	if tm.spec.Security.RunAsUser == 0 && tm.spec.Security.RunAsGroup == 0 {
		return nil
	}

	securityContext := &agentsv1alpha1.SecurityContext{
		RunAsUser:  &tm.spec.Security.RunAsUser,
		RunAsGroup: &tm.spec.Security.RunAsGroup,
	}

	if tm.spec.Security.ReadOnlyRootFS {
		securityContext.ReadOnlyRootFilesystem = &tm.spec.Security.ReadOnlyRootFS
	}

	if len(tm.spec.Security.DropCapabilities) > 0 {
		securityContext.Capabilities = &agentsv1alpha1.Capabilities{
			Drop: tm.spec.Security.DropCapabilities,
		}
	}

	return securityContext
}

// Cleanup cleans up the template manager
func (tm *TemplateManager) Cleanup(ctx context.Context) error {
	if tm.agentsClient != nil {
		return tm.Delete(ctx)
	}
	return nil
}
