# Grow SDK [![Build Status](https://travis-ci.org/grow/pygrow.png?branch=master)](https://travis-ci.org/grow/pygrow)

Welcome to the Grow SDK, the declarative file-based CMS and static site generator for building high-quality web sites.

Grow is almost certainly the best way for teams to build and launch web sites. It works great for all kinds of content-heavy web sites – fom small personal blogs, to highly-interactive marketing campaigns, to informational web sites for a large organization.

Grow differentiates itself by being:

- entirely file-based and backed by Git (so it works with your favorite tools),
- the best and easiest way to develop content-heavy localized websites,
- designed for true structured content management,
- designed with web performance and security in mind,
- designed for developers, designers, content writers, and translators to work together.

Visit the Grow SDK's website at http://growsdk.org where you can learn all about using the Grow SDK to build and launch your own web sites.

## Experimental!

The Grow SDK is still under development and is *considered experimental*. We may make backwards-incompatible changes to the API and design until v0.1.0. Please consult the documentation at http://growsdk.org, [join the mailing list](https://groups.google.com/forum/#!forum/growsdk), give it a try, and provide feedback.

## Quick start usage

Full documentation is available at http://growsdk.org, but this four-step process covers the basic workflow. See a full list of commands using: `grow help`.

(1) Install Grow.

    # For Mac OS X, paste this command into Terminal. You will be prompted to continue.

    python -c "$(curl -fsSL https://raw.github.com/grow/pygrow/master/install.py)" && source ~/.bash_profile

    # For Linux/Unix, use pip.

    # Installs Grow for a single user (recommended, see below for alternative).
    pip install --user grow

    # Or, installs Grow in Python's site-packages directory.
    sudo pip install grow

    # Add --user pip installations to your PATH. (Put this in ~/.bashrc).
    export PATH=$HOME/.local/bin:$PATH

(2) Initialize a new pod using the "codelab" theme.

    grow init codelab ~/example.com/

(3) Run a live development web server for live editing and previewing.

    grow run ~/example.com/

(4) Deploy your site to the default destination.

    grow deploy ~/example.com/

## Contributing

We welcome pull requests, themes, bug fixes, feature suggestions, cake, and any other sort of feedback.

### Issues and roadmap

We use GitHub to track issues. Feel free to [browse issues](https://github.com/grow/pygrow/issues "browse issues") and look for any issues pertaining to the features you'd like to work on and claim them. If the feature warrants discussion, conduct a discussion with the project authors in the GitHub issue or on the mailing list.

### Getting the code

We recommend using `virtualenv` to work on Grow in order to keep your system-wide installation separate from your working copy.

    sudo pip install virtualenv                   # Install virtualenv if you don't have it.
    virtualenv --no-site-packages <dir>           # Creates a new virtualenv in <dir>.
    cd <dir>
    source bin/activate                           # Activates the virtualenv.
    git clone git@github.com:grow/pygrow.git      # Clones this repo.
    ...
    cd pygrow
    pip install -r requirements.txt
    ...
    ./bin/grow                                    # Runs the Grow command line program.

### Running tests

To run Grow's unit tests, run from the project's root directory:

    python run_tests.py

The Grow SDK also includes service tests, which test the pod server RPC system:

    ./bin/grow run grow/pods/testdata/pod/        # Start a dev server.
    ./run_service_tests.sh

## License

The Grow SDK is released under the MIT License and it is lovingly developed by the [Grow SDK Project Authors](https://github.com/grow/pygrow/blob/master/LICENSE). Our mission is to bring joy to building and launching high-quality web sites.
