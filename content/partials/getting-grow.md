There are two ways to install the Grow SDK, depending on the platform you're using. Regardless of how you get Grow, you run it using the command line command `grow`.

### Mac OS X (packaged app)

*To install the Grow SDK on Mac OS X, paste the following command into Terminal.* This command downloads the SDK, which is packaged into an application, and sets up an alias. Before anything is done, you will be prompted to continue.

    curl https://raw.githubusercontent.com/grow/pygrow/master/install | bash && source ~/.bash_profile

### Linux/Unix (Python egg)

On Linux/Unix, you can install the Grow SDK with [pip](http://pypi.python.org/pypi/pip).

    # Installs Grow in Python's site-packages directory.
    sudo pip install grow

    # Or, install Grow for a single user.
    pip install --user grow

    # If you have Grow already, upgrade it.
    pip install --upgrade [--user] grow

The source code for all Grow SDK distributions is [open source](https://github.com/grow). You can learn more about the latest release from the [releases page](https://github.com/grow/pygrow/releases).
