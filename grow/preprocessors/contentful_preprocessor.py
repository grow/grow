from . import base
from contentful.cda import client
from contentful.cda import resources
from grow.common import utils
from grow.common import utils
from protorpc import messages
import os


class KeyMessage(messages.Message):
    preview = messages.StringField(1)
    production = messages.StringField(2)


class BindingMessage(messages.Message):
    collection = messages.StringField(1)
    contentModel = messages.StringField(2)


class ContentfulPreprocessor(base.BasePreprocessor):
    KIND = 'contentful'
    _edit_entry_url_format = 'https://app.contentful.com/spaces/{space}/entries/{entry}'
    _edit_space_url_format = 'https://app.contentful.com/spaces/{space}/entries'
    _preview_endpoint = 'preview.contentful.com'

    class Config(messages.Message):
        space = messages.StringField(2)
        keys = messages.MessageField(KeyMessage, 3)
        bind = messages.MessageField(BindingMessage, 4, repeated=True)

    def _parse_field(self, field):
        if isinstance(field, resources.Asset):
            return field.url
        elif isinstance(field, resources.Entry):
            return field.sys['id']
        elif isinstance(field, resources.ResourceLink):
            return self.cda.resolve_resource_link(field)
        elif isinstance(field, list):
            return [self._parse_field(sub_field) for sub_field in field]
        return field

    def _parse_entry(self, entry):
        """Parses an entry from Contentful."""
        body = entry.fields.pop('body', None)
        fields = entry.fields
        for key, field in entry.fields.iteritems():
          entry.fields[key] = self._parse_field(field)
        if body:
            body = body
            ext = 'md'
        else:
            body = ''
            ext = 'yaml'
        if 'title' in entry.fields:
            entry.fields['$title'] = entry.fields.pop('title')
        if 'slug' in entry.fields:
            entry.fields['$slug'] = entry.fields.pop('slug')
        if 'category' in entry.fields:
            category = entry.fields.pop('category')
            entry.fields['$category'] = category
        basename = '{}.{}'.format(entry.sys['id'], ext)
        if isinstance(body, unicode):
            body = body.encode('utf-8')
        return fields, body, basename

    def bind_collection(self, entries, collection_pod_path, contentful_model):
        """Binds a Grow collection to a Contentful collection."""
        collection = self.pod.get_collection(collection_pod_path)
        existing_pod_paths = [
            doc.pod_path for doc in collection.list_docs(recursive=False, inject=False)]
        new_pod_paths = []
        for i, entry in enumerate(entries):
            if entry.sys['contentType']['sys']['id'] != contentful_model:
                continue
            fields, body, basename = self._parse_entry(entry)
            doc = collection.create_doc(basename, fields=fields, body=body)
            new_pod_paths.append(doc.pod_path)
            self.pod.logger.info('Saved -> {}'.format(doc.pod_path))
        pod_paths_to_delete = set(existing_pod_paths) - set(new_pod_paths)
        for pod_path in pod_paths_to_delete:
            self.pod.delete_file(pod_path)
            self.pod.logger.info('Deleted -> {}'.format(pod_path))

    def run(self, *args, **kwargs):
        entries = self.cda.fetch(resources.Entry).all()
        for binding in self.config.bind:
            self.bind_collection(entries, binding.collection,
                                 binding.contentModel)

    @property
    @utils.memoize
    def cda(self):
        """Contentful API client."""
        endpoint = None
        token = self.config.keys.production
        # Use preview endpoint if preview key is provided.
        if self.config.keys.preview:
            token = self.config.keys.preview
            endpoint = ContentfulPreprocessor._preview_endpoint
        return client.Client(self.config.space, token, endpoint=endpoint)

    def can_inject(self, doc=None, collection=None):
        if not self.injected:
            return False
        for binding in self.config.bind:
            if doc and doc.pod_path.startswith(binding.collection):
                return True
            if (collection and
                    self._normalize_path(collection.pod_path)
                    == self._normalize_path(binding.collection)):
                return True
        return False

    def inject(self, doc=None, collection=None):
        """Conditionally injects data into documents or a collection, without
        updating the filesystem. If doc is provided, the document's fields are
        injected. If collection is provided, returns a list of injected
        document instances."""
        if doc is not None:
            query = {'sys.id': doc.base}
            entry = self.cda.fetch(resources.Entry).where(query).first()
            if not entry:
                self.pod.logger.info('Contentful entry not found: {}'.format(query))
                return  # Corresponding doc not found in Contentful.
            fields, body, basename = self._parse_entry(entry)
            if isinstance(body, unicode):
                body = body.encode('utf-8')
            doc.inject(fields=fields, body=body)
            return doc
        elif collection is not None:
            entries = self.cda.fetch(resources.Entry).all()
            docs = []
            for binding in self.config.bind:
                if (self._normalize_path(collection.pod_path)
                        != self._normalize_path(binding.collection)):
                    continue
                docs += self.create_doc_instances(
                    entries, collection, binding.contentModel)
            return docs

    def create_doc_instances(self, entries, collection, contentful_model):
        docs = []
        for i, entry in enumerate(entries):
            if entry.sys['contentType']['sys']['id'] != contentful_model:
                continue
            fields, body, basename = self._parse_entry(entry)
            pod_path = os.path.join(collection.pod_path, basename)
            doc = collection.get_doc(pod_path)
            doc.inject(fields=fields, body=body)
            docs.append(doc)
        return docs

    def _normalize_path(self, path):
        """Normalizes a collection path."""
        return path.rstrip('/')

    def get_edit_url(self, doc=None):
        """Returns the URL to edit in Contentful."""
        if doc:
            return ContentfulPreprocessor._edit_entry_url_format.format(
                space=self.config.space, entry=doc.base)
        return ContentfulPreprocessor._edit_space_url_format.format(
            space=self.config.space)
