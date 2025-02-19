.PHONY: all build deploy

build:
	rm -rf python_layers/python
	mkdir python_layers/python
	pip install -r python_layers/requirements.txt --target python_layers/python

deploy:
	cdk deploy

all: build deploy
