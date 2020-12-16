"""Grow deployment management."""

from protorpc import protojson
import json


class Deployments:
    """Manage the deployment destinations."""

    def __init__(self):
        self._deployments = {}

    @staticmethod
    def config_from_json(deployment_cls, content):
        """Create a deployment config from json content."""
        config_cls = deployment_cls.Config
        return protojson.decode_message(config_cls, content)

    def register_destination(self, destination_cls):
        """Register or override a deployment destination."""
        self._deployments[destination_cls.KIND] = destination_cls

    def make_deployment(self, kind, config, name='default'):
        """Create an instance of the deployment destination."""
        destination_cls = self._deployments.get(kind)
        if destination_cls is None:
            raise ValueError('No deployment destination exists for "{}".'.format(kind))

        if isinstance(config, dict):
            config = json.dumps(config)
        if not config:
            config = '{}'
        config = self.config_from_json(destination_cls, config)
        return destination_cls(config, name=name)
