#Python Template

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

## Project Setup

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

`versionner` is used for versioning. 
To do a major/minor/patch update: `ver up --major/--minor/--patch 1`