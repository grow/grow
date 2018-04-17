"""Render controller for rendering documents."""

import mimetypes
import sys
from grow.templates import tags
from grow.templates import doc_dependency
from . import controllers
from . import env
from . import errors
from . import messages
from . import ui


class RenderedController(controllers.BaseController):
    KIND = messages.Kind.RENDERED

    def __init__(self, view=None, doc=None, path=None, _pod=None):
        self.view = view
        self.path = path
        self._pod = _pod
        if doc:
            self._pod_path = doc.pod_path
            self._locale = str(doc.locale)
        else:
            self._pod_path = None
            self._locale = None
        super(RenderedController, self).__init__(_pod=_pod)

    def __repr__(self):
        doc = self.doc
        if not doc:
            return '<Rendered(view=\'{}\')>'.format(self.view)
        if doc.locale:
            return '<Rendered(view=\'{}\', doc=\'{}\', locale=\'{}\')>'.format(
                self.view, doc.pod_path, str(doc.locale))
        return '<Rendered(view=\'{}\', doc=\'{}\')>'.format(
            self.view, doc.pod_path)

    def get_mimetype(self, params=None):
        path_mimetype = None
        if self.doc:
            path_mimetype = mimetypes.guess_type(self.doc.get_serving_path())[0]
        return path_mimetype or mimetypes.guess_type(self.view)[0]

    @property
    def doc(self):
        # Rely on the pod caching to get the doc so that the routing map
        # does not need to be rebuilt every time a document changes.
        if self._pod_path is None:
            return None

        return self.pod.get_doc(self._pod_path, self._locale)

    @property
    def locale(self):
        doc = self.doc
        return doc.locale if doc else None

    def list_concrete_paths(self):
        if self.path:
            return [self.path]
        if not self.doc:
            return []
        return [self.doc.get_serving_path()]

    # pylint: disable=unused-argument
    def render(self, params, inject=True):
        doc = self.doc
        preprocessor = None
        translator = None
        if inject:
            preprocessor = self.pod.inject_preprocessors(doc=doc)
            translator = self.pod.inject_translators(doc=doc)
        jinja_env = self.pod.get_jinja_env(self.locale)
        template = jinja_env.get_template(self.view.lstrip('/'))
        track_dependency = doc_dependency.DocDependency(doc)
        local_tags = tags.create_builtin_tags(
            self.pod, doc, track_dependency=track_dependency)
        # NOTE: This should be done using get_template(... globals=...)
        # or passed as an argument into render but
        # it is not available included inside macros???
        # See: https://github.com/pallets/jinja/issues/688
        template.globals['g'] = local_tags

        # Track the message stats, including untranslated strings.
        if self.pod.is_enabled(self.pod.FEATURE_TRANSLATION_STATS):
            template.globals['_'] = tags.make_doc_gettext(doc)

        try:
            kwargs = {
                'doc': doc,
                'env': self.pod.env,
                'podspec': self.pod.podspec,
                '_track_dependency': track_dependency,
            }
            content = template.render(kwargs).lstrip()
            if self.pod.is_enabled(self.pod.FEATURE_UI):
                content = self._inject_ui(
                    content, preprocessor, translator)
            return content
        except Exception as e:
            text = 'Error building {}: {}'
            exception = errors.BuildError(text.format(self, e))
            exception.traceback = sys.exc_info()[2]
            exception.controller = self
            exception.exception = e
            if self._pod:
                self._pod.logger.exception(text.format(self, e))
            raise exception

    def _inject_ui(self, content, preprocessor, translator):
        if not self.get_mimetype().endswith('html'):
            return content

        ui_settings = self.pod.ui
        show_ui = (self.pod.env.name == env.Name.DEV
                   and (preprocessor or translator))
        if ui_settings or show_ui:
            jinja_env = ui.create_jinja_env()
            ui_template = jinja_env.get_template('views/ui.html')
            content += '\n' + ui_template.render({
                'doc': self.doc,
                'preprocessor': preprocessor,
                'translator': translator,
                'ui': ui_settings,
            })

        return content
