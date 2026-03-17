package main

import future.keywords.if

deny[msg] if {
  name := input.metadata.name
  not regex.match("^[a-z][a-z0-9-]*[a-z0-9]$", name)
  msg := sprintf("Resource name '%s' must be lowercase kebab-case", [name])
}
