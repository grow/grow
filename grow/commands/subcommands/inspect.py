"""Subcommand for inspecting pods."""

import click
from grow.commands.subcommands import inspect_routes
from grow.commands.subcommands import inspect_stats
from grow.commands.subcommands import inspect_untranslated


@click.group()
def inspect():
    """Inspect pod files and stats."""
    pass


# Add the sub commands.
inspect.add_command(inspect_routes.inspect_routes)
inspect.add_command(inspect_stats.inspect_stats)
inspect.add_command(inspect_untranslated.inspect_untranslated)
