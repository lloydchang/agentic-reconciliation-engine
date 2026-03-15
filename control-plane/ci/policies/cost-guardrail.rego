package main

import future.keywords.if
import future.keywords.in

large_sizes := {"xlarge", "2xlarge", "4xlarge", "8xlarge", "r6g.4xlarge", "Standard_E32s_v3"}

warn[msg] if {
  input.kind in {"Database","XDatabase"}
  input.spec.size in large_sizes
  msg := sprintf(
    "Resource %s/%s uses size '%s' — platform team review required (add platform.example.com/cost-approved: 'true' to suppress)",
    [input.kind, input.metadata.name, input.spec.size],
  )
}
