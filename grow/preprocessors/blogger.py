from . import base
from googleapiclient import discovery
from googleapiclient import errors
from grow.common import oauth
from grow.common import utils
from protorpc import messages
import datetime
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
        authenticated = messages.BooleanField(5, default=True)

    @staticmethod
    def create_service(authenticated=True):
        http = httplib2.Http(ca_certs=utils.get_cacerts_path())
        if authenticated:
            credentials = oauth.get_or_create_credentials(
                scope=OAUTH_SCOPE, storage_key='Grow SDK')
            http = credentials.authorize(http)
        key = None if authenticated else oauth.BROWSER_API_KEY
        return discovery.build('blogger', 'v3', http=http, developerKey=key)

    def get_edit_url(self, doc=None):
        """Returns the URL to edit in Blogger."""
        return BloggerPreprocessor._edit_url_format.format(
            blog_id=self.config.blog_id)

    def run(self, build=True):
        self.execute()

    def execute(self):
        items = BloggerPreprocessor.download_items(
            blog_id=self.config.blog_id,
            logger=self.pod.logger,
            authenticated=self.config.authenticated)
        self.bind_collection(items, self.config.collection)

    def _parse_item(self, item):
        item_id = item.pop('id')
        ext = 'md' if self.config.markdown else 'html'
        basename = '{}.{}'.format(item_id, ext)
        body = item.pop('content').encode('utf-8')
        fields = item
        # Formatted like: 2011-05-20T11:45:23-07:00
        published = fields['published'][:-6]
        published_dt = datetime.datetime.strptime(published, '%Y-%m-%dT%H:%M:%S')
        fields['$date'] = published_dt
        if 'title' in fields:
            fields['$title'] = fields.pop('title')
        if self.config.markdown:
            body = utils.clean_html(body, convert_to_markdown=True)
        return fields, body, basename

    @classmethod
    def download_items(cls, blog_id, logger=None, authenticated=True):
        logger = logger or logging
        service = cls.create_service(authenticated=authenticated)
        # pylint: disable=no-member
        resp = service.posts().list(blogId=blog_id).execute()
        if 'items' not in resp:
            logger.error('Received: {}'.format(resp))
            text = 'Unable to download Blogger blog: {}'
            raise base.PreprocessorError(text.format(blog_id))
        return resp['items']

    @classmethod
    def download_item(cls, blog_id, post_id, authenticated=True):
        service = cls.create_service(authenticated=authenticated)
        # pylint: disable=no-member
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
                blog_id=self.config.blog_id,
                post_id=post_id,
                authenticated=self.config.authenticated)
        except (errors.HttpError, base.PreprocessorError):
            text = 'Error downloading Blogger post -> {}'.format(path)
            raise base.PreprocessorError(text)
        if not item:
            return
        fields, body, _ = self._parse_item(item)
        if doc.exists:
            existing_data = doc.format.front_matter.data
        else:
            existing_data = {}
        fields = utils.format_existing_data(
            old_data=existing_data, new_data=fields,
            preserve=self.config.preserve)
        doc.inject(fields=fields, body=body)
        return self
