# Default make command
all: help

## run: Run data-notebooks containers.
run:
	make cats
	docker-compose up -d

## stop: Stop data-notebooks containers.
stop:
	docker-compose stop

## run-datadog: Run data-notebooks containers with Datadog.
run-datadog:
	docker-compose -f docker-compose.yml -f docker-compose-debug.yml up -d

## run-ngrok: Run ngrok to expose data-notebooks containers.
run-ngrok:
	docker-compose -f docker-compose.yml -f docker-compose-ngrok.yml up -d

## help: Show a list of commands
help : Makefile
	@echo "Usage:"
	@echo "  make [command]"
	@echo ""
	@echo "Commands:"
	@sed -n 's/^##//p' $< | awk 'BEGIN {FS = ": "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'


.PHONY: all help
