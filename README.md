# Grow SDK [![Build Status](https://travis-ci.org/grow/pygrow.png?branch=master)](https://travis-ci.org/grow/pygrow)

Welcome to the Grow SDK, the declarative file-based CMS and static site generator for building high-quality web sites.

Grow is almost certainly the best way for teams to build and launch web sites. It works great for all kinds of content-heavy web sites – from small personal blogs, to highly-interactive marketing campaigns, to informational web sites for a large organization.

Grow differentiates itself by being:

- entirely file-based and backed by Git (so it works with your favorite tools),
- the best and easiest way to develop content-heavy localized websites,
- designed for true structured content management,
- designed with web performance and security in mind,
- designed with first-party i18n support,
- designed for developers, designers, content writers, and translators to work together.

Visit the Grow SDK's website at http://growsdk.org where you can learn all about using the Grow SDK to build and launch your own web sites.

## Experimental!

The Grow SDK is still under development and is *considered experimental*. We may make backwards-incompatible changes to the API and design until v0.1.0. Please consult the documentation at http://growsdk.org, [join the mailing list](https://groups.google.com/forum/#!forum/growsdk), give it a try, and provide feedback.

## Quick start usage

Full documentation is available at https://growsdk.org, but this four-step process covers the basic workflow. See a full list of commands using: `grow --help`.

(1) Install Grow. You will be prompted to continue.

    curl https://install.growsdk.org | bash

(2) Initialize a new pod using the "codelab" theme.

    grow init codelab ~/example.com/

(3) Run a development web server for live editing and previewing.

    grow run ~/example.com/

(4) Build your site.

    grow build ~/example.com/

By using the installer from `install.growsdk.org`, you can take advantage of the autoupdater. If you'd prefer to build yourself or install Grow another way (such as `pip`), see [installation alternatives](#installation-alternatives).

## Contributing

We welcome pull requests, themes, bug fixes, feature suggestions, cake, and any other sort of feedback.

### Issues and roadmap

We use GitHub to track issues. Feel free to [browse issues](https://github.com/grow/pygrow/issues "browse issues") and look for any issues pertaining to the features you'd like to work on and claim them. If the feature warrants discussion, conduct a discussion with the project authors in the GitHub issue or on the mailing list.

### Getting the code

For contributors, Grow includes a setup script to help you get a development environment setup for running the tests and executing the command line tools. The setup script helps install `pip`, `virtualenv`, and all of the libraries required to perform development.

    git clone git@github.com:grow/pygrow.git       # Clones this repo.
    cd pygrow
    ./scripts/setup                                # Runs setup script.

Once installed, you can...

    ./scripts/test                                 # Runs tests.
    ./scripts/grow                                 # Runs `grow` command line program.

#### Gotchas

From a fresh system, you may need a few things to build a Grow release from scratch:

    sudo apt-get install python-dev python-pip libffi-dev g++ git libxml2-dev libxslt-dev libssl-dev zip
    sudo pip install pyinstaller

#### Installation alternatives

    # Installs Grow in Python's site-packages directory.
    sudo pip install grow

    # Or, install Grow for a single user.
    pip install --user grow

    # If you have Grow already, upgrade it.
    pip install --upgrade [--user] grow

    # Or, build from source.
    git clone git@github.com:grow/pygrow.git
    cd pygrow
    pip install -r requirements.txt
    python setup.py install

### Running tests

To run Grow's unit tests, run from the project's root directory:

    ./scripts/test                                # Runs unit tests.
    ./scripts/test_services                       # Runs service tests.

## License

The Grow SDK is released under the MIT License and it is lovingly developed by the [Grow SDK Project Authors](https://github.com/grow/pygrow/blob/master/LICENSE). Our mission is to bring joy to building and launching high-quality web sites.
