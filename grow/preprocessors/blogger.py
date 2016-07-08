from . import base
from googleapiclient import discovery
from googleapiclient import errors
from grow.common import oauth
from grow.common import utils
from protorpc import messages
import httplib2
import logging


OAUTH_SCOPE = 'https://www.googleapis.com/auth/blogger'


# Silence extra logging from googleapiclient.
discovery.logger.setLevel(logging.WARNING)


class BloggerPreprocessor(base.BasePreprocessor):
    _edit_url_format = 'https://www.blogger.com/blogger.g?blogID={blog_id}#allposts'
    KIND = 'blogger'

    class Config(messages.Message):
        blog_id = messages.IntegerField(1)
        collection = messages.StringField(2)
        preserve = messages.StringField(3, default='builtins')
        markdown = messages.BooleanField(4, default=False)

    @staticmethod
    def create_service():
        credentials = oauth.get_or_create_credentials(
            scope=OAUTH_SCOPE, storage_key='Grow SDK')
        http = httplib2.Http(ca_certs=utils.get_cacerts_path())
        http = credentials.authorize(http)
        return discovery.build('blogger', 'v3', http=http)

    def get_edit_url(self, doc=None):
        """Returns the URL to edit in Blogger."""
        return BloggerPreprocessor._edit_url_format.format(blog_id=self.config.blog_id)

    def run(self, build=True):
        try:
            self.execute()
        except errors.HttpError as e:
            self.logger.error(str(e))

    def execute(self):
        items = self.download_items(blog_id=self.config.blog_id, logger=self.pod.logger)
        self.bind_collection(items, self.config.collection)

    def _parse_item(self, item):
        item_id = item.pop('id')
        ext = 'md' if self.config.markdown else 'html'
        basename = '{}.{}'.format(item_id, ext)
        body = item.pop('content').encode('utf-8')
        fields = item
        if self.config.markdown:
            body = utils.clean_html(body, convert_to_markdown=True)
        return fields, body, basename

    @classmethod
    def download_items(cls, blog_id, logger=None):
        logger = logger or logging
        service = cls.create_service()
        resp = service.posts().list(blogId=blog_id).execute()
        if 'items' not in resp:
            text = 'Unable to download Blogger blog: {}'
            logger.error(text.format(blog_id))
            logger.error('Received: {}'.format(resp))
            return
        return resp['items']

    @classmethod
    def download_item(cls, blog_id, post_id):
        service = cls.create_service()
        resp = service.posts().get(blogId=blog_id, postId=post_id).execute()
        return resp

    def bind_collection(self, items, collection_pod_path):
        collection = self.pod.get_collection(collection_pod_path)
        existing_pod_paths = [
            doc.pod_path for doc in collection.list_docs(recursive=False, inject=False)]
        new_pod_paths = []
        for item in items:
            fields, body, basename = self._parse_item(item)
            doc = collection.create_doc(basename, fields=fields, body=body)
            new_pod_paths.append(doc.pod_path)
            self.pod.logger.info('Saved -> {}'.format(doc.pod_path))
        pod_paths_to_delete = set(existing_pod_paths) - set(new_pod_paths)
        for pod_path in pod_paths_to_delete:
            self.pod.delete_file(pod_path)
            self.pod.logger.info('Deleted -> {}'.format(pod_path))

    def _normalize_path(self, path):
        """Normalizes a collection path."""
        return path.rstrip('/')

    def can_inject(self, doc=None, collection=None):
        if not self.injected:
            return False
        if doc and doc.pod_path.startswith(self.config.collection):
            return True
        if (collection and
                self._normalize_path(collection.pod_path)
                == self._normalize_path(self.config.collection)):
            return True
        return False

    def inject(self, doc):
        path = doc.pod_path
        post_id = doc.base
        try:
            item = BloggerPreprocessor.download_item(
                blog_id=self.config.id, post_id=post_id)
        except (errors.HttpError, base.PreprocessorError):
            doc.pod.logger.error('Error downloading Blogger post -> %s', path)
            raise
        if not item:
            return
        fields, body, _ = self._parse_item(item)
        existing_data = doc.pod.read_yaml(doc.pod_path)
        fields = utils.format_existing_data(
            old_data=existing_data, new_data=fields,
            preserve=self.config.preserve)
        doc.inject(fields=fields, body=body)
