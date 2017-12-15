"""Rendering pool for grow documents."""

import random
import threading
from grow.templates import filters
from grow.templates import jinja_dependency
from grow.templates import tags


class Error(Exception):
    """Base rendering pool error."""
    pass


class RenderPool(object):
    """Rendering pool for rendering pods."""

    def __init__(self, pod, pool_size=1):
        self.pod = pod
        self._locales = self.pod.list_locales()
        self._pool_size = pool_size
        self._pool = {}
        self._adjust_pool_size(pool_size)

    @property
    def pool_size(self):
        """How many render environments are being used."""
        return self._pool_size

    @pool_size.setter
    def pool_size(self, value):
        """Set how many render environments are being used."""
        if value != self._pool_size:
            self._adjust_pool_size(value)
        self._pool_size = value

    def _adjust_pool_size(self, pool_size):
        """Adjust the pool size.

        Creates a new Jinja Environment for each locale and up to the pool size.

        Also creates a corresponding thread lock that should be used when
        rendering using the environment to prevent the same environment from
        being used in multiple threads at the same time.
        """
        for locale in self._locales:
            locale_str = str(locale)
            if locale_str not in self._pool:
                self._pool[locale_str] = []
            existing_size = len(self._pool[locale_str])
            if pool_size > existing_size:
                for _ in range(pool_size - existing_size):
                    self._pool[locale_str].append({
                        'lock': threading.RLock(),
                        'env': self._create_jinja_env(locale=locale_str),
                    })
            elif pool_size < existing_size:
                self._pool[locale_str] = self._pool[locale_str][:pool_size]

    def _create_jinja_env(self, locale='', root=None):
        kwargs = {
            'autoescape': True,
            'extensions': [
                'jinja2.ext.autoescape',
                'jinja2.ext.do',
                'jinja2.ext.i18n',
                'jinja2.ext.loopcontrols',
                'jinja2.ext.with_',
            ],
            'loader': self.pod.storage.JinjaLoader(self.pod.root if root is None else root),
            'lstrip_blocks': True,
            'trim_blocks': True,
        }
        if self.pod.env.cached:
            kwargs['bytecode_cache'] = self.pod.jinja_bytecode_cache
        kwargs['bytecode_cache'] = self.pod.jinja_bytecode_cache
        kwargs['extensions'].extend(self.pod.list_jinja_extensions())
        env = jinja_dependency.DepEnvironment(**kwargs)
        env.filters.update(filters.create_builtin_filters())
        env.globals.update(**tags.create_builtin_globals(env, self.pod, locale=locale))
        return env

    def custom_jinja_env(self, locale='', root=None):
        """Create a custom jinja env that is not part of the pool."""
        return {
            'lock': threading.RLock(),
            'env': self._create_jinja_env(locale, root),
        }

    def get_jinja_env(self, locale=''):
        """Retrieves a jinja environment and lock to use to render.

        When rendering should use the lock to prevent threading issues.

            with jinja_env['lock']:
                template = jinja_env['env'].get_template('...')
                template.render({})
        """
        locale = str(locale)
        if locale not in self._pool:
            # Add the new locale to the pool.
            self._locales.append(locale)
            self._adjust_pool_size(self._pool_size)

        pool = self._pool[locale]
        # Randomly select which pool item to use. This should distribute
        # rendering fairly evenly across the pool. Since render times are fairly
        # even for most sites this should not be an issue.
        return pool[random.randrange(len(pool))]
