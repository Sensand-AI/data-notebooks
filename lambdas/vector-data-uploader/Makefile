# Define variables for Docker image name and container name
IMAGE_NAME=vector-data-uploder
CONTAINER_NAME=lambda-vector-data-uploder-container
LOCAL_PORT=9003
IMAGE_URL=622020772926.dkr.ecr.us-east-1.amazonaws.com

# Default make command
all: help

## docker-build: Build the Docker image.
docker-build:
	docker build -t $(IMAGE_NAME) lambdas/vector-data-uploder/vector-data-uploder.Dockerfile --platform linux/amd64

## docker-login-staging: Login to AWS ECR (Staging)
docker-login-platform:
	aws-vault exec senplat -- aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $(IMAGE_URL)

## docker-login-staging: Login to AWS ECR (Staging)
docker-login-staging:
	aws-vault exec senstag -- aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $(IMAGE_URL)

## docker-tag-staging: Tag the Docker image (Staging)
docker-tag-staging:
	docker tag $(IMAGE_NAME):latest $(IMAGE_URL)/$(IMAGE_NAME):latest

## docker-push-staging: Push the Docker image (Staging)
docker-push-staging:
	aws-vault exec senstag -- docker push $(IMAGE_URL):latest

## clean: Stop and remove the Docker container.
clean:
	docker stop $(CONTAINER_NAME)
	docker rm $(CONTAINER_NAME)

## clean-image: Remove the Docker image.
clean-image:
	docker rmi $(IMAGE_NAME)

# TODO: update with the correct event data
## test-local: Test the Lambda function locally
test-local:
	curl -XPOST "http://localhost:$(LOCAL_PORT)/2015-03-31/functions/function/invocations" -d '{ \
		"parameters": { \
			"param1": "value1", \
			"param2": "value2" \
		} \
	}'

## help: Show a list of commands
help : Makefile
	@echo "Usage:"
	@echo "  make [command]"
	@echo ""
	@echo "Commands:"
	@sed -n 's/^##//p' $< | awk 'BEGIN {FS = ": "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'


.PHONY: all build run clean clean-image help
