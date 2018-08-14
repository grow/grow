"""Utilities around the system that Grow is running on."""

import os
import platform
import sys


if 'Linux' in platform.system():
    PLATFORM = 'linux'
elif 'Darwin' in platform.system():  # pragma: no cover
    PLATFORM = 'mac'
elif 'Windows' in platform.system():  # pragma: no cover
    PLATFORM = 'win'
else:  # pragma: no cover
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
