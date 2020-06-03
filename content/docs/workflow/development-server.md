---
$title: Development server
$order: 10.1
$category: Workflow
---

## Installation

```bash
# Install using the installer.
curl https://install.grow.io | bash

# Install using pip.
pip install grow
```

### Mac setup

Many Grow projects use Python and JavaScript extensions. On a fresh Mac OS, you may need `pip` and `yarn` (or `npm`) to successfully develop these projects on your machine in addition to Grow.

```bash
# Install pip.
sudo easy_install pip

# Install nvm (used to install node)
# See instructions: https://github.com/nvm-sh/nvm#install-script

# Install Homebrew (used to install Yarn)
# See instructions: https://brew.sh/

# Install Yarn.
brew install yarn
```

Note: some Node programs (e.g. certain versions of `node-sass`) may require Xcode and the command line tools to compile. Install Xcode (using App Store) and then follow the `xcode-select` instructions [here](https://github.com/nodejs/node-gyp/issues/569#issue-55705963).

This should cover most scenarios for installing and using Grow.

## Using the development server

Grow comes with a built-in development server. The development server dynamically renders and builds pages when requested. This avoids the need to watch files for changes and allows you to iteratively develop without rebuilding your entire site.

You can start the server with the `grow run` command:

```txt
grow run
```

When you start the development server, Grow checks for updates to the SDK, compiles translation catalogs, and runs any preprocessors configured in `podspec.yaml`.

The development server does not currently integrate with any other preprocessing systems, such as Gulp. You must execute those manually.

## Remote access

By default, the development server binds to `localhost` to avoid accidentally providing anyone from accessing your development server. If you need to access the development server from other devices on your local network, use the `--host` and `--port` flags to explicitly set the host and port parameters, respectively.

```bash
grow run --host=0.0.0.0 --port=8080
```

## Web console

The development server includes a basic web console that provides information about your site. Use the console to quickly audit your site's routes, collections, and translations.

Access the console by visiting `http://host:port/_grow`.

## pipenv

Install Grow from source using `pipenv` – enabling you to run multiple versions of Grow simultaneously.

```bash
# Install pipenv (run this one time).
brew install pipenv

# Activate a shell, install and run Grow from within your project folder.
pipenv shell
pip install grow==1.0.0a4
grow run
```
