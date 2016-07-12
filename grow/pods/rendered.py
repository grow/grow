from . import controllers
from . import messages
from . import tags
from babel import support
from grow.pods import ui
from grow.common import utils
from grow.pods import errors
import logging
import mimetypes
import sys


class RenderedController(controllers.BaseController):
    KIND = messages.Kind.RENDERED

    def __init__(self, view=None, document=None, path=None, _pod=None):
        self.view = view
        self.document = document
        self.path = path
        super(RenderedController, self).__init__(_pod=_pod)

    def __repr__(self):
        if not self.document:
            return '<Rendered(view=\'{}\')>'.format(self.view)
        return '<Rendered(view=\'{}\', doc=\'{}\')>'.format(
            self.view, self.document.pod_path)

    def get_mimetype(self, params=None):
        return mimetypes.guess_type(self.view)[0]

    @property
    def locale(self):
        if self.document:
            return self.document.locale

    def list_concrete_paths(self):
        if self.path:
            return [self.path]
        if not self.document:
            raise
        return [self.document.get_serving_path()]

    def render(self, params, inject=True):
        preprocessor = None
        if inject:
            preprocessor = self.pod.inject_preprocessors(doc=self.document)
        env = self.pod.get_jinja_env(self.locale)
        template = env.get_template(self.view.lstrip('/'))
        try:
            kwargs = {
                'doc': self.document,
                'env': self.pod.env,
                'podspec': self.pod.get_podspec(),
            }
            content = template.render(kwargs).lstrip()
            if preprocessor and self.get_mimetype().endswith('html'):
                content += '\n' + ui.overlay.render({
                    'doc': self.document,
                    'preprocessor': preprocessor,
                })
            return content
        except Exception as e:
            text = 'Error building {}: {}'
            exception = errors.BuildError(text.format(self, e))
            exception.traceback = sys.exc_info()[2]
            exception.controller = self
            exception.exception = e
            raise exception
