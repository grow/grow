from . import base
from . import messages
from grow.common import utils
import mimetypes
import os


class SitemapController(base.BaseController):
  KIND = messages.Kind.SITEMAP

  def __init__(self, pod, path=None, collections=None, locales=None):
    self.pod = pod
    if path:
      self.path = path
    else:
      self.path = (self.pod.podspec.root + '/sitemap.xml').replace('//', '/')
    self.path = '/' + self.path.lstrip('/')
    self.collections = pod.list_collections(collections)
    self.locales = locales
    super(SitemapController, self).__init__(_pod=pod)

  def __repr__(self):
    return '<Sitemap: {}>'.format(self.path)

  @property
  def mimetype(self):
    return mimetypes.guess_type(self.path)[0]

  def render(self):
    root = os.path.join(utils.get_grow_dir(), 'pods', 'templates')
    env = self.pod.create_template_env(root=root)
    template = env.get_template('sitemap.xml')
    return template.render({
        'docs': self._list_docs(),
    }).strip()

  def _list_docs(self):
    docs = []
    for col in self.collections:
      docs += col.list_servable_documents()
    return list(docs)
