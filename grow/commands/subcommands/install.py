"""Subcommand to install grow project dependencies."""

import os
import click
from grow.commands import shared
from grow.common import base_config
from grow.common import rc_config
from grow.pods import pods
from grow import storage
from grow.sdk import installer
from grow.sdk import installers


CFG = rc_config.RC_CONFIG.prefixed('grow.install')


@click.command()
@shared.pod_path_argument
@click.option('--gerrit/--no-gerrit', default=None,
              help='Whether to install the Gerrit Code Review commit hook. '
                   'If omitted, Grow will attempt to detect whether there is a '
                   'known Gerrit host amongst the remotes in your repository.')
@click.option('--force', '-f', default=False, is_flag=True,
             help='Whether to force install even when no changes found.')
@click.option('--ci/--no-ci', default=False,
              help='Whether to use the `npm ci` command instead of the '
                   '`npm install` command.')
def install(pod_path, gerrit, force, ci):
    """Checks whether the pod depends on npm, bower, and gulp and installs them
    if necessary. Then, runs install commands. Also optionally installs the
    Gerrit Code Review commit hook."""
    root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
    pod = pods.Pod(
        root, storage=storage.FileStorage, load_extensions=False)
    with pod.profile.timer('grow_install'):
        config = base_config.BaseConfig()
        config.set('gerrit', gerrit)
        config.set('force', force)
        config.set('ci', ci)
        built_in_installers = []
        for installer_class in installers.BUILT_IN_INSTALLERS:
            built_in_installers.append(installer_class(pod, config))
        grow_installer = installer.Installer(built_in_installers, pod)
        grow_installer.run_installers()
    return pod
