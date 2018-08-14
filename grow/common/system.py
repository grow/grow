"""Utilities around the system that Grow is running on."""

import os
import platform
import sys


# pragma: no cover
if 'Linux' in platform.system():
    PLATFORM = 'linux'
elif 'Darwin' in platform.system():
    PLATFORM = 'mac'
elif 'Windows' in platform.system():
    PLATFORM = 'win'
else:
    PLATFORM = None


try:
    # pylint: disable=protected-access
    VERSION = open(os.path.join(sys._MEIPASS, 'VERSION')).read().strip()
except AttributeError:
    VERSION = open(os.path.join(os.path.dirname(__file__), '..', 'VERSION')).read().strip()


def is_packaged_app():
    """Returns whether the environment is a packaged app."""
    try:
        # pylint: disable=pointless-statement,protected-access
        sys._MEIPASS
        return True
    except AttributeError:
        return False
