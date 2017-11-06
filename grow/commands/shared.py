"""Shared options or arguments for cli commands."""

import click
from grow.common import rc_config


CFG = rc_config.RC_CONFIG.prefixed('grow.shared')


def pod_path_argument(func):
    """Argument for pod path."""
    return click.argument('pod_path', default='.')(func)


def deployment_option(config):
    """Option for changing env based on deployment name."""
    shared_default = CFG.get('deployment', False)
    config_default = config.get('deployment', shared_default)
    def _decorator(func):
        return click.option(
            '--deployment', default=config_default,
            help='Name of the deployment config to use.')(func)
    return _decorator


def reroute_option(config):
    """Option for using new age router and rendering pipeline."""
    shared_default = CFG.get('re-route', False)
    config_default = config.get('re-route', shared_default)
    def _decorator(func):
        return click.option(
            '--re-route', 'use_reroute', is_flag=True, default=config_default,
            help='Use experimental routing/rendering pipeline.')(func)
    return _decorator
