There are two ways to install the Grow SDK. If you're unsure, stick with the Mac app. Regardless of how you get Grow, you run it using the command line command `grow`. The source code for all Grow SDK distributions is [open source](https://github.com/grow).

### Mac OS X app

You can download the Grow SDK as an OS X application. The entire SDK is packaged into the app, which is just a Unix executable.

<a href="https://github.com/grow/macgrow/releases" class="button button-primary"><i class="fa fa-download"></i>Download Grow SDK for Mac</a>

See usage below. You __must start the app using Terminal__, and not by double clicking.

    # Shows help for the Grow SDK executable.
    ./grow

You can install an alias in order to use `grow` anywhere.

    # Modify "<path>" below, then add the below line to ~/.bash_profile.
    alias grow='<path to grow>/grow'

    # After editing ~/.bash_profile, run...
    source ~/.bash_profile

### Python egg

Alternatively, the Grow SDK is a Python program, so you can run it practically anywhere you can run Python. You can install Grow with [pip](http://pypi.python.org/pypi/pip).

    # Installs Grow in Python's site-packages directory.
    sudo pip install grow

    # Or, install Grow for a single user.
    pip install --user grow

    # If you have Grow already, upgrade it.
    pip install --upgrade [--user] grow
