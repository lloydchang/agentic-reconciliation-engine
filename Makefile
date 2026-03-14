SKILLS := $(wildcard .agents/skills/*)

.PHONY: all build test $(SKILLS)

all: build

build: $(SKILLS)
	@go build -o bin/cloud-ai-worker ./ai-agents/cmd/worker/main.go
	@for dir in $(SKILLS); do $(MAKE) -C $$dir build; done

test: $(SKILLS)
	@go test -v ./ai-agents/...
	@for dir in $(SKILLS); do $(MAKE) -C $$dir test; done

$(SKILLS):
	@$(MAKE) -C $@ $(MAKECMDGOALS)
