"""Loads extensions from local extensions."""

from . import utils
import imp
import os
import sys

MAC_SYS_PREFIX = '/System/Library/Frameworks/Python.framework/Versions/3.7'
NO_CHANGE_PATHS = bool(os.environ.get('GROW_NO_CHANGE_PATH', False))


def _get_module(part1, paths):
    fp, pathname, description = imp.find_module(part1, paths)
    return imp.load_module(part1, fp, pathname, description)


def import_extension(name, paths):
    """Imports and returns a module, given its path (e.g.
    extensions.foo.Bar)."""
    if '.' not in name:
        raise ImportError
    part1, part2 = name.split('.', 1)
    if '.' in part2:
        fp, pathname, description = imp.find_module(part1, paths)
        return import_extension(part2, [pathname])

    if NO_CHANGE_PATHS:
        # Unable to find the module and cannot change the PATH.
        raise ImportError
    else:
        original_sys_path = sys.path[:]
        original_sys_prefix = sys.prefix
        if os.path.exists(MAC_SYS_PREFIX):
            sys.prefix = MAC_SYS_PREFIX
        from . import patched_site  # Updates sys.path.
        patched_site.main()
        try:
            module = _get_module(part1, paths)
        finally:
            # If extension modifies sys.path, preserve the modification.
            sys.prefix = original_sys_prefix
            sys.path = original_sys_path
    result = getattr(module, part2)
    return result
