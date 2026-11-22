"""Base command for grow."""

import importlib
import os

import click

import grow as grow_pkg

version = grow_pkg.__version__

HELP_TEXT = (
    'Grow is a declarative file-based website generator. Read docs at '
    f'https://grow.dev. This is version {version}.'
)

LAZY_SUBCOMMANDS = {
    'build': ('grow.commands.subcommands.build', 'build'),
    'convert': ('grow.commands.subcommands.convert', 'convert'),
    'deploy': ('grow.commands.subcommands.deploy', 'deploy'),
    'inspect': ('grow.commands.subcommands.inspect', 'inspect'),
    'install': ('grow.commands.subcommands.install', 'install'),
    'preprocess': ('grow.commands.subcommands.preprocess', 'preprocess'),
    'run': ('grow.commands.subcommands.run', 'run'),
    'stage': ('grow.commands.subcommands.stage', 'stage'),
    'translations': ('grow.commands.subcommands.translations', 'translations'),
}


class LazyGroup(click.Group):
    """Click group that imports subcommand modules lazily on first use."""

    def __init__(self, *args, lazy_subcommands=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.lazy_subcommands = dict(lazy_subcommands or {})

    def list_commands(self, ctx):
        names = set(super().list_commands(ctx))
        names.update(self.lazy_subcommands)
        return sorted(names)

    def get_command(self, ctx, cmd_name):
        if cmd_name in self.commands:
            return self.commands[cmd_name]
        if cmd_name in self.lazy_subcommands:
            module_name, attr_name = self.lazy_subcommands[cmd_name]
            module = importlib.import_module(module_name)
            cmd = getattr(module, attr_name)
            self.add_command(cmd, name=cmd_name)
            return cmd
        return super().get_command(ctx, cmd_name)


@click.group(cls=LazyGroup, lazy_subcommands=LAZY_SUBCOMMANDS, help=HELP_TEXT)
@click.version_option(prog_name='grow', version=version)
@click.option(
    '--auth',
    help='Information used to sign in to services that'
    ' require authentication. --auth should be an email address.',
    envvar='GROW_AUTH',
)
@click.option('--clear-auth', default=False, is_flag=True, help='Clears stored auth information.')
@click.option(
    '--auth-key-file',
    help='Path to a private key file used for services that require authentication.',
    envvar='GROW_KEY_FILE',
)
@click.option(
    '--interactive-auth/--no-interactive-auth',
    default=True,
    is_flag=True,
    envvar='INTERACTIVE_AUTH',
    help='Use the browser-based localhost OAuth callback flow (default).'
    ' Google deprecated the legacy out-of-band (OOB) copy-paste flow;'
    ' for headless or CI environments, pass --auth-key-file instead.',
)
@click.option(
    '--profile',
    default=False,
    is_flag=True,
    help='Show report of pod operation timing for performance analysis.',
)
def grow(auth, clear_auth, auth_key_file, interactive_auth, profile):
    """Grow CLI command."""
    if interactive_auth is False:
        os.environ['NO_INTERACTIVE_AUTH'] = '1'
        os.environ.pop('INTERACTIVE_AUTH', None)
    else:
        os.environ.pop('NO_INTERACTIVE_AUTH', None)
        os.environ['INTERACTIVE_AUTH'] = 'True'
    if auth is not None:
        os.environ['AUTH_EMAIL_ADDRESS'] = str(auth)
    if auth_key_file is not None:
        os.environ['AUTH_KEY_FILE'] = str(auth_key_file)
    if clear_auth:
        os.environ['CLEAR_AUTH'] = '1'


@grow.result_callback()
def process_subcommands(pod, profile, **_):
    """Handle flags that need to process after the sub command."""

    if not pod:
        return

    if profile:
        from grow.deployments.destinations import local as local_destination

        destination = local_destination.LocalDestination(local_destination.Config())
        destination.pod = pod
        destination.export_profile_report()
