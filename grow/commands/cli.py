"""Grow CLI command."""

import click
from grow.commands import build
from grow.commands import install
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
def process_subcommands(cmd_result, profile, **_):
    """Handle profiling the subcommands."""

    if not cmd_result:
        return

    # When profiling write a summary to command line and write the full
    # raw data to the file system.
    if profile:
        pass


grow.add_command(build.build)
grow.add_command(install.install)
