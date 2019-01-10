"""Grow UI Tools"""

import os
import jinja2
from grow.common import utils
from grow import storage
from grow.templates import filters


@utils.memoize
def create_jinja_env():
    root = os.path.join(utils.get_grow_dir(), 'ui', 'admin')
    loader = storage.FileStorage.JinjaLoader(root)
    env = jinja2.Environment(
        loader=loader,
        autoescape=True,
        trim_blocks=True,
        extensions=[
            'jinja2.ext.autoescape',
            'jinja2.ext.do',
            'jinja2.ext.i18n',
            'jinja2.ext.loopcontrols',
            'jinja2.ext.with_',
        ])
    env.filters.update(filters.create_builtin_filters())
    return env
