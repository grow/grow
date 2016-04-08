"""Collections contain content documents and blueprints."""

from . import documents
from . import messages
from grow.common import structures
from grow.common import utils
from grow.pods import locales
import json
import logging
import operator
import os
import re


class Error(Exception):
    pass


class CollectionNotEmptyError(Error):
    pass


class BadCollectionNameError(Error, ValueError):
    pass


class CollectionDoesNotExistError(Error, ValueError):
    pass


class CollectionExistsError(Error):
    pass


class BadFieldsError(Error, ValueError):
    pass


class NoLocalesError(Error):
    pass


class Collection(object):

    def __init__(self, pod_path, _pod):
        utils.validate_name(pod_path)
        self.pod = _pod
        self.collection_path = re.sub('^/content/?', '', pod_path).strip('/')
        self.pod_path = pod_path
        self._default_locale = _pod.podspec.default_locale
        self._blueprint_path = os.path.join(self.pod_path, '_blueprint.yaml')

    def __repr__(self):
        return '<Collection "{}">'.format(self.collection_path)

    def __eq__(self, other):
        return (isinstance(other, Collection)
                and self.collection_path == other.collection_path)

    def __iter__(self):
        for doc in self.list_docs():
            yield doc

    @classmethod
    def list(cls, pod):
        # TODO: Implement "depth" argument on pod.list_dir and use.
        paths = pod.list_dir('/content/')
        clean_paths = set()
        for path in paths:
            parts = path.split('/')
            if len(parts) >= 2:  # Disallow files in root-level /content/ dir.
                clean_paths.add(os.path.join('/content', parts[0]))
        return [cls(pod_path, _pod=pod) for pod_path in clean_paths]

    @property
    def exists(self):
        return self.pod.file_exists(self._blueprint_path)

    def create_from_message(self, message):
        if self.exists:
            raise CollectionExistsError('{} already exists.'.format(self))
        self.update_from_message(message)
        return self

    @classmethod
    def get(cls, collection_path, _pod):
        return cls(collection_path, _pod)

    def get_doc(self, pod_path, locale=None):
        return documents.Document(pod_path, locale=locale, _pod=self.pod,
                                  _collection=self)

    @property
    @utils.memoize
    def yaml(self):
        if not self.exists:
            return {}
        result = utils.parse_yaml(self.pod.read_file(self._blueprint_path))
        if result is None:
            return {}
        return result

    def list_categories(self):
        return self.yaml.get('categories')

    @property
    def title(self):
        return self.yaml.get('title')

    @property
    def root(self):
        return self.yaml.get('root')

    def delete(self):
        if len(self.list_docs(include_hidden=True)):
            text = 'Collections that are not empty cannot be deleted.'
            raise CollectionNotEmptyError(text)
        self.pod.delete_file(self._blueprint_path)

    def update_from_message(self, message):
        if not message.fields:
            raise BadFieldsError('Fields are required to create a collection.')
        fields = json.loads(message.fields)
        fields = utils.dump_yaml(fields)
        self.pod.write_file(self._blueprint_path, fields)

    def get_view(self):
        return self.yaml.get('view')

    def get_path_format(self):
        return self.yaml.get('path')

    def list_docs(self, order_by=None, locale=utils.SENTINEL, reverse=None,
                  include_hidden=False):
        reverse = False if reverse is None else reverse
        order_by = 'order' if order_by is None else order_by
        key = operator.attrgetter(order_by)
        sorted_docs = structures.SortedCollection(key=key)
        for path in self.pod.list_dir(self.pod_path):
            pod_path = os.path.join(self.pod_path, path.lstrip('/'))
            slug, ext = os.path.splitext(os.path.basename(pod_path))
            if (slug.startswith('_')
                    or ext not in messages.extensions_to_formats
                    or not pod_path):
                continue
            try:
                doc = self.get_doc(pod_path)
                if not include_hidden and doc.hidden:
                    continue
                if locale in [utils.SENTINEL, None]:
                    sorted_docs.insert(doc)
                if locale is None:
                    continue
                for each_locale in doc.list_locales():
                    # TODO(jeremydw): Add test for listing documents at the default locale.
                    if each_locale == doc.default_locale and locale != each_locale:
                        continue
                    if locale in [utils.SENTINEL, each_locale]:
                        sorted_docs.insert(self.get_doc(pod_path, locale=each_locale))
            except Exception as e:
                logging.error('Error loading doc: {}'.format(pod_path))
                raise
        return reversed(sorted_docs) if reverse else sorted_docs

    def list_servable_documents(self, include_hidden=False, locales=None):
        docs = []
        for doc in self.list_docs(include_hidden=include_hidden):
            if (self.yaml.get('draft') or not doc.has_serving_path()
                or not doc.get_view() or (locales and doc.locale not in locales)):
                continue
            docs.append(doc)
        return docs

    @property
    def localization(self):
        return self.yaml.get('localization')

    def list_locales(self):
        if 'localization' in self.yaml:
            if self.yaml['localization'].get('use_podspec_locales'):
                return self.pod.list_locales()
            try:
                return locales.Locale.parse_codes(self.localization['locales'])
            except KeyError:
                # Locales inherited from podspec.
                podspec = self.pod.get_podspec()
                config = podspec.get_config()
                if 'localization' in config and 'locales' in config['localization']:
                    return locales.Locale.parse_codes(config['localization']['locales'])
                raise NoLocalesError('{} has no locales.')
        return []

    def to_message(self):
        message = messages.CollectionMessage()
        message.title = self.title
        message.collection_path = self.collection_path
        return message
