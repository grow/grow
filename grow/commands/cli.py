"""Grow CLI command."""

import click
from grow.commands import build
from grow.common import system

HELP_TEXT = ('Grow is a declarative file-based website generator. Read docs at '
             'https://grow.io. This is version {}.'.format(system.VERSION))

# pylint: disable=unused-argument
@click.group(help=HELP_TEXT)
@click.version_option(system.VERSION, message='%(version)s')
@click.option('--profile',
              default=False, is_flag=True,
              help='Show report of grow timing for performance analysis.')
def grow(profile):
    """Grow CLI command."""
    pass


@grow.resultcallback()
def process_subcommands(pod, profile, **_):
    """Handle profiling the subcommands."""

    if not pod:
        return

    if profile:
        # TODO: Write the profile report out to the file system.
        pass


grow.add_command(build.build)
