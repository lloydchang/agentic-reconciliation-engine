#!/bin/bash
# Example: Simple Phase 1 setup with all features
# This runs the full Phase 1 automation with test resource creation

set -e

echo "Starting Phase 1 Crossplane setup..."
python3 ./scripts/phase1_setup.py \
  --test-resource \
  "$@"

echo "Phase 1 setup complete!"
echo ""
echo "Next steps:"
echo "  1. Check provider health: kubectl get providers -A"
echo "  2. Monitor test resources: kubectl get buckets -n crossplane-system -w"
echo "  3. Implement CrossplaneProvider in orchestrator"
echo "  4. Proceed to Phase 2 when ready"
