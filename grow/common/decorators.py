"""Grow decorators."""

import functools


SENTINEL = object()


# pylint: disable=too-few-public-methods
class Memoize(object):
    """A decorator that lazily caches the result of the function call.

        class Foo(object):

            @Memoize
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
            self.cache[key] = self.func(*args, **kwargs)
            return self.cache[key]
        # except TypeError:
        #     return self.func(*args, **kwargs)

    def __repr__(self):
        return self.func.__doc__

    def reset(self):
        """Reset the memoize cache."""
        self.cache = {}


# pylint: disable=too-few-public-methods
class MemoizeProperty(object):
    """A decorator that lazily caches the result of a property.

        class Foo(object):

            @MemoizeProperty
            def foo(self):
                # calculate something important here
                return 42
    """

    def __init__(self, func):
        self.func = func
        self.cache = {}

    def __repr__(self):
        return self.func.__doc__

    def __get__(self, instance, owner):
        if instance is None:
            return self

        try:
            return self.cache[instance]
        except KeyError:
            self.cache[instance] = self.func(instance)
            return self.cache[instance]

    def reset(self):
        """Reset the memoize cache."""
        self.cache = SENTINEL


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
