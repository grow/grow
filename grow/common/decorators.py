"""Grow decorators."""

import functools


# pylint: disable=too-few-public-methods
class Memoize(object):
    """A decorator that lazily caches the result of the function call.

        class Foo(object):

            @memoize
            def foo(self):
                # calculate something important here
                return 42
    """

    def __init__(self, func):
        self.func = func
        self.cache = {}

    def __call__(self, *args, **kwargs):
        key = (args, frozenset(kwargs.items()))
        try:
            return self.cache[key]
        except KeyError:
            value = self.func(*args, **kwargs)
            self.cache[key] = value
            return value
        except TypeError:
            return self.func(*args, **kwargs)

    def __repr__(self):
        return self.func.__doc__

    def __get__(self, obj, objtype):
        func = functools.partial(self.__call__, obj)
        func.reset = self._reset
        return func

    def _reset(self):
        self.cache = {}


# pylint: disable=too-few-public-methods
class MemoizeTag(Memoize):
    """A decorator that optionally lazily caches the result of the function call.

    Controls the memoize with a `use_cache` kwarg to determine if it should
    skip the cache.
    """

    def __call__(self, *args, **kwargs):
        use_cache = kwargs.pop('use_cache', True)
        if use_cache is True:
            return super(MemoizeTag, self).__call__(*args, **kwargs)
        return self.func(*args, **kwargs)
