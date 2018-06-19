"""Utilities around the system that Grow is running on."""

import sys

def is_packaged_app():
    """Returns whether the environment is a packaged app."""
    try:
        # pylint: disable=pointless-statement,protected-access
        sys._MEIPASS
        return True
    except AttributeError:
        return False
