import logging
import sys

from grow import commands
from grow.commands import group
commands.add_subcommands(group.grow)

logging.basicConfig(level=logging.INFO, format='%(message)s')


def main(as_module=False):
    args = sys.argv[1:]
    name = None
    if as_module:
        name = 'python -m grow'
        sys.argv = ['-m', 'grow'] + args
    group.grow.main(args=args, prog_name=name)


if __name__ == '__main__':
    main(as_module=True)