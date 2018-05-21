"""Core extensions."""

from . import pod_extension
from . import podcache_extension
from . import routes_extension

EXTENSIONS = (
    pod_extension.PodExtension,
    podcache_extension.PodcacheExtension,
    routes_extension.RoutesExtension,
)
