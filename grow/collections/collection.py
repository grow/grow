"""Collections contain content documents and blueprints."""

import copy
import logging
import operator
import os
import re
import sys
from grow.common import structures
from grow.common import utils
from grow.documents import document
from grow.documents import document_fields
from grow.documents import document_front_matter
from grow.translations import locales
from grow.pods import messages


class Error(Exception):
    pass


class BadCollectionNameError(Error, ValueError):
    pass


class BadFieldsError(Error, ValueError):
    pass


class CollectionDoesNotExistError(Error, ValueError):
    pass


class CollectionExistsError(Error):
    pass


class CollectionNotEmptyError(Error):
    pass


class NoLocalesError(Error):
    pass


class Collection(object):
    CONTENT_PATH = '/content'
    BLUEPRINT_PATH = '_blueprint.yaml'
    EDITOR_PATH = '_editor.yaml'
    IGNORE_INITIAL = ('_',)

    _content_path_regex = re.compile('^' + CONTENT_PATH + '/?')

    def __eq__(self, other):
        return (isinstance(other, Collection)
                and self.collection_path == other.collection_path)

    def __getattr__(self, name):
        try:
            return self.fields[name]
        except KeyError:
            return object.__getattribute__(self, name)

    def __init__(self, pod_path, _pod):
        utils.validate_name(pod_path)
        self.pod = _pod
        self.pod_path = pod_path
        self.collection_path = Collection.clean_collection_path(pod_path)
        self.basename = os.path.basename(self.collection_path)
        self.blueprint_path = os.path.join(
            self.pod_path, Collection.BLUEPRINT_PATH)
        self.editor_path = os.path.join(
            self.pod_path, Collection.EDITOR_PATH)

    def __iter__(self):
        for doc in self.list_docs():
            yield doc

    def __repr__(self):
        return '<Collection "{}">'.format(self.collection_path)

    @classmethod
    def clean_collection_path(cls, pod_path):
        return Collection._content_path_regex.sub('', pod_path).strip('/')

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

    def _get_builtin_field(self, name):
        """Returns a builtin field, which is a field prefixed with a `$`. To be
        backwards compatible with the legacy recommendation, we return the
        field unprefixed with `$` if a prefixed field cannot be found."""
        return self.fields.get('${}'.format(name), self.fields.get(name))

    def _owns_doc_at_path(self, pod_path):
        dir_name = os.path.dirname(pod_path)
        doc_blueprint_path = os.path.join(dir_name, self.BLUEPRINT_PATH)
        if doc_blueprint_path == self.blueprint_path:
            return True
        parts = pod_path.split(os.sep)
        for i, part in enumerate(parts):
            path = os.sep.join(parts[:-i])
            doc_blueprint_path = os.path.join(path, self.BLUEPRINT_PATH)
            if self.pod.file_exists(doc_blueprint_path):
                return doc_blueprint_path == self.blueprint_path
        return False

    @classmethod
    def create(cls, collection_path, fields, pod):
        """Creates a new collection by writing a blueprint."""
        collection = cls.get(collection_path, pod)
        if collection.exists:
            raise CollectionExistsError(
                '{} already exists.'.format(collection))
        fields = utils.dump_yaml(fields)
        pod.write_file(collection.blueprint_path, fields)
        return collection

    @classmethod
    def get(cls, collection_path, _pod):
        """Returns a collection object."""
        return cls(collection_path, _pod)

    @classmethod
    def list(cls, pod):
        items = []
        for root, dirs, _ in pod.walk(cls.CONTENT_PATH + '/'):
            for dir_name in dirs:
                pod_path = os.path.join(root, dir_name)
                pod_path = pod_path.replace(pod.root, '')
                col_path = os.path.join(pod_path, cls.BLUEPRINT_PATH)
                if pod.file_exists(col_path):
                    items.append(pod.get_collection(pod_path))
        return items

    @utils.cached_property
    def default_locale(self):
        if self.localization and 'default_locale' in self.localization:
            locale = self.localization['default_locale']
        else:
            locale = self.pod.podspec.default_locale
        locale = locales.Locale.parse(locale)
        if locale:
            locale.set_alias(self.pod)
        return locale

    @utils.cached_property
    def editor_config(self):
        if not self.pod.file_exists(self.editor_path):
            return {}
        result = utils.parse_yaml(self.pod.read_file(self.editor_path))
        if result is None:
            return {}
        return result

    @property
    def exists(self):
        """Returns whether the collection exists, as determined by whether
        the collection's blueprint exists."""
        return self.pod.file_exists(self.blueprint_path)

    @utils.cached_property
    def fields(self):
        untag = document_fields.DocumentFields.untag
        fields = untag(self.tagged_fields, params={'env': self.pod.env.name})
        return {} if not fields else fields

    @utils.cached_property
    def locales(self):
        localized = ('$localization' in self.fields
                     or 'localization' in self.fields)
        if localized:
            # Disable localization with $localization:~.
            if self.localization is None:
                return []
            if 'locales' in self.localization:
                codes = self.localization['locales'] or []
                return locales.Locale.parse_codes(codes)
        return self.pod.list_locales()

    @property
    def localization(self):
        return self._get_builtin_field('localization')

    @property
    def order(self):
        # Default to maxint so unordered collections go to the end.
        return self.fields.get('$order', sys.maxint)

    @property
    def parent(self):
        parent_pod_path = os.path.normpath(self.pod_path[:-len(self.basename)])
        if parent_pod_path == Collection.CONTENT_PATH:
            return
        return self.pod.get_collection(parent_pod_path)

    @property
    def path_format(self):
        return self._get_builtin_field('path')

    @property
    def root(self):
        return self._get_builtin_field('root')

    @property
    def tagged_fields(self):
        return copy.deepcopy(self.yaml)

    @property
    def title(self):
        return self._get_builtin_field('title')

    @property
    def view(self):
        return self._get_builtin_field('view')

    @utils.cached_property
    def yaml(self):
        if not self.exists:
            return {}
        result = utils.parse_yaml(self.pod.read_file(self.blueprint_path))
        if result is None:
            return {}
        return result

    def create_doc(self, basename, fields=utils.SENTINEL, body=utils.SENTINEL):
        """Creates a document within the collection."""
        doc_pod_path = os.path.join(self.pod_path, basename)
        doc = self.get_doc(doc_pod_path)
        doc.write(fields=fields, body=body)
        return doc

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

    def delete(self):
        if len(self.list_docs(include_hidden=True)):
            text = 'Collections that are not empty cannot be deleted.'
            raise CollectionNotEmptyError(text)
        self.pod.delete_file(self.blueprint_path)

    def get_doc(self, pod_path, locale=None):
        """Returns a document contained in this collection."""
        pod_path = document.Document.clean_localized_path(pod_path, locale)
        if locale is not None:
            localized_path = document.Document.localize_path(pod_path, locale)
            if self.pod.file_exists(localized_path):
                pod_path = localized_path
        cached = self.pod.podcache.collection_cache.get_document(
            self, pod_path, locale)
        if cached:
            return cached
        doc = document.Document(
            pod_path, locale=locale, _pod=self.pod, _collection=self)
        self.pod.podcache.collection_cache.add_document(doc)
        return doc

    def list_categories(self):
        return self._get_builtin_field('categories') or []

    def list_docs(self, order_by=None, locale=utils.SENTINEL, reverse=None,
                  include_hidden=False, recursive=True, inject=False):
        reverse = False if reverse is None else reverse
        if order_by is None:
            order_by = ('order', 'pod_path')
        elif isinstance(order_by, basestring):
            order_by = (order_by, 'pod_path')
        key = operator.attrgetter(*order_by)
        sorted_docs = structures.SortedCollection(key=key)
        if inject:
            injected_docs = self.pod.inject_preprocessors(collection=self)
            if injected_docs is not None:
                sorted_docs = injected_docs
                self.pod.logger.info(
                    'Injected collection -> {}'.format(self.pod_path))
            return reversed(sorted_docs) if reverse else sorted_docs
        for path in self.pod.list_dir(self.pod_path, recursive=recursive):
            pod_path = os.path.join(self.pod_path, path.lstrip('/'))
            # Document is owned by a different collection, skip it.
            if not self._owns_doc_at_path(pod_path):
                continue
            slug, ext = os.path.splitext(os.path.basename(pod_path))
            if (slug.startswith(self.IGNORE_INITIAL)
                    or ext not in messages.extensions_to_formats
                    or not pod_path):
                continue
            try:
                _, locale_from_path = \
                    document.Document.parse_localized_path(pod_path)
                if locale_from_path:
                    if (locale is not None
                            and locale in [utils.SENTINEL, locale_from_path]):
                        new_doc = self.get_doc(
                            pod_path, locale=locale_from_path)
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
                    self._add_localized_docs(
                        sorted_docs, pod_path, locale, doc)
            except Exception as e:
                logging.error('Error loading doc: {}'.format(pod_path))
                raise
        return reversed(sorted_docs) if reverse else sorted_docs

    # Aliases `collection.docs` to `collection.list_docs`. `collection.docs`
    # should be the public and supported way to retrieve documents from a
    # collection.
    docs = list_docs

    def list_docs_unread(self, locale=utils.SENTINEL, recursive=True, inject=False):
        """Lists the docs without triggering a read from the storage system."""
        docs = []
        if inject:
            injected_docs = self.pod.inject_preprocessors(collection=self)
            if injected_docs is not None:
                docs = injected_docs
                self.pod.logger.info(
                    'Injected collection -> {}'.format(self.pod_path))
            return docs
        for path in self.pod.list_dir(self.pod_path, recursive=recursive):
            pod_path = os.path.join(self.pod_path, path.lstrip('/'))
            # Document is owned by a different collection, skip it.
            if not self._owns_doc_at_path(pod_path):
                continue
            slug, ext = os.path.splitext(os.path.basename(pod_path))
            if (slug.startswith(self.IGNORE_INITIAL)
                    or ext not in messages.extensions_to_formats
                    or not pod_path):
                continue
            try:
                _, locale_from_path = \
                    document.Document.parse_localized_path(pod_path)
                if locale_from_path:
                    if (locale is not None
                            and locale in [utils.SENTINEL, locale_from_path]):
                        docs.append(self.get_doc(
                            pod_path, locale=locale_from_path))
                    continue
                docs.append(self.get_doc(pod_path))
            except Exception:
                logging.error('Error loading doc: {}'.format(pod_path))
                raise
        return docs

    def list_servable_documents(self, include_hidden=False, locales=None,
                                inject=None, doc_list=None):
        if not doc_list:
            inject = False if inject is None else inject
            doc_list = self.list_docs(
                include_hidden=include_hidden, inject=inject)
        docs = []
        for doc in doc_list:
            if (self._get_builtin_field('draft')
                    or not doc.has_serving_path()
                    or not doc.view
                    or (locales and doc.locale not in locales)):
                continue

            # If there is a localized version of the default locale
            # the base document should not be added with the same locale.
            if (doc.locale and doc.locale == doc.default_locale and
                    not document.Document.is_localized_path(doc.pod_path)):
                localized_path = document.Document.localize_path(
                    doc.pod_path, doc.locale)
                if self.pod.file_exists(localized_path):
                    continue

            docs.append(doc)
        return docs

    def list_servable_document_locales(self, pod_path, include_hidden=False,
                                       locales=None):
        sorted_docs = structures.SortedCollection(key=None)
        doc = self.get_doc(pod_path)

        try:
            doc.has_serving_path()  # Using doc fields forces file read.
        except document_front_matter.BadFormatError:
            # Skip adding invalid documents.
            return []

        sorted_docs.insert(doc)
        self._add_localized_docs(sorted_docs, pod_path, utils.SENTINEL, doc)
        return self.list_servable_documents(
            include_hidden=include_hidden, locales=locales, doc_list=sorted_docs)

    def titles(self, title_name=None):
        if title_name is None:
            return self.title
        titles = self.fields.get('$titles', {})
        return titles.get(title_name, self.title)

    def to_message(self):
        message = messages.CollectionMessage()
        message.title = self.title
        message.collection_path = self.collection_path
        return message
