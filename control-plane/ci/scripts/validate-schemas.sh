#!/bin/bash
set -euo pipefail
cd $(dirname $0)

SCHEMA_LOCATION='https://raw.githubusercontent.com/datreeio/CRDs-catalog/main/{{.Group}}/{{.ResourceKind}}_{{.ResourceAPIVersion}}.json'

kubeconform \
  -strict \
  -ignore-missing-schemas \
  -schema-location default \
  -schema-location "$SCHEMA_LOCATION" \
  -summary \
  infrastructure/ control-plane/

echo "Schema validation passed"
