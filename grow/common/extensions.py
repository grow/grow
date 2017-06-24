"""Loads extensions, with a workaround for the frozen version."""

# NOTE: Here be demons, specifically for the packaged application. There are no
# demons present here when Grow runs in the normal environment. The very
# concept of importing and running external "plugin-like" code is antithetical
# to PyInstaller, whose goal is to package everything necessary for running a
# program into a single executable. However, we need to support the extension
# system in Grow, allowing users to write and run arbitrary Python code (which
# may or may not depend on other, external libraries).
#
# We attempted to include the entire stdlib in with the packaged app
# (https://github.com/grow/grow/commit/b4530658), though that wasn't
# sufficient. The Python stdlib os.py module has its own platform-specific
# magic that is performed upon execution, which was bizarrely incompatible with
# PyInstaller's module importers (on sys.meta_path). Other users of
# PyInstaller, attempting to implement something similar, encountered similar
# errors (https://stackoverflow.com/q/35254139).
#
# That wasn't enough, though, because other bizarre errors related to the
# stdlib would occur. Specifically, modules had difficulty importing the
# `exceptions` module. None of these errors would occur if these libraries
# simply relied on the system's `site-packages` and system Python library. To
# permit extensions to rely on the system `site-packages`, we can import
# Python's `site` module, which sets `sys.path` depending on the system.
# Normally that would be enough, but PyInstaller overwrites the system `site`
# module with a `site` module that specifically prevents this behavior
# (https://github.com/pyinstaller/pyinstaller/issues/510).
#
# To permit extensions to rely on the system libraries, we overwite
# PyInstaller's `site` module with our vendored copy of the default `site`
# module from Python (which we're calling `patched_site.py`. This was not
# enough, though, and we had to make one modification to `patched_site.py`'s
# main: preventing a magic function (`abs__file__()`) from being executed since
# its behavior was also not compatible with PyInstaller.
#
# After all is said and done, we reset `sys.path` after the extension is
# loaded, to prevent any permanent changes during runtime. There may be a more
# intelligent way to fix this situation by writing a custom module loader and
# inserting it into `sys.meta_path`, but I was unable to do that.

from . import utils
import imp
import sys

IS_PACKAGED_APP = utils.is_packaged_app()


def import_extension(name, paths):
    """Imports and returns a module, given its path (e.g.
    extensions.foo.Bar)."""
    if '.' not in name:
        raise ImportError
    part1, part2 = name.split('.', 1)
    if '.' in part2:
        fp, pathname, description = imp.find_module(part1, paths)
        return import_extension(part2, [pathname])
    if IS_PACKAGED_APP:
        original_sys_path = sys.path[:]
        import patched_site
    fp, pathname, description = imp.find_module(part1, paths)
    module = imp.load_module(part1, fp, pathname, description)
    result = getattr(module, part2)
    if IS_PACKAGED_APP:
        sys.path = original_sys_path
    return result
