IMAGE_NAME=notebook-executor
CONTAINER_NAME=lambda-notebook-executor-container
LOCAL_PORT=9000
IMAGE_URL=622020772926.dkr.ecr.us-east-1.amazonaws.com
AWS_STAGING_PROFILE=senstag

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

## docker-login-staging: Login to AWS ECR (Staging)
docker-login-staging:
	aws-vault exec $(AWS_STAGING_PROFILE) -- aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $(IMAGE_URL)

## build-notebook-executor: Build the Docker image.
build-notebook-executor:
	docker build -t $(IMAGE_NAME) -f ./lambdas/notebook-executor/notebook-executor.Dockerfile . --platform linux/amd64

## help: Show a list of commands
help : Makefile
	@echo "Usage:"
	@echo "  make [command]"
	@echo ""
	@echo "Commands:"
	@sed -n 's/^##//p' $< | awk 'BEGIN {FS = ": "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'


.PHONY: all help
