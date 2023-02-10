#!/bin/bash

set -ex

echo "Generating flake8 badge..."
PYLINT_VERSION=$(pylint --version | grep pylint | awk '{print $2}')
anybadge -l pylint -v "$PYLINT_VERSION" -f .badges/pylint.svg -o

echo "Generating tests count badge..."
pytest --junitxml=.reports/junit/junit.xml
genbadge tests -o .badges/tests-count.svg

echo "Generating coverage badge..."
coverage run -m pytest --cov=template_python */tests
coverage xml -o .reports/coverage/coverage.xml
genbadge coverage --input-file .reports/coverage/coverage.xml -o .badges/coverage.svg

echo "Generating flake8 badge..."
rm -f .reports/flake8/flake8stats.txt && \
  flake8 \
    --exit-zero \
    --statistics \
    --max-line-length 140 \
    --tee \
    --output-file .reports/flake8/flake8stats.txt \
    --format=html \
    --htmldir .reports/flake8 \
    .
genbadge flake8 -o .badges/flake8.svg

echo "Generating interrogate badge..."
interrogate .
