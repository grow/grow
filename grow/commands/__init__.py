"""Grow CLI commands."""

from grow.commands import group as grow_group


def add_subcommands(group):
    """Register lazy subcommands on a Click group."""
    if hasattr(group, 'lazy_subcommands'):
        group.lazy_subcommands.update(grow_group.LAZY_SUBCOMMANDS)
        return
    import importlib

    for name, (module_name, attr_name) in grow_group.LAZY_SUBCOMMANDS.items():
        if name not in group.commands:
            module = importlib.import_module(module_name)
            group.add_command(getattr(module, attr_name), name=name)
