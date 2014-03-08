# Grow SDK [![Build Status](https://travis-ci.org/grow/pygrow.png?branch=master)](https://travis-ci.org/grow/pygrow)

Welcome to the Grow SDK! Grow is almost certainly the best way for teams to build and launch web sites. It's a file-based static site generator and content management system.

Grow works great for all kinds of content-heavy web sites – fom small personal blogs, to highly-interactive marketing campaigns, to informational web sites for a large organization.

Grow differentiates itself by being:

- entirely file-based and backed by Git (so it works with your favorite tools),
- designed for true structured content management,
- designed with web performance and security in mind,
- designed for developers, designers, content writers, and translators to work together,
- fully international with built-in localization support.

Using Grow, you can:

- develop everywhere (cloud or local, in a browser or on your machine),
- deploy anywhere (Google Cloud Storage, S3, Dropbox, GitHub pages, App Engine, your custom server, etc.),
- launch web sites on demand or at a specific time,
- manage multiple sites (instead of just one),
- collaborate with people, teams, and organizations (via roles, review processes, and project organization).

Visit the Grow SDK's website at http://growsdk.org where you can learn all about using the Grow SDK to build and launch your own web sites.

## In development

The Grow SDK is still under development and is *not quite ready for use*. If you're interested in learning more about the project, please visit the SDK's public website at http://growsdk.org where you can subscribe to our newsletter and be notified when the . You can also watch this repository for updates.

## Quick start usage

Full documentation is available at http://growsdk.org, but this four-step process covers the basic workflow.

(1) Install Grow. (Coming soon: a downloadable Mac application for those without `pip`.)

    # Install Grow in Python's site-packages directory.
    sudo pip install grow

    # Or install Grow for a single user (recommended).
    pip install --user grow

    # Add --user pip installations to your PATH. (Put this in ~/.bashrc).
    export PATH=$HOME/.local/bin:$PATH

(2) Initialize a new pod using the "cards" theme.

    grow init cards ~/example.com/

(3) Run a small web server for live editing and previewing.

    grow run ~/example.com/

(4) Deploy your site to the public web.

    grow deploy ~/example.com/

See a full list of commands using: `grow help`.

## Contributing

### Getting the code

We recommend using `virtualenv` to work on Grow in order to keep your system-wide installation separate from your working copy.

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
