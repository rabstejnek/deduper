# pyscaffold

An opinionated starter template for setting up a python 3.12+ package with a CLI.

NOTE: this project is unrelated to the excellent [PyScaffold](https://pypi.org/project/PyScaffold/) project. This repo will likely not be published to pypi, and handles a much smaller and more narrow use case. Apologies in advance for the confusion in naming.

## Customize for your project...

To customize for your own package:

1. Search & replace `pyscaffold` and replace with `yourproject` (or whatever you want to call it).
    - includes source code, tests, and this readme!
    - rename the `pyscaffold` project and test folder too
2. Review pyproject.toml; change `authors`, `classifiers`, `project.urls`, etc.
3. Follow the "Developer setup" section below
4. Update this readme! Delete this section, edit quickstart guide, etc.

This is a manual [cookiecutter](https://github.com/cookiecutter/cookiecutter).  This was done intentionally; keeping it a manual job is nice for testing because it makes it easier to ensure that our github actions work as expected.

## Quickstart

Make sure you have python 3.12 available and on your path. Then:

```bash
# update pip
python -m pip install -U pip

# if it's local file or a github link...
pip install path/to/pyscaffold-0.0.1-py3-none-any.whl
# if it's on pypi
pip install pyscaffold

# test our CLI
pyscaffold --help
pyscaffold hello
pyscaffold hello --name Andy
pyscaffold bottles --num 20
```

## Developer setup

Make sure you have python 3.12 available and on your path. Then:

```bash
# clone project
git clone git@github.com:shapiromatron/pyscaffold.git
cd pyscaffold

# create virtual environment and activate
python -m venv venv --prompt pyscaffold
source venv/bin/activate  # or venv\Scripts\activate on windows.

# install packages
python -m pip install -U pip
python -m pip install -e ".[dev]"

# test local install
pyscaffold hello

# these should work on mac/linux/windows
make test   # run tests
make lint   # identify formatting errors
make format  # fix formatting errors when possible
make build  # build a python wheel
```

Github actions are setup to execute whenever code is pushed to check code formatting and successful tests. In addition, when code is pushed to the `main` branch, a wheel artifact is created and stored on github.
