package config

import (
	"fmt"
	"time"

	"k8s.io/client-go/rest"
)

// AgentSandboxConfig defines configuration for Agent Sandbox provider
type AgentSandboxConfig struct {
	Enabled           bool            `yaml:"enabled" json:"enabled"`
	Kubeconfig        *rest.Config    `yaml:"-" json:"-"`
	DefaultNamespace  string          `yaml:"default_namespace" json:"default_namespace"`
	DefaultTemplate   string          `yaml:"default_template" json:"default_template"`
	DefaultWarmPool   string          `yaml:"default_warm_pool" json:"default_warm_pool"`
	Timeout           time.Duration   `yaml:"timeout" json:"timeout"`
	EnableSnapshots   bool            `yaml:"enable_snapshots" json:"enable_snapshots"`
	StorageBucket     string          `yaml:"storage_bucket" json:"storage_bucket"`
	ResourceDefaults  ResourceSpec    `yaml:"resource_defaults" json:"resource_defaults"`
	NetworkPolicy     NetworkPolicy   `yaml:"network_policy" json:"network_policy"`
	Templates         []TemplateSpec  `yaml:"templates" json:"templates"`
	WarmPools         []WarmPoolSpec  `yaml:"warm_pools" json:"warm_pools"`
}

// ResourceSpec defines resource requirements for sandbox environments
type ResourceSpec struct {
	CPU    string `yaml:"cpu" json:"cpu"`
	Memory string `yaml:"memory" json:"memory"`
	GPU    string `yaml:"gpu" json:"gpu"`
	Disk   string `yaml:"disk" json:"disk"`
}

// NetworkPolicy defines network access rules for sandboxes
type NetworkPolicy struct {
	DefaultDenyEgress bool     `yaml:"default_deny_egress" json:"default_deny_egress"`
	AllowedDomains    []string `yaml:"allowed_domains" json:"allowed_domains"`
	AllowedPorts      []int    `yaml:"allowed_ports" json:"allowed_ports"`
}

// TemplateSpec defines a sandbox template configuration
type TemplateSpec struct {
	Name        string                 `yaml:"name" json:"name"`
	Description string                 `yaml:"description" json:"description"`
	Image       string                 `yaml:"image" json:"image"`
	Command     []string               `yaml:"command" json:"command"`
	Args        []string               `yaml:"args" json:"args"`
	Resources   ResourceSpec           `yaml:"resources" json:"resources"`
	Environment map[string]string      `yaml:"environment" json:"environment"`
	RuntimeClass string                `yaml:"runtime_class" json:"runtime_class"`
	Labels      map[string]string      `yaml:"labels" json:"labels"`
	Annotations map[string]string      `yaml:"annotations" json:"annotations"`
	Security    SecuritySpec           `yaml:"security" json:"security"`
}

// SecuritySpec defines security settings for sandbox templates
type SecuritySpec struct {
	RunAsUser    int64    `yaml:"run_as_user" json:"run_as_user"`
	RunAsGroup   int64    `yaml:"run_as_group" json:"run_as_group"`
	ReadOnlyRootFS bool   `yaml:"read_only_root_fs" json:"read_only_root_fs"`
	DropCapabilities []string `yaml:"drop_capabilities" json:"drop_capabilities"`
	SeccompProfile string `yaml:"seccomp_profile" json:"seccomp_profile"`
}

// WarmPoolSpec defines a warm pool configuration
type WarmPoolSpec struct {
	Name         string        `yaml:"name" json:"name"`
	TemplateName string        `yaml:"template_name" json:"template_name"`
	Replicas     int32         `yaml:"replicas" json:"replicas"`
	MinReady     int32         `yaml:"min_ready" json:"min_ready"`
	IdleTimeout  time.Duration `yaml:"idle_timeout" json:"idle_timeout"`
}

// DefaultAgentSandboxConfig returns a default configuration for Agent Sandbox
func DefaultAgentSandboxConfig() *AgentSandboxConfig {
	return &AgentSandboxConfig{
		Enabled:          false,
		DefaultNamespace:  "agent-sandbox",
		DefaultTemplate:   "python-runtime-template",
		DefaultWarmPool:   "python-runtime-warmpool",
		Timeout:           time.Minute * 10,
		EnableSnapshots:   false,
		StorageBucket:     "",
		ResourceDefaults: ResourceSpec{
			CPU:    "250m",
			Memory: "512Mi",
			GPU:    "",
			Disk:   "1Gi",
		},
		NetworkPolicy: NetworkPolicy{
			DefaultDenyEgress: true,
			AllowedDomains:   []string{},
			AllowedPorts:     []int{},
		},
		Templates: []TemplateSpec{
			{
				Name:        "python-runtime-template",
				Description: "Python runtime template for AI agents",
				Image:       "python:3.10-slim",
				Command:     []string{"python3"},
				Args:        []string{"-c", "while True: pass"},
				Resources: ResourceSpec{
					CPU:    "250m",
					Memory: "512Mi",
				},
				Environment: map[string]string{
					"PYTHONUNBUFFERED": "1",
				},
				RuntimeClass: "gvisor",
				Labels: map[string]string{
					"app": "agent-sandbox-workload",
				},
				Security: SecuritySpec{
					RunAsUser:      1000,
					RunAsGroup:     1000,
					ReadOnlyRootFS: false,
					SeccompProfile: "runtime/default",
				},
			},
			{
				Name:        "bash-runtime-template",
				Description: "Bash runtime template for infrastructure operations",
				Image:       "ubuntu:22.04",
				Command:     []string{"bash"},
				Args:        []string{"-c", "while true; do sleep 30; done"},
				Resources: ResourceSpec{
					CPU:    "250m",
					Memory: "512Mi",
				},
				Environment: map[string]string{
					"DEBIAN_FRONTEND": "noninteractive",
				},
				RuntimeClass: "gvisor",
				Labels: map[string]string{
					"app": "agent-sandbox-workload",
				},
				Security: SecuritySpec{
					RunAsUser:      1000,
					RunAsGroup:     1000,
					ReadOnlyRootFS: false,
					SeccompProfile: "runtime/default",
				},
			},
		},
		WarmPools: []WarmPoolSpec{
			{
				Name:         "python-runtime-warmpool",
				TemplateName: "python-runtime-template",
				Replicas:     2,
				MinReady:     1,
				IdleTimeout:  time.Minute * 30,
			},
			{
				Name:         "bash-runtime-warmpool",
				TemplateName: "bash-runtime-template",
				Replicas:     1,
				MinReady:     1,
				IdleTimeout:  time.Minute * 30,
			},
		},
	}
}

// Validate validates the Agent Sandbox configuration
func (c *AgentSandboxConfig) Validate() error {
	if c.Enabled && c.Kubeconfig == nil {
		return fmt.Errorf("kubeconfig is required when Agent Sandbox is enabled")
	}

	if c.DefaultNamespace == "" {
		return fmt.Errorf("default_namespace is required")
	}

	if c.DefaultTemplate == "" {
		return fmt.Errorf("default_template is required")
	}

	// Validate templates
	templateNames := make(map[string]bool)
	for _, template := range c.Templates {
		if template.Name == "" {
			return fmt.Errorf("template name is required")
		}
		if template.Image == "" {
			return fmt.Errorf("template %s: image is required", template.Name)
		}
		if templateNames[template.Name] {
			return fmt.Errorf("duplicate template name: %s", template.Name)
		}
		templateNames[template.Name] = true
	}

	// Validate warm pools
	for _, pool := range c.WarmPools {
		if pool.Name == "" {
			return fmt.Errorf("warm pool name is required")
		}
		if pool.TemplateName == "" {
			return fmt.Errorf("warm pool %s: template_name is required", pool.Name)
		}
		if !templateNames[pool.TemplateName] {
			return fmt.Errorf("warm pool %s: template %s not found", pool.Name, pool.TemplateName)
		}
		if pool.Replicas < 0 {
			return fmt.Errorf("warm pool %s: replicas must be non-negative", pool.Name)
		}
		if pool.MinReady < 0 || pool.MinReady > pool.Replicas {
			return fmt.Errorf("warm pool %s: min_ready must be between 0 and replicas", pool.Name)
		}
	}

	// Validate default template exists
	if !templateNames[c.DefaultTemplate] {
		return fmt.Errorf("default_template %s not found in templates", c.DefaultTemplate)
	}

	return nil
}

// GetTemplate returns a template by name
func (c *AgentSandboxConfig) GetTemplate(name string) (*TemplateSpec, error) {
	for _, template := range c.Templates {
		if template.Name == name {
			return &template, nil
		}
	}
	return nil, fmt.Errorf("template %s not found", name)
}

// GetWarmPool returns a warm pool by name
func (c *AgentSandboxConfig) GetWarmPool(name string) (*WarmPoolSpec, error) {
	for _, pool := range c.WarmPools {
		if pool.Name == name {
			return &pool, nil
		}
	}
	return nil, fmt.Errorf("warm pool %s not found", name)
}
