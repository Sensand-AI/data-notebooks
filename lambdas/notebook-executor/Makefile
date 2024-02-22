# Define variables for Docker image name and container name
IMAGE_NAME=lambda-notebook-executor
CONTAINER_NAME=lambda-notebook-executor-container

# Default make command
all: build

## build: Build the Docker image.
build:
	docker build -t $(IMAGE_NAME) . --platform linux/amd64 --no-cache

## run: Run the Docker container.
run:
	docker run --name $(CONTAINER_NAME) -p 9000:8080 $(IMAGE_NAME)

## clean: Stop and remove the Docker container.
clean:
	docker stop $(CONTAINER_NAME)
	docker rm $(CONTAINER_NAME)

## clean-image: Remove the Docker image.
clean-image:
	docker rmi $(IMAGE_NAME)

## help: Show a list of commands
help : Makefile
	@echo "Usage:"
	@echo "  make [command]"
	@echo ""
	@echo "Commands:"
	@sed -n 's/^##//p' $< | awk 'BEGIN {FS = ": "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'


.PHONY: all build run clean clean-image help
