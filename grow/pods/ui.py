from grow.common import utils
from grow.pods.storage import storage
import jinja2
import os

_root = os.path.join(utils.get_grow_dir(), 'ui', 'templates')
_loader = storage.FileStorage.JinjaLoader(_root)
env = jinja2.Environment(
    loader=_loader,
    autoescape=True,
    trim_blocks=True,
    extensions=[
        'jinja2.ext.autoescape',
        'jinja2.ext.do',
        'jinja2.ext.i18n',
        'jinja2.ext.loopcontrols',
        'jinja2.ext.with_',
    ])

overlay = env.get_template('ui.html')
