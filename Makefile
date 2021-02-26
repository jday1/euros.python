VERSION = `cat ./VERSION`

lint:
	docker-compose run --rm lint

clean-lint:
	docker-compose build --no-cache lint && make lint

test:
	docker-compose run --rm test

clean-test:
	docker-compose build --no-cache test && make test

build:
	docker build -t template_python:$(VERSION) -t template_python:latest .

deploy:
	docker run -p 8080:8080 template_python:latest
