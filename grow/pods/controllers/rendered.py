from . import base
from . import messages
from . import tags
from grow.pods import errors
from grow.pods.storage import gettext_storage as gettext
import logging
import mimetypes
import webapp2


class RenderedController(base.BaseController):
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

  @property
  def mimetype(self):
    return mimetypes.guess_type(self.view)[0]

  @property
  def locale(self):
    if self.document:
      return self.document.locale

  @webapp2.cached_property
  def _template_env(self):
    # NOTE: The same template environment can be reused within a controller
    # since a single controller's locale never changes.
    return self.pod.create_template_env(self.locale)

  def _install_translations(self, locale):
    active_locale = self._template_env.active_locale
    if locale == active_locale and active_locale != '__unset':
      return
    if locale is None:
      gettext_translations = gettext.NullTranslations()
    else:
      catalog = self.pod.catalogs.get(locale)
      gettext_translations = catalog.gettext_translations
    self._template_env.uninstall_gettext_translations(None)
    self._template_env.install_gettext_translations(gettext_translations,
                                                    newstyle=True)
    self._template_env.active_locale = locale

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

  def render(self):
    self._install_translations(self.locale)
    template = self._template_env.get_template(self.view.lstrip('/'))
    g_tags = {
        'breadcrumb': self.__wrap(tags.breadcrumb),
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
      logging.exception(e)
      exception = errors.BuildError(text.format(self, e))
      exception.controller = self
      exception.exception = e
      raise exception
