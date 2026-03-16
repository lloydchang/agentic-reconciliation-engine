package main

import future.keywords.if
import future.keywords.in

stateful_kinds := {
  "Database", "XDatabase",
  "Volume", "XVolume",
  "Queue", "XQueue",
}

deny[msg] if {
  input.kind in stateful_kinds
  input.spec.deletionPolicy == "Delete"
  not input.metadata.annotations["platform.example.com/allow-deletion"] == "true"
  msg := sprintf(
    "Changing deletionPolicy to Delete on %s/%s requires annotation platform.example.com/allow-deletion: 'true'",
    [input.kind, input.metadata.name],
  )
}
