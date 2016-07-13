from . import controllers
from . import messages
from grow.common import utils
from grow.pods import env
from grow.pods import errors
from grow.pods import ui
import mimetypes
import sys


class RenderedController(controllers.BaseController):
    KIND = messages.Kind.RENDERED

    def __init__(self, view=None, doc=None, path=None, _pod=None):
        self.view = view
        self.doc = doc
        self.path = path
        super(RenderedController, self).__init__(_pod=_pod)

    def __repr__(self):
        if not self.doc:
            return '<Rendered(view=\'{}\')>'.format(self.view)
        return '<Rendered(view=\'{}\', doc=\'{}\')>'.format(
            self.view, self.doc.pod_path)

    def get_mimetype(self, params=None):
        return mimetypes.guess_type(self.view)[0]

    @property
    def locale(self):
        return self.doc.locale if self.doc else None

    def list_concrete_paths(self):
        if self.path:
            return [self.path]
        if not self.doc:
            raise
        return [self.doc.get_serving_path()]

    def render(self, params, inject=True):
        preprocessor = None
        if inject:
            preprocessor = self.pod.inject_preprocessors(doc=self.doc)
        env = self.pod.get_jinja_env(self.locale)
        template = env.get_template(self.view.lstrip('/'))
        try:
            kwargs = {
                'doc': self.doc,
                'env': self.pod.env,
                'podspec': self.pod.get_podspec(),
            }
            content = template.render(kwargs).lstrip()
            content = self._inject_ui(content, preprocessor)
            return content
        except Exception as e:
            text = 'Error building {}: {}'
            exception = errors.BuildError(text.format(self, e))
            exception.traceback = sys.exc_info()[2]
            exception.controller = self
            exception.exception = e
            raise exception

    def _inject_ui(self, content, preprocessor):
        show_ui = (self.pod.env.name == env.Name.DEV and preprocessor
                   and self.get_mimetype().endswith('html'))
        if show_ui:
            jinja_env = ui.create_jinja_env()
            ui_template = jinja_env.get_template('ui.html')
            content += '\n' + ui_template.render({
                'doc': self.doc,
                'preprocessor': preprocessor,
            })
        return content
