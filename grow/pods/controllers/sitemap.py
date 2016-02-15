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
        col_paths = [col.collection_path for col in self.collections]
        if self.locales:
            locale_ids = [str(locale) for locale in self.locales]
            return '<Sitemap(collections="{}", locales="{}")>'.format(
                ', '.join(col_paths), ', '.join(locale_ids))
        else:
            return '<Sitemap(collections="{}")>'.format(', '.join(col_paths))

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
            docs += col.list_servable_documents(locales=self.locales)
        return list(docs)

    def list_concrete_paths(self):
        return [self.path]
