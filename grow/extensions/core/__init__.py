"""Core extensions."""

from . import (
    deployment_extension,
    node_extension,
    pod_extension,
    podcache_extension,
    routes_extension,
)

EXTENSIONS = (
    deployment_extension.DeploymentExtension,
    node_extension.NodeExtension,
    pod_extension.PodExtension,
    podcache_extension.PodcacheExtension,
    routes_extension.RoutesExtension,
)
