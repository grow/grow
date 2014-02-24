import logging
import mimetypes
import jinja2
from grow.common import utils
from grow.pods import errors
from grow.pods.controllers import base
from grow.pods.controllers import tags
from grow.pods.storage import gettext_storage as gettext


class PageController(base.BaseController):

  KIND = 'Page'

  class Defaults(object):
    LL = 'en'
    LOCALE = None
    CC = None

  def __init__(self, view=None, document=None, path=None, _pod=None):
    self.view = view
    self.document = document
    self.path = path
    super(PageController, self).__init__(_pod=_pod)

  def __repr__(self):
    if not self.document:
      return '<Page(view=\'{}\')>'.format(self.view)
    return '<Page(view=\'{}\', document=\'{}\')>'.format(self.view, self.document.pod_path)

  @property
  def mimetype(self):
    return mimetypes.guess_type(self.view)[0]

  @property
  def locale(self):
    return self.document.locale

  @property
  def ll(self):
    return self.route_params.get('ll', PageController.Defaults.LL)

  @property
  def cc(self):
    return self.route_params.get('cc', PageController.Defaults.CC)

  @property
  @utils.memoize
  def _template_env(self):
    _template_loader = self.pod.storage.JinjaLoader(self.pod.root)
    env = jinja2.Environment(
        loader=_template_loader, autoescape=True, trim_blocks=True,
        extensions=['jinja2.ext.i18n'])
    env.filters['markdown'] = tags.markdown_filter
    return env

  def _install_translations(self, ll):
    if ll is None:
      gettext_translations = gettext.NullTranslations()
    else:
      translation = self.pod.translations.get_translation(ll)
      gettext_translations = translation.get_gettext_translations()
    self._template_env.install_gettext_translations(gettext_translations)

  def list_concrete_paths(self):
    if self.path:
      return [self.path]
    if not self.document:
      raise
    return [self.document.get_serving_path()]

  def render(self):
    # TODO(jeremydw): This is a bit hacky. Be more explicit about translations.
    ll = self.locale
    self._install_translations(ll)
    template = self._template_env.get_template(self.view.lstrip('/'))
    context = {}
    context = {
        'categories': lambda *args, **kwargs: tags.categories(*args, _pod=self.pod, **kwargs),
        'docs': lambda *args, **kwargs: tags.docs(*args, _pod=self.pod, **kwargs),
        'get_doc': lambda *args, **kwargs: tags.get_doc(*args, _pod=self.pod, **kwargs),
        'static': lambda path: tags.static(path, _pod=self.pod),
        'breadcrumb': lambda *args, **kwargs: tags.breadcrumb(*args, _pod=self.pod, **kwargs),
        'nav': lambda *args, **kwargs: tags.nav(*args, _pod=self.pod, **kwargs),
        'cc': self.cc,
        'doc': self.document,
        'll': self.ll,
        'params': self.route_params,
        'pod': self.pod,
    }
    try:
      return template.render({
          'g': context,
          'doc': self.document,
      })
    except Exception as e:
      text = 'Error building {}: {}'
      logging.exception(e)
      raise errors.BuildError(text.format(self, e))
