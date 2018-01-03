"""Base command for grow."""

import os
import click
from grow.commands import deprecated
from grow.commands.subcommands import inspect_routes
from grow.commands.subcommands import inspect_stats
from grow.commands.subcommands import translations_download
from grow.commands.subcommands import translations_extract
from grow.commands.subcommands import translations_filter
from grow.commands.subcommands import translations_import
from grow.commands.subcommands import translations_machine
from grow.commands.subcommands import translations_upload
from grow.common import config
from grow.deployments.destinations import local as local_destination

HELP_TEXT = ('Grow is a declarative file-based website generator. Read docs at '
             'https://grow.io. This is version {}.'.format(config.VERSION))

# pylint: disable=unused-argument
@click.group(
    cls=deprecated.DeprecatedGroup, help=HELP_TEXT,
    # TODO: Remove after deprecation period.
    deprecated=[
        deprecated.DeprecatedItem(
            'download_translations', 'translations download',
            cmd=translations_download.translations_download),
        deprecated.DeprecatedItem(
            'extract', 'translations extract',
            cmd=translations_extract.translations_extract),
        deprecated.DeprecatedItem(
            'filter', 'translations filter',
            cmd=translations_filter.translations_filter),
        deprecated.DeprecatedItem(
            'import_translations', 'translations import',
            cmd=translations_import.translations_import),
        deprecated.DeprecatedItem(
            'machine_translate', 'translations machine',
            cmd=translations_machine.translations_machine),
        deprecated.DeprecatedItem(
            'routes', 'inspect routes',
            cmd=inspect_routes.inspect_routes),
        deprecated.DeprecatedItem(
            'stats', 'inspect stats',
            cmd=inspect_stats.inspect_stats),
        deprecated.DeprecatedItem(
            'upload_translations', 'translations upload',
            cmd=translations_upload.translations_upload),
    ])
@click.version_option(config.VERSION, message='%(version)s')
@click.option('--auth', help='Information used to sign in to services that'
              ' require authentication. --auth should be an email address.',
              envvar='GROW_AUTH')
@click.option('--clear-auth', default=False, is_flag=True,
              help='Clears stored auth information.')
@click.option('--auth-key-file', help='Path to a private key file used for'
              ' services that require authentication.', envvar='GROW_KEY_FILE')
@click.option(
    '--interactive-auth', default=False, is_flag=True,
    envvar='INTERACTIVE_AUTH',
    help='Whether to automatically open an authorization page in your'
         ' default web browser for any steps that require authentication.'
         ' If you are running Grow on a machine with access to a web browser,'
         ' you may use --interactive-auth to automatically open the web'
         ' browser. By default, this option is turned off, requiring you to'
         ' manually copy and paste an authorization code.')
@click.option('--profile',
              default=False, is_flag=True,
              help='Show report of pod operation timing for performance analysis.')
def grow(auth, clear_auth, auth_key_file, interactive_auth, profile):
    """Grow CLI command."""
    if interactive_auth not in (None, False):
        os.environ['INTERACTIVE_AUTH'] = str(interactive_auth)
    if auth is not None:
        os.environ['AUTH_EMAIL_ADDRESS'] = str(auth)
    if auth_key_file is not None:
        os.environ['AUTH_KEY_FILE'] = str(auth_key_file)
    if clear_auth:
        os.environ['CLEAR_AUTH'] = '1'


@grow.resultcallback()
def process_subcommands(pod, profile, **_):
    """Handle flags that need to process after the sub command."""

    if not pod:
        return

    if profile:
        destination = local_destination.LocalDestination(
            local_destination.Config())
        destination.pod = pod
        destination.export_profile_report()
