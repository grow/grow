"""Utilities around the system that Grow is running on."""

import os
import sys

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
