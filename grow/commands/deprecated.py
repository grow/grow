"""Click deprecated groups."""

import logging
import click
from click.utils import make_str


# pylint: disable=too-few-public-methods
class DeprecatedItem(object):
    """Configuration for an alias item."""

    def __init__(self, old_name, new_name, cmd=None):
        self.old_name = old_name
        self.new_name = new_name
        self.cmd = cmd


class DeprecatedGroup(click.Group):
    """Group support for deprecating commands."""

    def __init__(self, name=None, commands=None, deprecated=None, **attrs):
        click.Group.__init__(self, name, commands, **attrs)
        self.deprecated = deprecated or []

    def resolve_command(self, ctx, args):
        """Override how the command is resolved to check for deprecated."""
        cmd_name = make_str(args[0])

        for item in self.deprecated:
            if item.old_name == cmd_name:
                message = ('The `{}` command has moved to `{}` '
                           'and will be removed in a future version.')
                logging.warn(message.format(cmd_name, item.new_name))
                return cmd_name, item.cmd, args[1:]
        return click.Group.resolve_command(self, ctx, args)
