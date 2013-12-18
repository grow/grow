import logging
import mimetypes
import jinja2
from grow.common import utils
from grow.pods import errors
from grow.pods.controllers import base
from grow.pods.controllers import tags
from grow.pods.controllers.tags import markdown_filter


class PageController(base.BaseController):

  KIND = 'Page'

  class Defaults(object):
    LL = 'en'
    CC = None

  def __init__(self, view=None, document=None, path=None, pod=None):
    self.view = view
    self.document = document
    self.path = path
    self.pod = pod
    self.route_params = {}

  def __repr__(self):
    if not self.document:
      return '<Page(view=\'{}\')>'.format(self.view)
    return '<Page(view=\'{}\', document=\'{}\')>'.format(self.view, self.document.pod_path)

  @property
  def mimetype(self):
    return mimetypes.guess_type(self.view)[0]

  @property
  def ll(self):
    # TODO: Validate languages.
    return self.route_params.get('ll', PageController.Defaults.LL)

  @property
  def cc(self):
    # TODO: Validate regions.
    return self.route_params.get('cc', PageController.Defaults.CC)

  @property
  @utils.memoize
  def _template_env(self):
    _template_loader = self.pod.storage.JinjaLoader(self.pod.root)
    env = jinja2.Environment(
        loader=_template_loader, autoescape=True, trim_blocks=True,
        extensions=['jinja2.ext.i18n'])
    env.filters['markdown'] = markdown_filter.markdown_filter
    return env

  def _install_translations(self, ll):
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
    self._install_translations(self.ll)
    template = self._template_env.get_template(self.view.lstrip('/'))
    context = {
        'cc': self.cc,
        'content': self.document,  # TODO: Remove.
        'doc': self.document,
        'docs': lambda *args, **kwargs: tags.docs(*args, _pod=self.pod, **kwargs),
        'categories': lambda *args, **kwargs: tags.categories(*args, _pod=self.pod, **kwargs),
        'is_active': lambda doc: tags.is_active(doc, self.document),
        'static': lambda path: tags.static(path, _pod=self.pod),
        'll': self.ll,
        'params': self.route_params,
        'pod': self.pod,
    }
    try:
      return template.render({'g': context})
    except Exception as e:
      text = 'Error building {}: {}'
      logging.exception(e)
      raise errors.BuildError(text.format(self, e))
