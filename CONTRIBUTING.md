# Contributing to Grow

## Development

Set up a development environment:

```
git clone git@github.com:grow/grow.git
make develop
```

Once your development environment is set up, run Grow:

```bash
pipenv shell
pip install --editable .
grow
```

Then run tests:

```bash
make test
```

We try to set everything up for you automatically (including a `virtualenv`) in
the `make` commands, but if you are using Linux and something is not working,
you might try:

```bash
make develop-linux
make test
```

## Development without pipenv

If you are using standard virtual environments or a different virtual environment manager (like pyenv) you can follow this instructions.

### Install libyaml

```bash
# On Mac with Homebrew (https://brew.sh/).
brew install libyaml

# On Ubuntu.
sudo apt install libyaml-dev
```

### Create the virtualenv and activate it

Follow the instructions of your virtual environment manager.

### Create requirements

You can create the file `requirements.txt` with

```bash
cat Pipfile | grep '[=<>]=' | sed -e s," = ",, -e s,\",,g > requirements.txt
```

then install the requirements with

```bash
pip install -r requirements.txt
```

## Commit messages

[Release Please](https://github.com/googleapis/release-please) is used to
automatically create changelogs, releases, and versions.

- Commit messages must follow the [Conventional
  Commit](https://www.conventionalcommits.org/en/v1.0.0/) specification
- Follow the [Angular
  convention](https://github.com/angular/angular/blob/22b96b9/CONTRIBUTING.md#type)
  to see all commit types

## Docker

- Run `pipenv run ./docker_push.sh` to update docker images.
