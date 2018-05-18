"""Core extensions."""

from . import podcache_extension
from . import routes_extension

EXTENSIONS = (
    podcache_extension.PodcacheExtension,
    routes_extension.RoutesExtension,
)
