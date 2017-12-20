"""Subcommand for working with translations."""

import click
from grow.commands.subcommands import translations_download
from grow.commands.subcommands import translations_extract
from grow.commands.subcommands import translations_filter
from grow.commands.subcommands import translations_import
from grow.commands.subcommands import translations_machine
from grow.commands.subcommands import translations_upload


@click.group()
def translations():
    """Translation operations for the pod."""
    pass


# Add the sub commands.
translations.add_command(translations_download.translations_download)
translations.add_command(translations_extract.translations_extract)
translations.add_command(translations_filter.translations_filter)
translations.add_command(translations_import.translations_import)
translations.add_command(translations_machine.translations_machine)
translations.add_command(translations_upload.translations_upload)
