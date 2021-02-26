FROM python:3.9

# We install the app dependencies, project code under test will be accessed by docker-compose.yml volume config
RUN mkdir /app
COPY . /app
WORKDIR /app

RUN pip install -e .[lint]
