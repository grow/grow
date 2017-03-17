from . import controllers
from . import messages
from grow.common import utils
import mimetypes
import os


class SitemapController(controllers.BaseController):
    KIND = messages.Kind.SITEMAP

    def __init__(self, pod, path=None, collections=None, locales=None, template=None):
        self.pod = pod
        if path:
            self.path = path
        else:
            self.path = (self.pod.podspec.root + '/sitemap.xml').replace('//', '/')
        self.path = '/' + self.path.lstrip('/')
        self.locales = locales
        self.template = template
        self._collection_paths = collections
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

    @utils.cached_property
    def collections(self):
        return list(self.pod.list_collections(self._collection_paths))

    def get_mimetype(self, params=None):
        return self.mimetype

    def render(self, params=None, inject=False):
        root = os.path.join(utils.get_grow_dir(), 'pods', 'templates')
        env = self.pod.get_jinja_env(root=root)
        if self.template:
            content = self.pod.read_file(self.template)
            template = env.from_string(content)
        else:
            template = env.get_template('sitemap.xml')
        docs = self._list_docs()
        return template.render({
            'pod': self.pod,
            'docs': docs,
        }).strip()

    def _list_docs(self):
        docs = []
        for col in self.collections:
            docs += col.list_servable_documents(locales=self.locales)
        return list(docs)

    def list_concrete_paths(self):
        return [self.path]
