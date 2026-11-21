---
$title: Install
$path: /install/
$order: 2
$category: Get started
---
# Install Grow.dev

Grow.dev is a Python 3 program. We recommend using
[Pipenv](https://pypi.org/project/pipenv/) to manage Python installations and
versions across projects. To use Pipenv with Grow.dev, see the below steps.

Using Pipenv permits you to have a different version of Python and a different
version of Grow.dev installed on a per-project basis.

## Install Pipenv

### Mac setup

1. Install [Homebrew](https://brew.sh/).
2. Install Pipenv and LibYAML:

```bash
brew install pipenv libyaml
```

### Linux setup

1. Install [Pipenv](https://pypi.org/project/pipenv/)

## Create a Pipfile

Pipenv uses `Pipfile` files to specify Python installations and dependencies.

Run the following to add a `Pipfile` and `Pipfile.lock`:

```bash
# Setup the pipenv config using Python 3
pipenv --python 3

# Install the grow dependency.
pipenv install grow~=1.0.0
```

Need to use a different version of Grow.dev? Update the versions of `grow` and
`python_version` in `Pipfile` accordingly.

## Node setup

Most Grow.dev projects rely on Node in some way for JavaScript extensions. We
recommend using `nvm` for managing Node versions.

- [Read nvm install instructions](https://github.com/nvm-sh/nvm#install-script)

Most Grow.dev extensions rely on Node versions 10.x or higher.

Note for Mac users: many Node programs (i.e. popular `node-sass`) may require
Xcode and its command line tools to compile. Install Xcode using the Mac App
Store, and then follow the `xcode-select` [install
instructions](https://github.com/nodejs/node-gyp/issues/569#issue-55705963).

## Alias

For convenience, we recommend adding a global alias for `grow` to `pipenv run
grow`. This permits you to run `grow` instead of `pipenv run grow` for all
Grow commands.

```bash
# In .bash_profile (or similar).
alias grow='pipenv run grow'
```

## Using a starter

We recommend using a starter project to get started with your first Grow.dev
website. Get started with our [base starter](http://github.com/grow/starter)
which provides a `Pipfile` and a project structure that's ready to go.

## Next steps

Once the above steps are completed, you can invoke `grow` to use the CLI. Run
the below commands from within your project directory:

```bash
# Output help.
grow --help

# Install project dependencies (Python and Node extensions).
grow install

# Run the development server.
grow run

# Build the project.
grow build
```

Once you're familiar with the overall setup, most projects can be started with:

```bash
pipenv install
grow install
grow run
```

## Troubleshooting

### LibYAML

If you are seeing this message: `Warning: libyaml missing, using slower yaml
parser.` when running `grow` you may not have LibYAML installed or need to run a
command to fix Pipenv to correctly use it.

- [Learn about the LibYAML fix]([url('/content/docs/workflow/libyaml.md')]).

### watchdog on macOS and Python 3.8

Certain configurations of macOS and xCode may run into issues installing the
`watchdog` dependency. The simplest way to resolve this is to use Python 3.7,
which isn't impacted by the
[issue](https://github.com/gorakhargosh/watchdog/issues/689). Many systems will
have Python 3.7 available, but newer systems may only have Python 3.8.

```bash
# Install Python 3.7.9 globally.
brew install pyenv
pyenv install 3.7.9
pyenv global 3.7.9

# Run from your Grow project directory.
pipenv --rm
pipenv install
```

### Getting Python 3x on macOS

We recommend using the newest verson of macOS which has the newest versions of
Python 3 available. If you are on an older version of macOS, you can use
`pyenv` to install Python 3:

```bash
# Install
brew install pyenv
pyenv install 3.7.9
pyenv global 3.7.9

# Configure which versions to use for Python 3 and Python 2
pyenv install 3.7.9 2.7.18
pyenv global 3.7.9 2.7.18
```
