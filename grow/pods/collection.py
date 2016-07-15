"""Collections contain content documents and blueprints."""

from . import documents
from . import formats
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
    CONTENT_PATH = '/content'
    BLUEPRINT_PATH = '_blueprint.yaml'
    _content_path_regex = re.compile('^' + CONTENT_PATH + '/?')

    def __init__(self, pod_path, _pod):
        utils.validate_name(pod_path)
        regex = Collection._content_path_regex
        self.pod = _pod
        self.collection_path = regex.sub('', pod_path).strip('/')
        self.pod_path = pod_path
        self.basename = os.path.basename(self.collection_path)
        self._default_locale = _pod.podspec.default_locale
        self._blueprint_path = os.path.join(
            self.pod_path, Collection.BLUEPRINT_PATH)

    def __repr__(self):
        return '<Collection "{}">'.format(self.collection_path)

    def __eq__(self, other):
        return (isinstance(other, Collection)
                and self.collection_path == other.collection_path)

    def __iter__(self):
        for doc in self.list_docs():
            yield doc

    def __getattr__(self, name):
        try:
            return self.fields[name]
        except KeyError:
            return object.__getattribute__(self, name)

    @utils.cached_property
    def fields(self):
        fields = utils.untag_fields(self.tagged_fields)
        return {} if not fields else fields

    @utils.cached_property
    def tagged_fields(self):
        return self.yaml

    @classmethod
    def list(cls, pod):
        items = []
        for root, dirs, _ in pod.walk(cls.CONTENT_PATH + '/'):
            for dir_name in dirs:
                pod_path = os.path.join(root, dir_name)
                pod_path = pod_path.replace(pod.root, '')
                col_path = os.path.join(pod_path, '_blueprint.yaml')
                if pod.file_exists(col_path):
                    items.append(pod.get_collection(pod_path))
        return items

    def collections(self):
        """Returns collections contained within this collection. Implemented
        as a function to allow future implementation of arguments."""
        items = []
        for root, dirs, _ in self.pod.walk(self.pod_path):
            if root == self.pod.abs_path(self.pod_path):
                for dir_name in dirs:
                    pod_path = os.path.join(self.pod_path, dir_name)
                    items.append(self.pod.get_collection(pod_path))
        return items

    @property
    def exists(self):
        """Returns whether the collection exists, as determined by whether
        the collection's blueprint exists."""
        return self.pod.file_exists(self._blueprint_path)

    @classmethod
    def create(cls, collection_path, fields, pod):
        """Creates a new collection by writing a blueprint."""
        collection = cls.get(collection_path, pod)
        if collection.exists:
            raise CollectionExistsError('{} already exists.'.format(collection))
        fields = utils.dump_yaml(fields)
        pod.write_file(collection._blueprint_path, fields)
        return collection

    @classmethod
    def get(cls, collection_path, _pod):
        """Returns a collection object."""
        return cls(collection_path, _pod)

    def get_doc(self, pod_path, locale=None):
        """Returns a document contained in this collection."""
        if locale is not None:
            localized_path = formats.Format.localize_path(pod_path, locale)
            if self.pod.file_exists(localized_path):
                pod_path = localized_path
        return documents.Document(pod_path, locale=locale, _pod=self.pod,
                                  _collection=self)

    def create_doc(self, basename, fields=utils.SENTINEL, body=utils.SENTINEL):
        """Creates a document within the collection."""
        doc_pod_path = os.path.join(self.pod_path, basename)
        doc = self.get_doc(doc_pod_path)
        doc.write(fields=fields, body=body)
        return doc

    @property
    @utils.memoize
    def yaml(self):
        if not self.exists:
            return {}
        result = utils.parse_yaml(self.pod.read_file(self._blueprint_path))
        if result is None:
            return {}
        return result

    def _get_builtin_field(self, name):
        """Returns a builtin field, which is a field prefixed with a `$`. To be
        backwards compatible with the legacy recommendation, we return the
        field unprefixed with `$` if a prefixed field cannot be found."""
        return self.fields.get('${}'.format(name), self.fields.get(name))

    def list_categories(self):
        return self._get_builtin_field('categories') or []

    @property
    def title(self):
        return self._get_builtin_field('title')

    @property
    def root(self):
        return self._get_builtin_field('root')

    @property
    def view(self):
        return self._get_builtin_field('view')

    @property
    def localization(self):
        return self._get_builtin_field('localization')

    @property
    def path_format(self):
        return self._get_builtin_field('path')

    def delete(self):
        if len(self.list_docs(include_hidden=True)):
            text = 'Collections that are not empty cannot be deleted.'
            raise CollectionNotEmptyError(text)
        self.pod.delete_file(self._blueprint_path)

    def list_docs(self, order_by=None, locale=utils.SENTINEL, reverse=None,
                  include_hidden=False, recursive=True, inject=False):
        reverse = False if reverse is None else reverse
        order_by = 'order' if order_by is None else order_by
        key = operator.attrgetter(order_by)
        sorted_docs = structures.SortedCollection(key=key)
        if inject:
            injected_docs = self.pod.inject_preprocessors(collection=self)
            if injected_docs is not None:
                sorted_docs = injected_docs
                self.pod.logger.info('Injected collection -> {}'.format(self.pod_path))
            return reversed(sorted_docs) if reverse else sorted_docs
        for path in self.pod.list_dir(self.pod_path, recursive=recursive):
            pod_path = os.path.join(self.pod_path, path.lstrip('/'))
            slug, ext = os.path.splitext(os.path.basename(pod_path))
            if (slug.startswith('_')
                    or ext not in messages.extensions_to_formats
                    or not pod_path):
                continue
            try:
                _, locale_from_path = \
                    formats.Format.parse_localized_path(pod_path)
                if locale_from_path:
                    if (locale is not None
                            and locale in [utils.SENTINEL, locale_from_path]):
                        new_doc = self.get_doc(pod_path, locale=locale_from_path)
                        if not include_hidden and new_doc.hidden:
                            continue
                        sorted_docs.insert(new_doc)
                    continue
                doc = self.get_doc(pod_path)
                if not include_hidden and doc.hidden:
                    continue
                if locale in [utils.SENTINEL, None]:
                    sorted_docs.insert(doc)
                if locale is None:
                    continue
                if locale == doc.default_locale:
                    sorted_docs.insert(doc)
                else:
                    self._add_localized_docs(sorted_docs, pod_path, locale, doc)
            except Exception as e:
                logging.error('Error loading doc: {}'.format(pod_path))
                raise
        return reversed(sorted_docs) if reverse else sorted_docs

    # Aliases `collection.docs` to `collection.list_docs`. `collection.docs`
    # should be the public and supported way to retrieve documents from a
    # collection.
    docs = list_docs

    def _add_localized_docs(self, sorted_docs, pod_path, locale, doc):
        for each_locale in doc.locales:
            if each_locale == doc.default_locale and locale != each_locale:
                continue
            base, ext = os.path.splitext(pod_path)
            localized_file_path = '{}@{}{}'.format(base, each_locale, ext)
            if (locale in [utils.SENTINEL, each_locale]
                    and not self.pod.file_exists(localized_file_path)):
                new_doc = doc.localize(each_locale)
                sorted_docs.insert(new_doc)

    def list_servable_documents(self, include_hidden=False, locales=None, inject=None):
        docs = []
        inject = False if inject is None else inject
        for doc in self.list_docs(include_hidden=include_hidden, inject=inject):
            if (self._get_builtin_field('draft')
                    or not doc.has_serving_path()
                    or not doc.view
                    or (locales and doc.locale not in locales)):
                continue
            docs.append(doc)
        return docs

    @utils.cached_property
    def locales(self):
        if self.localization:
            if self.localization.get('use_podspec_locales'):
                return self.pod.list_locales()
            try:
                return locales.Locale.parse_codes(self.localization['locales'])
            except KeyError:
                # Locales inherited from podspec.
                podspec = self.pod.get_podspec()
                config = podspec.get_config()
                if ('localization' in config
                        and 'locales' in config['localization']):
                    identifiers = config['localization']['locales']
                    return locales.Locale.parse_codes(identifiers)
                raise NoLocalesError('{} has no locales.')
        return []

    def to_message(self):
        message = messages.CollectionMessage()
        message.title = self.title
        message.collection_path = self.collection_path
        return message
