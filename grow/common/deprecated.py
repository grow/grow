"""Deprecation helper for warning users of deprecated classes."""

import logging

# pylint: disable=too-few-public-methods
class DeprecationHelper(object):
    """Deprecation helper class for deprecating a class."""

    def __init__(self, new_target, message, warn=logging.warn):
        self.new_target = new_target
        self.message = message
        self._warning = warn
        self._has_warned = False

    def _warn(self):
        # Only warn once to prevent spamming logs.
        if not self._has_warned:
            self._warning(self.message)
            self._has_warned = True

    def __call__(self, *args, **kwargs):
        self._warn()
        return self.new_target(*args, **kwargs)

    def __getattr__(self, attr):
        self._warn()
        return getattr(self.new_target, attr)


# pylint: disable=too-few-public-methods
class MovedHelper(DeprecationHelper):
    """Specialized deprecation helper for warning of moved classes."""

    def __init__(self, new_target, orig_class_name, *args, **kwargs):
        new_class_name = new_target.__module__ + "." + new_target.__name__
        message = 'The {} class has moved to {} and will be removed in a future version.'.format(
            orig_class_name, new_class_name)
        super(MovedHelper, self).__init__(new_target, message, *args, **kwargs)
