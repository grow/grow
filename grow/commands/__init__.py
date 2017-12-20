"""Grow CLI commands."""

from grow.commands.subcommands import build
from grow.commands.subcommands import convert
from grow.commands.subcommands import deploy
from grow.commands.subcommands import init
from grow.commands.subcommands import inspect
from grow.commands.subcommands import install
from grow.commands.subcommands import preprocess
from grow.commands.subcommands import run
from grow.commands.subcommands import stage
from grow.commands.subcommands import translations


def add_subcommands(group):
    """Add all subcommands to a group."""
    group.add_command(build.build)
    group.add_command(convert.convert)
    group.add_command(deploy.deploy)
    group.add_command(init.init)
    group.add_command(inspect.inspect)
    group.add_command(install.install)
    group.add_command(preprocess.preprocess)
    group.add_command(run.run)
    group.add_command(stage.stage)
    group.add_command(translations.translations)
