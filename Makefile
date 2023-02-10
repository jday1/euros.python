install:
	pip install -r requirements.txt -r requirements_extras.txt -r requirements_test.txt -e .

upgrade:
	pur -r requirements.txt -r requirements_extras.txt -r requirements_test.txt

format:
	black . && docformatter .

check:
	flake8 --max-line-length 140 . && pylint .  && pydocstyle . && interrogate .

test:
	pytest .

run:
	gunicorn -w 1 -b 0.0.0.0:8080 template_python.main:main_app

build_docker:
	export RES=`python -c "import importlib.metadata; print(importlib.metadata.version('template_python'))"` && \
	docker build -t template_python:${RES} -t template_python:latest .

run_docker:
	docker run -p 8080:8080 template_python:latest
