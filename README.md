# Python Template

## Prerequisites

1) Install [brew](https://brew.sh/):

    ```/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"```

2) Install pyenv and pyenv-virtualenv:

    ```brew install pyenv pyenv-virtualenv```
    
3) Add the following to your bash_profile. This ensures pyenv and pyenv-virtualenv load automatically:
   ```
   eval "$(pyenv init -)"
   eval "$(pyenv virtualenv-init -)"
   ```
   
4) Install docker:

    ```brew cask install docker```
    
5) Install make:
    
    ```brew install make```

## Setup

1) Ensure the python version you want to use is installed: `pyenv install 3.9.1`

2) Create your virtual environment: `pyenv virtualenv 3.9.1 template_python`

3) Modify Intellij to use your virtual environment:

    a) File -> Project Structure

    b) Project Structure -> New -> Python SDK

    c) Existing Environment

    d) ~/.pyenv/versions/template_python/bin/python

    e) You can check this by opening the terminal and running `python --version`.
    You should see something similar to:
    
    ```   
    (template_python)
    jamesday @ ~/personal-projects/template.python 
     [1] → python --version
    Python 3.9.1
    ```

4) Run `pip install versionner; ver init; pip install .` (Needs to be ran this way to avoid cyclic issues)

## Versioning

`versionner` is used for versioning. Run `pip install -e .[versioning]` to install.
 
To do a major/minor/patch update: `ver up --major/--minor/--patch 1`

## Lint

Linting is important to maintain readability of the codebase. Pylama is used to enforce standards with the `pylama.ini`
file used to manage options such as rule exemptions [(see docs)](https://pylama.readthedocs.io/en/latest/#set-pylama-checkers-options).  

### With Docker

Run `make lint` to run `pylama` in docker generating a report accessed @ `./lint.txt`.

### Without Docker

Run `pylama --report my_lint.txt`.

## Test

### With Docker

For convenience, testing can be done in docker to remove some of the burden.
If changes have been made to test dependencies run `make clean-test`, otherwise run `make test`.

### Without Docker

If changes have been made to test dependencies you will first need to run `pip install -e .[dev]`.

Then to run the tests: `pytest`.


To run with coverage: `coverage run -m pytest --html=report.html --self-contained-html`. This will generate a report
which can be accessed @ `./report.html`

## Deploy

### With Docker

To deploy using docker first build the application using `make build` and then run using `make deploy`. This will spin
up and instance of the application in a docker container with endpoints available on port 8080.

### Without Docker

To run without docker, there are two methods.
1) `python template_python/main.py` - will run flask using a development server
2) `gunicorn -w 1 -b 0.0.0.0:8080 template_python.main:app` - will run flask on a server with 1 worker.

## Endpoints

With the application running (whether with or without docker), there is an sample endpoint called hello_world which
simply returns `Hello World!` as shown below.

```
(template_python) 
jamesday @ ~/personal-projects/template.python * main
 [5] → curl localhost:8080/hello_world
Hello World!
```
