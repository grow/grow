"""Grow CLI commands."""

from grow.commands.subcommands import (
    build,
    convert,
    deploy,
    inspect,
    install,
    preprocess,
    run,
    stage,
    translations,
)


def add_subcommands(group):
    """Add all subcommands to a group."""
    group.add_command(build.build)
    group.add_command(convert.convert)
    group.add_command(deploy.deploy)
    group.add_command(inspect.inspect)
    group.add_command(install.install)
    group.add_command(preprocess.preprocess)
    group.add_command(run.run)
    group.add_command(stage.stage)
    group.add_command(translations.translations)
