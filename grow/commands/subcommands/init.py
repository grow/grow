"""Subcommand to initialize a new pod."""

import os
import click
from grow.commands import shared
from grow.common import rc_config
from grow.pods import pods
from grow import storage
from grow.sdk import themes


CFG = rc_config.RC_CONFIG.prefixed('grow.init')


@click.command()
@click.argument('theme')
@shared.pod_path_argument
@click.option('--force', default=False, is_flag=True,
              help='Whether to overwrite existing files.')
def init(theme, pod_path, force):
    """Initializes a pod with a theme."""
    root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
    pod = pods.Pod(root, storage=storage.FileStorage)
    with pod.profile.timer('grow_init'):
        theme = themes.GrowTheme(theme)
        theme.extract(pod, force=force)
    return pod
