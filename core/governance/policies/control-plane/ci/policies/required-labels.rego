package main

import future.keywords.if
import future.keywords.in

infra_kinds := {"Database","XDatabase","Volume","XVolume","Queue","XQueue","XCluster","XNetwork"}
required := {"team", "env", "cost-center"}

deny[msg] if {
  input.kind in infra_kinds
  label := required[_]
  not input.metadata.labels[label]
  msg := sprintf("Resource %s/%s is missing required label: %s", [input.kind, input.metadata.name, label])
}
