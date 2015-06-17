from . import base
from . import messages
from . import tags
from grow.pods import errors
from grow.pods.storage import gettext_storage as gettext
import logging
import mimetypes


class RenderedController(base.BaseController):
  KIND = messages.Kind.RENDERED

  class Defaults(object):
    LL = 'en'
    LOCALE = None
    CC = None

  def __init__(self, view=None, document=None, path=None, _pod=None):
    self.view = view
    self.document = document
    self.path = path
    super(RenderedController, self).__init__(_pod=_pod)

  def __repr__(self):
    if not self.document:
      return '<Rendered(view=\'{}\')>'.format(self.view)
    return '<Rendered(view=\'{}\', document=\'{}\')>'.format(
        self.view, self.document.pod_path)

  @property
  def mimetype(self):
    return mimetypes.guess_type(self.view)[0]

  @property
  def locale(self):
    if self.document:
      return self.document.locale

  @property
  def ll(self):
    return self.route_params.get('ll', RenderedController.Defaults.LL)

  @property
  def cc(self):
    return self.route_params.get('cc', RenderedController.Defaults.CC)

  @property
  def _template_env(self):
    return self.pod.template_env

  def _install_translations(self, ll):
    if ll is None:
      gettext_translations = gettext.NullTranslations()
    else:
      catalog = self.pod.catalogs.get(ll)
      gettext_translations = catalog.gettext_translations
    self._template_env.uninstall_gettext_translations(None)
    self._template_env.install_gettext_translations(gettext_translations, newstyle=True)

  def list_concrete_paths(self):
    if self.path:
      return [self.path]
    if not self.document:
      raise
    return [self.document.get_serving_path()]

  def render(self):
    self._install_translations(self.locale)
    template = self._template_env.get_template(self.view.lstrip('/'))
    g = {
        'breadcrumb': lambda *args, **kwargs: tags.breadcrumb(*args, _pod=self.pod, **kwargs),
        'categories': lambda *args, **kwargs: tags.categories(*args, _pod=self.pod, **kwargs),
        'cc': self.cc,
        'csv': lambda *args, **kwargs: tags.csv(*args, _pod=self.pod, **kwargs),
        'date': lambda *args, **kwargs: tags.date(*args, _pod=self.pod, **kwargs),
        'doc': lambda *args, **kwargs: tags.get_doc(*args, _pod=self.pod, **kwargs),
        'docs': lambda *args, **kwargs: tags.docs(*args, _pod=self.pod, **kwargs),
        'locales': lambda *args, **kwargs: tags.locales(*args, _pod=self.pod, **kwargs),
        'nav': lambda *args, **kwargs: tags.nav(*args, _pod=self.pod, **kwargs),
        'params': self.route_params,
        'static': lambda path: tags.static(path, _pod=self.pod),
        'url': lambda *args, **kwargs: tags.url(*args, _pod=self.pod, **kwargs),
        'yaml': lambda path: tags.yaml(path, _doc=self.document, _pod=self.pod),
    }
    try:
      return template.render({
          'g': g,
          'doc': self.document,
          'env': self.pod.env,
          'podspec': self.pod.get_podspec(),
      }).lstrip()
    except Exception as e:
      text = 'Error building {}: {}'
      logging.exception(e)
      raise errors.BuildError(text.format(self, e))
