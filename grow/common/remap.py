"""Recursive data structure remapping utility (replaces boltons.iterutils.remap)."""

from collections.abc import Mapping


def default_exit(path, key, old_parent, new_parent, new_items):
    """Populate a newly constructed container with remapped items."""
    if isinstance(new_parent, Mapping):
        new_parent.update(new_items)
        return new_parent
    if isinstance(new_parent, list):
        new_parent.extend(v for _, v in new_items)
        return new_parent
    if isinstance(new_parent, set):
        new_parent.update(v for _, v in new_items)
        return new_parent
    if isinstance(new_parent, tuple):
        return type(old_parent)(v for _, v in new_items)
    return new_parent


def _enter(obj):
    if isinstance(obj, Mapping):
        return type(obj)(), obj.items()
    if isinstance(obj, list):
        return type(obj)(), enumerate(obj)
    if isinstance(obj, set):
        return type(obj)(), enumerate(obj)
    if isinstance(obj, tuple) and not hasattr(obj, '_fields'):
        return (), enumerate(obj)
    return None, None


def remap(root, visit=None, exit=None):
    """Recursively traverse and transform nested mappings and sequences."""
    exit_fn = exit or default_exit

    def _remap(obj, path, key):
        new_parent, items = _enter(obj)
        if items is None:
            return obj

        new_items = []
        for k, v in items:
            child_path = (*path, k)
            if _enter(v)[1] is not None:
                v = _remap(v, child_path, k)
            if visit is not None:
                visited = visit(path, k, v)
                if visited is False:
                    continue
                if visited is True:
                    new_k, new_v = k, v
                else:
                    new_k, new_v = visited
            else:
                new_k, new_v = k, v
            new_items.append((new_k, new_v))

        return exit_fn(path, key, obj, new_parent, new_items)

    return _remap(root, (), None)
