import webapp2
from . import base
from grow.common import utils
from contentful.cda import client
from contentful.cda import resources
from protorpc import messages


class KeyMessage(messages.Message):
    preview = messages.StringField(1)
    production = messages.StringField(2)


class BindingMessage(messages.Message):
    collection = messages.StringField(1)
    type = messages.StringField(2)


class ContentfulPreprocessor(base.BasePreprocessor):
    KIND = 'contentful'

    class Config(messages.Message):
        space = messages.StringField(2)
        keys = messages.MessageField(KeyMessage, 3)
        bind = messages.MessageField(BindingMessage, 4, repeated=True)

    def parse_entry(self, entry):
        body = entry.fields.pop('body', None)
        fields = entry.fields
        for key, value in entry.fields.iteritems():
            if isinstance(value, resources.Asset):
                entry.fields[key] = value.url
            elif isinstance(value, resources.Entry):
                entry.fields[key] = value.sys['id']
        if body:
            body = body.encode('utf-8')
            ext = 'md'
        else:
            body = ''
            ext = 'yaml'
        if 'title' in entry.fields:
            title = entry.fields.pop('title')
            entry.fields['$title'] = title
        basename = '{}.{}'.format(entry.sys['id'], ext)
        return fields, body, basename

    def bind_collection(self, entries, collection_pod_path, contentful_type):
        collection = self.pod.get_collection(collection_pod_path)
        existing_pod_paths = [
            doc.pod_path for doc in collection.list_docs()]
        new_pod_paths = []
        for i, entry in enumerate(entries):
            if entry.sys['contentType']['sys']['id'] != contentful_type:
                continue
            fields, body, basename = self.parse_entry(entry)
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
            self.bind_collection(entries, binding.collection, binding.type)

    @webapp2.cached_property
    def cda(self):
        token = self.config.keys.preview
        token = self.config.keys.production
        return client.Client(self.config.space, token)

    def inject(self, doc):
        query = {'sys.id': doc.base}
        entry = self.cda.fetch(resources.Entry).where(query).first()
        if not entry:
            return
        fields, body, basename = self.parse_entry(entry)
        doc.fields.update(fields)
        doc.format.body = body
        doc.pod.logger.info('Injected -> {}'.format(doc.pod_path))
        return
