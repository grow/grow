from grow.common import utils
from grow.pods.storage import storage
import jinja2
import os


@utils.memoize
def create_jinja_env():
    root = os.path.join(utils.get_grow_dir(), 'ui', 'templates')
    loader = storage.FileStorage.JinjaLoader(root)
    return jinja2.Environment(
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
