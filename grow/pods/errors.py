class Error(Exception):
    """Base Exception class for module."""


class RouteNotFoundError(Error, KeyError):
    """Raised when a resource is not found within the pod."""


class NoPathError(Error, ValueError):
    """Raised when a path is requested for a resource that doesn't have one."""


class PodConfigurationError(Error, ValueError):
    pass


class PodNotFoundError(Error):
    pass


class TestFailedError(Error, AssertionError):
    pass


class BuildError(Error):
    exception = None
    controller = None


class BadNameError(Error, ValueError):
    pass


class BadYamlError(Error, ValueError):
    pass
