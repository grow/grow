"""Core extensions."""

from . import deployment_extension
from . import node_extension
from . import pod_extension
from . import podcache_extension
from . import routes_extension

EXTENSIONS = (
    deployment_extension.DeploymentExtension,
    node_extension.NodeExtension,
    pod_extension.PodExtension,
    podcache_extension.PodcacheExtension,
    routes_extension.RoutesExtension,
)
