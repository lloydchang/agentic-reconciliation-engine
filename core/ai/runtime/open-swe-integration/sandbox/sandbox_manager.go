package sandbox

import (
	"context"
	"fmt"
	"time"

	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/resource"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/kubernetes"
)

// SandboxManager handles sandbox resource management and isolation
type SandboxManager struct {
	clientset *kubernetes.Clientset
	namespace string
	limits    ResourceLimits
}

// ResourceLimits defines sandbox resource constraints
type ResourceLimits struct {
	MaxMemory     string `json:"max_memory"`
	MaxCPU        string `json:"max_cpu"`
	MaxPods       int    `json:"max_pods"`
	MaxExecTime   time.Duration `json:"max_exec_time"`
	StorageLimit  string `json:"storage_limit"`
	NetworkPolicy string `json:"network_policy"`
}

// NewSandboxManager creates a new sandbox manager
func NewSandboxManager(clientset *kubernetes.Clientset, namespace string) *SandboxManager {
	return &SandboxManager{
		clientset: clientset,
		namespace: namespace,
		limits: ResourceLimits{
			MaxMemory:    "512Mi",
			MaxCPU:       "500m",
			MaxPods:      5,
			MaxExecTime:  5 * time.Minute,
			StorageLimit: "1Gi",
			NetworkPolicy: "isolated",
		},
	}
}

// CreateSandboxPod creates an isolated sandbox pod for code execution
func (sm *SandboxManager) CreateSandboxPod(ctx context.Context, executionID string, code string) (*corev1.Pod, error) {
	podName := fmt.Sprintf("sandbox-%s", executionID)

	pod := &corev1.Pod{
		ObjectMeta: metav1.ObjectMeta{
			Name:      podName,
			Namespace: sm.namespace,
			Labels: map[string]string{
				"app":              "open-swe-sandbox",
				"sandbox-id":       executionID,
				"security-context": "isolated",
			},
			Annotations: map[string]string{
				"open-swe/sandbox-execution": executionID,
				"security.alpha.kubernetes.io/sandbox": "true",
			},
		},
		Spec: corev1.PodSpec{
			RestartPolicy: corev1.RestartPolicyNever,
			SecurityContext: &corev1.PodSecurityContext{
				RunAsUser:    int64Ptr(1000),
				RunAsGroup:   int64Ptr(1000),
				FSGroup:      int64Ptr(1000),
				RunAsNonRoot: boolPtr(true),
			},
			Containers: []corev1.Container{
				{
					Name:  "sandbox-executor",
					Image: "open-swe/sandbox-executor:latest",
					Command: []string{
						"/bin/sh",
						"-c",
						fmt.Sprintf("timeout %d python3 -c \"%s\"", int(sm.limits.MaxExecTime.Seconds()), code),
					},
					Resources: corev1.ResourceRequirements{
						Limits: corev1.ResourceList{
							corev1.ResourceMemory: resource.MustParse(sm.limits.MaxMemory),
							corev1.ResourceCPU:    resource.MustParse(sm.limits.MaxCPU),
						},
						Requests: corev1.ResourceList{
							corev1.ResourceMemory: resource.MustParse("128Mi"),
							corev1.ResourceCPU:    resource.MustParse("100m"),
						},
					},
					SecurityContext: &corev1.SecurityContext{
						AllowPrivilegeEscalation: boolPtr(false),
						ReadOnlyRootFilesystem:   boolPtr(true),
						Capabilities: &corev1.Capabilities{
							Drop: []corev1.Capability{
								"ALL",
							},
						},
					},
					VolumeMounts: []corev1.VolumeMount{
						{
							Name:      "tmp-volume",
							MountPath: "/tmp",
							ReadOnly:  false,
						},
					},
				},
			},
			Volumes: []corev1.Volume{
				{
					Name: "tmp-volume",
					VolumeSource: corev1.VolumeSource{
						EmptyDir: &corev1.EmptyDirVolumeSource{
							SizeLimit: resource.MustParse("100Mi"),
						},
					},
				},
			},
			// Network isolation
			AutomountServiceAccountToken: boolPtr(false),
		},
	}

	createdPod, err := sm.clientset.CoreV1().Pods(sm.namespace).Create(ctx, pod, metav1.CreateOptions{})
	if err != nil {
		return nil, fmt.Errorf("failed to create sandbox pod: %w", err)
	}

	return createdPod, nil
}

// MonitorExecution monitors sandbox execution and enforces limits
func (sm *SandboxManager) MonitorExecution(ctx context.Context, podName string) error {
	watchCtx, cancel := context.WithTimeout(ctx, sm.limits.MaxExecTime+30*time.Second)
	defer cancel()

	watcher, err := sm.clientset.CoreV1().Pods(sm.namespace).Watch(watchCtx, metav1.ListOptions{
		FieldSelector: fmt.Sprintf("metadata.name=%s", podName),
	})

	if err != nil {
		return fmt.Errorf("failed to watch pod: %w", err)
	}
	defer watcher.Stop()

	for event := range watcher.ResultChan() {
		pod, ok := event.Object.(*corev1.Pod)
		if !ok {
			continue
		}

		switch pod.Status.Phase {
		case corev1.PodSucceeded, corev1.PodFailed:
			return nil
		case corev1.PodRunning:
			// Check resource usage
			if err := sm.enforceResourceLimits(pod); err != nil {
				return fmt.Errorf("resource limit violation: %w", err)
			}
		}
	}

	return fmt.Errorf("pod monitoring timeout")
}

// enforceResourceLimits checks and enforces resource limits
func (sm *SandboxManager) enforceResourceLimits(pod *corev1.Pod) error {
	// Check memory usage
	for _, container := range pod.Status.ContainerStatuses {
		if container.LastTerminationState.Terminated != nil {
			if container.LastTerminationState.Terminated.Reason == "OOMKilled" {
				return fmt.Errorf("sandbox exceeded memory limit")
			}
		}
	}

	// Check execution time
	if pod.Status.StartTime != nil {
		runtime := time.Since(pod.Status.StartTime.Time)
		if runtime > sm.limits.MaxExecTime {
			// Delete pod if it exceeds time limit
			sm.clientset.CoreV1().Pods(sm.namespace).Delete(context.Background(), pod.Name, metav1.DeleteOptions{})
			return fmt.Errorf("sandbox exceeded execution time limit")
		}
	}

	return nil
}

// CleanupSandbox cleans up sandbox resources
func (sm *SandboxManager) CleanupSandbox(ctx context.Context, executionID string) error {
	labelSelector := fmt.Sprintf("sandbox-id=%s", executionID)

	// Delete pods
	err := sm.clientset.CoreV1().Pods(sm.namespace).DeleteCollection(ctx, metav1.DeleteOptions{}, metav1.ListOptions{
		LabelSelector: labelSelector,
	})
	if err != nil {
		return fmt.Errorf("failed to cleanup sandbox pods: %w", err)
	}

	// Delete configmaps
	err = sm.clientset.CoreV1().ConfigMaps(sm.namespace).DeleteCollection(ctx, metav1.DeleteOptions{}, metav1.ListOptions{
		LabelSelector: labelSelector,
	})
	if err != nil {
		return fmt.Errorf("failed to cleanup sandbox configmaps: %w", err)
	}

	return nil
}

// GetSandboxStatus returns the current status of a sandbox execution
func (sm *SandboxManager) GetSandboxStatus(ctx context.Context, executionID string) (*SandboxStatus, error) {
	labelSelector := fmt.Sprintf("sandbox-id=%s", executionID)

	podList, err := sm.clientset.CoreV1().Pods(sm.namespace).List(ctx, metav1.ListOptions{
		LabelSelector: labelSelector,
	})
	if err != nil {
		return nil, fmt.Errorf("failed to list sandbox pods: %w", err)
	}

	if len(podList.Items) == 0 {
		return &SandboxStatus{Status: "not_found"}, nil
	}

	pod := podList.Items[0]
	status := &SandboxStatus{
		ExecutionID: executionID,
		Status:      string(pod.Status.Phase),
		StartTime:   pod.Status.StartTime,
	}

	if pod.Status.Phase == corev1.PodSucceeded || pod.Status.Phase == corev1.PodFailed {
		status.CompletionTime = &pod.Status.ContainerStatuses[0].State.Terminated.FinishedAt
		if pod.Status.ContainerStatuses[0].State.Terminated.ExitCode != 0 {
			status.Error = pod.Status.ContainerStatuses[0].State.Terminated.Message
		}
	}

	return status, nil
}

// SandboxStatus represents the status of a sandbox execution
type SandboxStatus struct {
	ExecutionID   string     `json:"execution_id"`
	Status        string     `json:"status"`
	StartTime     *metav1.Time `json:"start_time,omitempty"`
	CompletionTime *metav1.Time `json:"completion_time,omitempty"`
	Error         string     `json:"error,omitempty"`
}

// Helper functions
func int64Ptr(i int64) *int64 { return &i }
func boolPtr(b bool) *bool { return &b }
