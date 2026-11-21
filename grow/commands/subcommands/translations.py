"""Subcommand for working with translations."""

import click

from grow.commands.subcommands import (
    translations_diff,
    translations_download,
    translations_extract,
    translations_filter,
    translations_import,
    translations_upload,
)


@click.group()
def translations():
    """Translation operations for the pod."""


# Add the sub commands.
translations.add_command(translations_diff.translations_diff)
translations.add_command(translations_download.translations_download)
translations.add_command(translations_extract.translations_extract)
translations.add_command(translations_filter.translations_filter)
translations.add_command(translations_import.translations_import)
translations.add_command(translations_upload.translations_upload)
