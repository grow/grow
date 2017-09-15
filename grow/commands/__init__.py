"""Grow CLI commands."""

from grow.commands.subcommands import build
from grow.commands.subcommands import convert
from grow.commands.subcommands import deploy
from grow.commands.subcommands import download_translations
from grow.commands.subcommands import extract
from grow.commands.subcommands import filter as grow_filter
from grow.commands.subcommands import import_translations
from grow.commands.subcommands import init
from grow.commands.subcommands import install
from grow.commands.subcommands import machine_translate
from grow.commands.subcommands import preprocess
from grow.commands.subcommands import routes
from grow.commands.subcommands import run
from grow.commands.subcommands import stage
from grow.commands.subcommands import stats
from grow.commands.subcommands import upload_translations


def add_subcommands(group):
    """Add all subcommands to a group."""
    group.add_command(build.build)
    group.add_command(convert.convert)
    group.add_command(deploy.deploy)
    group.add_command(download_translations.download_translations)
    group.add_command(extract.extract)
    group.add_command(grow_filter.filter)
    group.add_command(import_translations.import_translations)
    group.add_command(init.init)
    group.add_command(machine_translate.machine_translate)
    group.add_command(preprocess.preprocess)
    group.add_command(routes.routes)
    group.add_command(run.run)
    group.add_command(install.install)
    group.add_command(stats.stats)
    group.add_command(stage.stage)
    group.add_command(upload_translations.upload_translations)
