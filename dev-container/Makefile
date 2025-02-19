.PHONY: all build push

build:
	docker buildx build --platform=linux/amd64 -t localhost:5001/dev-container:latest .

push:
	docker push localhost:5001/dev-container:latest

all: build push
