IMAGE_NAME=notebook-executor
CONTAINER_NAME=lambda-notebook-executor-container
LOCAL_PORT=9000
IMAGE_URL=622020772926.dkr.ecr.us-east-1.amazonaws.com
AWS_STAGING_PROFILE=senstag
AWS_PLATFORM_PROFILE=senplat

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

## docker-login-platform: Login to AWS ECR (Platform)
docker-login-platform:
	aws-vault exec $(AWS_PLATFORM_PROFILE) -- aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $(IMAGE_URL)

## docker-tag: Tag the Docker image (Platform)
docker-tag:
	docker tag $(IMAGE_NAME):latest $(IMAGE_URL)/$(IMAGE_NAME):latest

## build-notebook-executor: Build the Docker image.
build-notebook-executor:
	docker build -t $(IMAGE_NAME) -f ./lambdas/notebook-executor/notebook-executor.Dockerfile . --platform linux/amd64

## build-notebook-executor-no-cache: Build the Docker image.
build-notebook-executor-no-cache:
	docker build -t $(IMAGE_NAME) -f ./lambdas/notebook-executor/notebook-executor.Dockerfile . --platform linux/amd64 --no-cache

## docker-push-notebook-executor: Push the Docker image (Platform)
docker-push-notebook-executor:
	docker push $(IMAGE_URL)/$(IMAGE_NAME):latest

## docker-push: Push the Docker image (Platform)
docker-push: docker-tag docker-push-notebook-executor

## lambda-update: Update the lambda function with the latest image.
lambda-update:
	aws-vault exec $(AWS_STAGING_PROFILE) -- aws lambda update-function-code --function-name NotebookExecutorFunction --image-uri $(IMAGE_URL)/$(IMAGE_NAME):latest --region us-east-1

## lambda-details: Get the lambda function details.
lambda-details:
	aws-vault exec $(AWS_STAGING_PROFILE) -- aws lambda get-function --function-name NotebookExecutorFunction --region us-east-1

## help: Show a list of commands
help : Makefile
	@echo "Usage:"
	@echo "  make [command]"
	@echo ""
	@echo "Commands:"
	@sed -n 's/^##//p' $< | awk 'BEGIN {FS = ": "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'


.PHONY: all help
