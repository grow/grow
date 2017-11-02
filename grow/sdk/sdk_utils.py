"""Utility functions for managing the sdk."""

import platform
from grow.common import config


VERSION = config.VERSION
PLATFORM = None
if 'Linux' in platform.system():
    PLATFORM = 'linux'
elif 'Darwin' in platform.system():
    PLATFORM = 'mac'
elif 'Windows' in platform.system():
    PLATFORM = 'win'
