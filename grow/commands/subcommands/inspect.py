"""Subcommand for inspecting pods."""

import click
from grow.commands.subcommands import inspect_routes
from grow.commands.subcommands import inspect_stats


@click.group()
def inspect():
    """Inspects a pod."""
    pass


# Add the sub commands.
inspect.add_command(inspect_routes.routes)
inspect.add_command(inspect_stats.stats)
