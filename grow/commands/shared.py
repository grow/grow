"""Shared options or arguments for cli commands."""

import click


def pod_path_argument(func):
    """Argument for pod path."""
    return click.argument('pod_path', default='.')(func)


def deployment_option(func):
    """Option for changing env based on deployment name."""
    return click.option(
        '--deployment', default=None, help='Name of the deployment config to use.')(func)


def reroute_option(func):
    """Option for using new age router and rendering pipeline."""
    return click.option(
        '--re-route', 'use_reroute', is_flag=True, default=False,
        help='Use experimental routing/rendering pipeline.')(func)
