IMAGE_NAME=notebook-executor
CONTAINER_NAME=lambda-notebook-executor-container
LOCAL_PORT=9000
IMAGE_URL=622020772926.dkr.ecr.us-east-1.amazonaws.com
AWS_STAGING_PROFILE=senstag
AWS_PLATFORM_PROFILE=senplat

VECTOR_DATA_UPLOADER_IMAGE_NAME=vector-data-uploader

BASE_IMAGE_NAME=gis-base
BASE_CONTAINER_NAME=local-base-container


include .env

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
	docker build -t $(IMAGE_NAME):latest -f ./lambdas/notebook-executor/notebook-executor.Dockerfile . --platform linux/amd64

## build-notebook-executor-no-cache: Build the Docker image.
build-notebook-executor-no-cache:
	docker build -t $(IMAGE_NAME):latest -f ./lambdas/notebook-executor/notebook-executor.Dockerfile . --platform linux/amd64 --no-cache

## docker-push-notebook-executor: Push the Docker image (Platform)
docker-push-notebook-executor:
	docker push $(IMAGE_URL)/$(IMAGE_NAME):latest

## docker-push: Push the Docker image (Platform)
docker-push: docker-tag docker-push-notebook-executor

## build-base-container: Build the base container.
build-base-container:
	docker build -t gis-base:latest -f ./base.Dockerfile . --platform linux/amd64

## run-base-container: Run the base container and open a shell.
run-base-container:
	docker run --name $(BASE_CONTAINER_NAME) --entrypoint "/bin/sh" -it gis-base:latest -c "sleep infinity"

## exec-base-container: Run the base container and open a shell.
exec-base-container:
	docker exec -it $(BASE_CONTAINER_NAME) /bin/sh

## tag-base-container: Tag the base container.
tag-base-container:
	docker tag $(BASE_IMAGE_NAME):latest $(IMAGE_URL)/$(BASE_IMAGE_NAME):latest

## push-base-container: Push the base container.
push-base-container:
	docker push $(IMAGE_URL)/$(BASE_IMAGE_NAME):latest

## build-pytest-container: Build the pytest container.
build-pytest-container:
	docker build -t pytest:latest -f ./pytest.Dockerfile . --platform linux/amd64

## run-pytest-container: Run the pytest container and open a shell.
run-pytest-container:
	docker run --name pytest-container --entrypoint "/bin/sh" -it pytest:latest -c "sleep infinity"

## exec-pytest-container: Run the pytest container and open a shell.
exec-pytest-container:
	docker exec -it pytest-container /bin/sh

## lambda-update: Update the lambda function with the latest image.
lambda-update:
	aws-vault exec $(AWS_STAGING_PROFILE) -- aws lambda update-function-code --function-name NotebookExecutorFunction --image-uri $(IMAGE_URL)/$(IMAGE_NAME):latest --region us-east-1

## lambda-details: Get the lambda function details.
lambda-details:
	aws-vault exec $(AWS_STAGING_PROFILE) -- aws lambda get-function --function-name NotebookExecutorFunction --region us-east-1

## build-vector-data-uploader: Build the Docker image.
build-vector-data-uploader:
	docker build -t $(VECTOR_DATA_UPLOADER_IMAGE_NAME):latest -f ./lambdas/vector-data-uploader/vector-data-uploader.Dockerfile . --platform linux/amd64

## build-vector-data-uploader-no-cache: Build the Docker image.
build-vector-data-uploader-no-cache:
	docker build -t $(VECTOR_DATA_UPLOADER_IMAGE_NAME):latest -f ./lambdas/vector-data-uploader/vector-data-uploader.Dockerfile . --platform linux/amd64 --no-cache

## run-vector-data-uploader: Run vector-data-uploader.
run-vector-data-uploader:
	docker compose -f docker-compose.yml up --build -d vector-data-uploader

## help: Show a list of commands
help : Makefile
	@echo "Usage:"
	@echo "  make [command]"
	@echo ""
	@echo "Commands:"
	@sed -n 's/^##//p' $< | awk 'BEGIN {FS = ": "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'


.PHONY: all help
