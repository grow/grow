from . import controllers
from . import messages
from . import tags
from babel import support
from grow.common import utils
from grow.pods import errors
import logging
import mimetypes
import sys
import webapp2


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

    def get_mimetype(self, params):
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

    def __wrap(self, func):
        use_cache = self.pod.env.cached
        return lambda *args, **kwargs: func(
            *args, _pod=self.pod, use_cache=use_cache, **kwargs)

    def render(self, params):
        env = self.pod.get_jinja_env(self.locale)
        template = env.get_template(self.view.lstrip('/'))
        g_tags = {
            'breadcrumb': self.__wrap(tags.breadcrumb),
            'collection': self.__wrap(tags.collection),
            'collections': self.__wrap(tags.collections),
            'categories': self.__wrap(tags.categories),
            'csv': self.__wrap(tags.csv),
            'date': self.__wrap(tags.date),
            'doc': self.__wrap(tags.get_doc),
            'docs': self.__wrap(tags.docs),
            'json': self.__wrap(tags.json),
            'locales': self.__wrap(tags.locales),
            'nav': self.__wrap(tags.nav),
            'static': self.__wrap(tags.static),
            'statics': self.__wrap(tags.statics),
            'url': self.__wrap(tags.url),
            'yaml': self.__wrap(tags.yaml),
        }
        try:
            kwargs = {
                'g': g_tags,
                'doc': self.document,
                'env': self.pod.env,
                'podspec': self.pod.get_podspec(),
            }
            return template.render(kwargs).lstrip()
        except Exception as e:
            text = 'Error building {}: {}'
            exception = errors.BuildError(text.format(self, e))
            exception.traceback = sys.exc_info()[2]
            exception.controller = self
            exception.exception = e
            raise exception
