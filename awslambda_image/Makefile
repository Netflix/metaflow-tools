# Usage: make REGISTRY=1234567890.dkr.ecr.us-west-2.amazonaws.com IMAGE=my-metaflow-lambda:latest

all: Dockerfile entrypoint.py
	docker build -t $(REGISTRY)/$(IMAGE) .
	aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin $(REGISTRY)
	docker push $(REGISTRY)/$(IMAGE)
