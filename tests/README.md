# GitOps Infrastructure Control Plane - Tests

This directory contains validation scripts and tests for the GitOps Infrastructure Control Plane.

## Drift Test

The `drift-test.sh` script validates the core capability of the GitOps control plane: **continuous reconciliation**.

### Purpose

This test verifies that:
1. Infrastructure is initially provisioned correctly via Git
2. Manual changes (drift) are detected by the controllers
3. Drift is automatically repaired to match the Git state
4. The system maintains infrastructure consistency without human intervention

### Test Flow

1. **Verification**: Confirms initial infrastructure exists (VPC, EKS cluster)
2. **Drift Creation**: Manually deletes a subnet to introduce configuration drift
3. **Reconciliation**: Waits for controllers to detect and repair the drift
4. **Cluster Test**: Tests EKS cluster drift detection by modifying node count
5. **Final Validation**: Verifies all components are healthy and reconciled

### Prerequisites

- AWS CLI configured with appropriate permissions
- `kubectl` access to the management cluster
- Initial infrastructure deployment completed
- Flux controllers running and healthy

### Usage

```bash
# Make the script executable
chmod +x tests/drift-test.sh

# Run the drift test
./tests/drift-test.sh
```

### Expected Output

The script will:
- Show step-by-step progress with colored output
- Display infrastructure state changes
- Confirm when drift is detected and repaired
- Provide final pass/fail status

### Success Criteria

✅ **PASS**: All drift is automatically reconciled within the timeout period  
❌ **FAIL**: Drift is not detected or not repaired automatically

### Troubleshooting

If the test fails:
1. Check controller logs: `kubectl logs -n ack-system deployment/ack-ec2-controller`
2. Verify Flux status: `flux get kustomizations`
3. Check resource status: `kubectl get vpc,subnet -n flux-system`
4. Ensure cloud provider permissions are correctly configured

## Integration Tests

Additional test scripts can be added here for:
- Multi-cloud resource provisioning validation
- Controller health checks
- Performance and scalability testing
- Disaster recovery scenarios
