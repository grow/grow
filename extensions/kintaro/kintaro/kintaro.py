"""Kintaro extension for integrating Kintaro into Grow sites."""

import copy
import datetime
import json
import logging
import os
import re
import ssl
from collections import defaultdict

import httplib2
import slugify
from googleapiclient import discovery
from jinja2.ext import Extension
from protorpc import messages

import grow
from grow.common import oauth
from grow.documents import document as grow_document

KINTARO_HOST = 'kintaro-content-server.appspot.com'
KINTARO_API_ROOT = 'https://{host}/_ah/api'
DISCOVERY_URL = KINTARO_API_ROOT + '/discovery/v1/apis/{api}/{apiVersion}/rest'
KINTARO_EDIT_PATH_FORMAT = (
    'https://{host}'
    '/app#/project/{project}'
    '/repo/{repo}'
    '/collection/{collection}'
    '/document/{document}/edit'
)
PARTIAL_CONVERSION = re.compile(r'([A-Z])')
_HOST_RE = re.compile(r'^[A-Za-z0-9.-]+$')
STORAGE_KEY = 'Grow SDK - Kintaro'

# Silence extra logging from googleapiclient.
discovery.logger.setLevel(logging.WARNING)

OAUTH_SCOPES = (
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/kintaro',
)


class Error(Exception):
    """General kintaro error."""


class RemoveValueError(Error):
    """Field needs to be removed from the document."""


class UnknownReferenceError(Error):
    """Error finding the referenced kintaro document."""


class UnknownDocumentError(Error):
    """Error finding a kintaro document."""


class InvalidKeyField(Error):
    """Error finding the key field in a kintaro document."""


class BindingMessage(messages.Message):
    collection = messages.StringField(1)
    kintaro_collection = messages.StringField(2)
    key = messages.StringField(3)
    slugify_key = messages.BooleanField(4, default=True)


class LocaleAliasMessage(messages.Message):
    grow_locale = messages.StringField(1)
    kintaro_locale = messages.StringField(2)


def _get_base_field(field):
    localization_removed = field.split('@')[0]
    if localization_removed.startswith('$'):
        return localization_removed[1:]
    return localization_removed


def _validate_host(host):
    if not host or not _HOST_RE.match(host) or '..' in host:
        raise Error(f'Invalid Kintaro host: {host!r}')
    return host


def _sanitize_basename(basename):
    cleaned = str(basename or '').strip()
    if not cleaned or '/' in cleaned or '\\' in cleaned or cleaned in ('.', '..'):
        raise Error(f'Invalid document basename: {basename!r}')
    return cleaned


class GroupedEntry:
    def __init__(self):
        self._fields = {}
        self.schema = None
        self.document_id = None

    @staticmethod
    def is_document_reference(data):
        document_signature_a = sorted(['collection_id', 'repo_id', 'document_id'])
        document_signature_b = sorted(['document_label', *document_signature_a])
        data_keys = sorted(data.keys())
        return data_keys in (document_signature_a, document_signature_b)

    @staticmethod
    def merge_data(original_data, new_data, locale):
        if GroupedEntry.is_document_reference(new_data):
            return new_data

        final_data = copy.deepcopy(original_data)
        for field, value in new_data.items():
            localized_field = f'{field}@{locale}'
            base_value = original_data.get(field)

            if isinstance(value, dict):
                if GroupedEntry.is_document_reference(value):
                    final_data[localized_field] = value
                elif base_value is not None:
                    final_data[field] = GroupedEntry.merge_data(base_value, value, locale)
            elif isinstance(value, list):
                new_value = GroupedEntry.merge_lists(base_value or [], value, locale)
                if base_value != new_value:
                    final_data[localized_field] = new_value
            elif value is None or value == base_value:
                continue
            else:
                final_data[localized_field] = value
        return final_data

    @staticmethod
    def merge_lists(original_list, new_list, locale):
        if not any(x is not None for x in new_list):
            return original_list[:]
        if len(original_list) != len(new_list):
            return new_list
        final_list = []
        for orig_item, new_item in zip(original_list, new_list):
            if isinstance(new_item, dict) and isinstance(orig_item, dict):
                final_list.append(GroupedEntry.merge_data(orig_item, new_item, locale))
            else:
                final_list.append(new_item)
        return final_list

    def add_field_data(self, field_data, locale=None):
        if locale is None:
            self._fields = field_data
        else:
            self._fields = GroupedEntry.merge_data(self._fields, field_data, locale)

    @property
    def fields(self):
        return self._fields

    def to_raw_entry(self):
        return {
            'schema': self.schema,
            'document_id': self.document_id,
            'content_json': json.dumps(self._fields),
        }


class _GoogleServicePreprocessor(grow.Preprocessor):
    _last_run = None

    def create_service(self, host):
        safe_host = _validate_host(host)
        credentials = oauth.get_or_create_credentials(scope=OAUTH_SCOPES, storage_key=STORAGE_KEY)
        http = httplib2.Http()
        http = credentials.authorize(http)
        now = datetime.datetime.now()
        if self._last_run is None or now - self._last_run >= datetime.timedelta(minutes=50):
            credentials.refresh(http)
            self._last_run = now
        url = DISCOVERY_URL.replace('{host}', safe_host)
        return discovery.build('content', 'v1', http=http, discoveryServiceUrl=url)


class KintaroPreprocessor(_GoogleServicePreprocessor):
    KIND = 'kintaro'

    class Config(messages.Message):
        bind = messages.MessageField(BindingMessage, 1, repeated=True)
        repo = messages.StringField(2)
        project = messages.StringField(3)
        host = messages.StringField(4, default=KINTARO_HOST)
        use_index = messages.BooleanField(5, default=True)
        locale_aliases = messages.MessageField(LocaleAliasMessage, 6, repeated=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._service = None
        self._env_regex = None
        self._env_regex_match = None
        self._env_regex_replace = r'@env.\1'
        self._removed = set()
        self._in_use = set()
        self._id_map = {}
        self._kintaro_locale_to_locale_strings = None
        self._locale_strings_to_kintaro_locale = None

    @property
    def service(self):
        if not self._service:
            self._service = self.create_service(host=self.config.host)
        return self._service

    @property
    def locale_strings_to_kintaro_locale(self):
        if not self._locale_strings_to_kintaro_locale:
            self._locale_strings_to_kintaro_locale = {
                locale.grow_locale: locale.kintaro_locale for locale in self.config.locale_aliases
            }
        return self._locale_strings_to_kintaro_locale

    @property
    def kintaro_locale_to_locale_strings(self):
        if not self._kintaro_locale_to_locale_strings:
            self._kintaro_locale_to_locale_strings = {
                locale.kintaro_locale: locale.grow_locale for locale in self.config.locale_aliases
            }
        return self._kintaro_locale_to_locale_strings

    def _get_collection_from_pod_path(self, collection_pod_path):
        collection = self.pod.get_collection(collection_pod_path)
        if not collection.exists:
            self.pod.create_collection(collection_pod_path, {})
        return collection

    def _group_entries(self, entries_by_locale, collection_pod_path, key=None):
        documents_by_id = defaultdict(GroupedEntry)
        raw_sorted_locales = sorted(e for e in entries_by_locale if e is not None)
        sorted_locales = (
            [None, *raw_sorted_locales] if None in entries_by_locale else raw_sorted_locales
        )

        for locale in sorted_locales:
            for entry in entries_by_locale[locale]:
                fields = self._get_entry_field_data(entry)
                doc_id = KintaroPreprocessor._get_doc_id(entry)
                doc_entry = documents_by_id[doc_id]
                doc_entry.add_field_data(fields, locale=locale)

                if locale is None:
                    doc_entry.schema = entry.get('schema', {})
                    doc_entry.document_id = entry.get('document_id', {})

        return documents_by_id.values()

    def bind_collection(self, entries, collection_pod_path, key=None):
        collection = self.pod.get_collection(collection_pod_path)
        if not collection.exists:
            self.pod.create_collection(collection_pod_path, {})
        existing_pod_paths = [
            doc.pod_path for doc in collection.docs(recursive=False, inject=False)
        ]
        new_pod_paths = []
        saved_metadata = False
        for entry in entries:
            fields, _unused_body, basename, schema = self._parse_entry(
                collection.pod_path, entry, key=key
            )
            doc = collection.create_doc(basename, fields=fields, body='')
            new_pod_paths.append(doc.pod_path)
            self.pod.logger.info(f'Saved -> {doc.pod_path}')

            if not saved_metadata:
                meta_filename = os.path.join(collection.pod_path, '_schema.yaml')
                self.pod.write_yaml(meta_filename, schema)
                self.pod.logger.info(f'Schema -> {meta_filename}')
                saved_metadata = True

        pod_paths_to_delete = set(existing_pod_paths) - set(new_pod_paths)
        self._removed = self._removed | pod_paths_to_delete

    def _regroup_schema(self, schema):
        return {field['name']: field for field in schema}

    def _parse_field(self, key, value, field_data, locale=None):
        built_in_fields = getattr(grow_document, 'BUILT_IN_FIELDS', ['title', 'order'])
        if key in built_in_fields:
            key = f'${key}'

        key = self._parse_field_key(key, field_data, locale=locale)

        tagged_regex = re.compile(r'^({})@'.format('|'.join(re.escape(f) for f in built_in_fields)))
        if tagged_regex.search(key):
            key = f'${key}'

        value = self._parse_field_deep(key, value, field_data, locale=locale)
        return key, value

    def _parse_field_deep(self, key, value, field_data, locale=None):
        if (
            self._env_regex_match
            and self._env_regex_match.search(key)
            and key.startswith(('path', '$path'))
        ):
            if field_data['type'] == 'BooleanField':
                if value is True:
                    raise RemoveValueError()
                return None
            if value is None:
                return ''

        if value is None:
            return None

        single_field = not isinstance(value, list)
        if single_field:
            value = [value]

        if field_data['type'] == 'ReferenceField':
            for idx in range(len(value)):
                if not value[idx]:
                    continue
                localized_coll_field = next(
                    (k for k in value[idx] if k.startswith('collection_id@')),
                    '',
                )
                coll_field = localized_coll_field or 'collection_id'
                for binding in self.config.bind:
                    if binding.kintaro_collection == value[idx].get(coll_field):
                        filename = self._get_basename_from_entry(value[idx], key=binding.key)
                        content_path = os.path.join(binding.collection, filename)
                        value[idx] = self.pod.get_doc(content_path, locale=locale)
                        if not value[idx].exists:
                            value[idx].write(fields={})
                        self._in_use.add(value[idx].pod_path)
                        break
        elif 'schema_fields' in field_data:
            names_to_schema_fields = self._regroup_schema(field_data['schema_fields'])
            for idx in range(len(value)):
                value[idx] = self._parse_field_value(
                    value[idx], names_to_schema_fields, locale=locale
                )
        if single_field:
            value = value[0]

        return value

    def _parse_field_key(self, key, field_data, locale=None):
        if field_data['translatable'] and '@' not in key:
            key = f'{key}@'
            if locale:
                key = f'{key}{locale}'
        if self._env_regex:
            key = re.sub(self._env_regex, self._env_regex_replace, key)
        return key

    def _parse_field_value(self, value, names_to_schema_fields, locale=None):
        clean_value = {}
        for sub_key, sub_value in value.items():
            raw_key = _get_base_field(sub_key)
            new_key = self._parse_field_key(sub_key, names_to_schema_fields[raw_key], locale=locale)
            clean_value[new_key] = self._parse_field_deep(
                new_key, sub_value, names_to_schema_fields[raw_key], locale=locale
            )
        return clean_value

    @staticmethod
    def _get_doc_id(entry):
        localized_doc_field = next((k for k in entry if k.startswith('document_id@')), '')
        doc_field = localized_doc_field or 'document_id'
        return str(entry.get(doc_field))

    def _get_basename_from_entry(self, entry, key=None, slugify_key=None):
        doc_id = KintaroPreprocessor._get_doc_id(entry)
        if doc_id not in self._id_map:
            self._set_basename_from_entry(entry, key, slugify_key=slugify_key)
        return f'{_sanitize_basename(self._id_map[doc_id])}.yaml'

    def _get_entry_field_data(self, entry):
        return json.loads(entry.get('content_json', '{}'))

    def _set_basename_from_entry(self, entry, key=None, slugify_key=None):
        slugify_key = True if slugify_key is None else slugify_key
        doc_id = KintaroPreprocessor._get_doc_id(entry)
        if key:
            fields = self._get_entry_field_data(entry)
            if key in fields:
                basename = fields[key]
                if slugify_key:
                    basename = slugify.slugify(basename)
                self._id_map[doc_id] = _sanitize_basename(basename)
            else:
                raise InvalidKeyField(f'Could not find field "{key}" in document {doc_id}')
        else:
            self._id_map[doc_id] = _sanitize_basename(doc_id)

    def _parse_entry(self, collection_path, entry, key=None, locale=None, slugify_key=None):
        deployments = list(self.pod.yaml.get('deployments', {}).keys())
        if deployments and not self._env_regex:
            escaped = '|'.join(re.escape(d) for d in deployments)
            self._env_regex = re.compile(rf'_env_({escaped})$')
            self._env_regex_match = re.compile(rf'@env\.({escaped})$')
        schema = entry.get('schema', {})
        schema_fields = schema.get('schema_fields', [])
        names_to_schema_fields = self._regroup_schema(schema_fields)
        fields = self._get_entry_field_data(entry)
        fields['document_id'] = KintaroPreprocessor._get_doc_id(entry)
        basename = self._get_basename_from_entry(fields, key=key, slugify_key=slugify_key)
        clean_fields = {}
        path = os.path.join(collection_path, basename)
        doc = self.pod.get_doc(path)
        front_matter_data = doc.format.front_matter.data
        if front_matter_data:
            for field_key, value in front_matter_data.items():
                if field_key.startswith('$'):
                    clean_fields[field_key] = value
        for name, value in fields.items():
            if name == 'document_id':
                clean_fields[name] = value
                continue
            raw_name = _get_base_field(name)
            field_data = names_to_schema_fields[raw_name]
            try:
                parsed_key, parsed_value = self._parse_field(name, value, field_data, locale=locale)
                clean_fields[parsed_key] = parsed_value

                if (
                    parsed_key.startswith('$path')
                    and parsed_value in ('', None)
                    and self._env_regex_match
                    and self._env_regex_match.search(parsed_key)
                ):
                    localization = clean_fields.get('$localization', {})
                    localization[parsed_key.lstrip('$')] = parsed_value
                    clean_fields['$localization'] = localization

            except RemoveValueError:
                pass
        if schema:
            schema.pop('mod_info', None)
        clean_fields.pop('$meta', None)
        return clean_fields, '', basename, schema

    def _get_documents_from_search(
        self, repo_id, collection_id, project_id, documents, kintaro_locale=None
    ):
        results = []
        for doc_item in documents:
            document_id = KintaroPreprocessor._get_doc_id(doc_item)
            entry = self._download_entry(
                document_id, collection_id, repo_id, project_id, kintaro_locale=kintaro_locale
            )
            results.append(entry)
        return results

    def download_entries(
        self,
        repo_id,
        collection_id,
        project_id,
        kintaro_locale=None,
        document_id=None,
        key=None,
        slugify_key=None,
    ):
        body = {
            'repo_id': repo_id,
            'collection_id': collection_id,
            'project_id': project_id,
            'document_id': document_id,
            'result_options': {
                'limit': 1000,
                'locale': kintaro_locale,
                'return_json': True,
                'return_schema': True,
            },
        }

        if kintaro_locale is None:
            self.pod.logger.info(f'Downloading documents from {collection_id}')
        else:
            self.pod.logger.info(
                f'Downloading documents from {collection_id} in the {kintaro_locale} locale'
            )

        try:
            resp = self.service.documents().searchDocuments(body=body).execute()
        except ssl.SSLError:
            resp = self.service.documents().searchDocuments(body=body).execute()

        documents = resp.get('document_list', {}).get('documents', [])

        if not self.config.use_index:
            documents_from_get = self._get_documents_from_search(
                repo_id, collection_id, project_id, documents, kintaro_locale=kintaro_locale
            )
            self._update_id_map(documents_from_get, kintaro_locale, key, slugify_key=slugify_key)
            return documents_from_get

        schema = resp.get('schema', {})
        for doc_item in documents:
            doc_item['schema'] = schema

        self._update_id_map(documents, kintaro_locale, key)
        return documents

    def download_and_group_entries(self, bindings, document_id=None):
        entries_with_binding = []
        for binding in bindings:
            entries_by_locale = {}
            for locale in self._get_locale_strings():
                alias = self._get_kintaro_locale_from_locale_string(locale)
                downloaded_entries = self.download_entries(
                    repo_id=self.config.repo,
                    collection_id=binding.kintaro_collection,
                    project_id=self.config.project,
                    kintaro_locale=alias,
                    document_id=document_id,
                    key=binding.key,
                    slugify_key=binding.slugify_key,
                )
                entries_by_locale[locale] = downloaded_entries

            entries_with_binding.append([binding, entries_by_locale])

        results = []
        for binding, entries_by_locale in entries_with_binding:
            grouped_entries = self._group_entries(
                entries_by_locale, binding.collection, key=binding.key
            )
            results.append(
                [binding, [grouped_entry.to_raw_entry() for grouped_entry in grouped_entries]]
            )
        return results

    def download_entry(self, document_id, collection_id, repo_id, project_id):
        return self._download_entry(document_id, collection_id, repo_id, project_id)

    def _download_entry(self, document_id, collection_id, repo_id, project_id, kintaro_locale=None):
        return (
            self.service.documents()
            .getDocument(
                document_id=document_id,
                collection_id=collection_id,
                project_id=project_id,
                repo_id=repo_id,
                include_schema=True,
                locale=kintaro_locale,
                use_json=True,
            )
            .execute()
        )

    def _normalize(self, path):
        return path.rstrip('/') if path else None

    def get_edit_url(self, doc=None):
        if not doc:
            return None
        kintaro_collection = ''
        kintaro_document = doc.base
        doc_pod_path = self._normalize(doc.collection.pod_path)
        for binding in self.config.bind:
            if self._normalize(binding.collection) == doc_pod_path:
                kintaro_collection = binding.kintaro_collection
        if kintaro_collection:
            return KINTARO_EDIT_PATH_FORMAT.format(
                host=_validate_host(self.config.host),
                project=self.config.project,
                repo=self.config.repo,
                collection=kintaro_collection,
                document=kintaro_document,
            )
        return None

    def can_inject(self, doc=None, collection=None):
        if not self.injected:
            return False
        if doc:
            doc_pod_path = self._normalize(doc.collection.pod_path)
            for binding in self.config.bind:
                if self._normalize(binding.collection) == doc_pod_path:
                    return True
        return False

    def inject(self, doc=None, collection=None):
        if doc:
            document_id = KintaroPreprocessor._get_doc_id(doc.fields)
            collection_path = self._normalize(doc.collection.pod_path)
            for binding in self.config.bind:
                if self._normalize(binding.collection) == collection_path:
                    _binding, entries = self.download_and_group_entries(
                        [binding], document_id=document_id
                    )[0]
                    entry = None
                    for entry_candidate in entries:
                        if KintaroPreprocessor._get_doc_id(entry_candidate) == document_id:
                            entry = entry_candidate
                            break

                    if entry is None:
                        raise UnknownDocumentError(f'Unable to retrieve {document_id}')

                    fields, _, _, _ = self._parse_entry(
                        collection_path,
                        entry,
                        key=binding.key,
                        slugify_key=binding.slugify_key,
                    )
                    doc.inject(fields, body='')
                    return doc
        return None

    def _get_locale_strings(self):
        return [None, *self.pod.yaml.get('localization', {}).get('locales', [])]

    def _get_kintaro_locale_from_locale_string(self, grow_locale):
        return self.locale_strings_to_kintaro_locale.get(grow_locale, grow_locale)

    def _get_locale_string_from_kintaro_locale(self, kintaro_locale):
        return self.kintaro_locale_to_locale_strings.get(kintaro_locale, kintaro_locale)

    def _update_id_map(self, raw_entries, kintaro_locale, key, slugify_key=None):
        if kintaro_locale is not None:
            return
        for entry in raw_entries:
            self._set_basename_from_entry(entry, key, slugify_key=slugify_key)

    def run(self, *args, **kwargs):
        entries_with_bindings = self.download_and_group_entries(self.config.bind)

        for binding, entries in entries_with_bindings:
            self.bind_collection(entries, binding.collection)

        for pod_path in self._removed:
            if pod_path in self._in_use:
                self.pod.logger.info(f'Skipping delete for in-use reference -> {pod_path}')
                continue
            self.pod.delete_file(pod_path)
            self.pod.logger.info(f'Deleted -> {pod_path}')


def doc_to_schema_fields(doc, schema_file_name='_schema.yaml'):
    """Parse a doc to retrieve the schema file."""
    return doc_to_schema(doc, schema_file_name=schema_file_name)['schema_fields']


def doc_to_schema(doc, schema_file_name='_schema.yaml'):
    """Parse a doc to retrieve the schema file."""
    return doc.pod.read_yaml(f'{doc.collection.pod_path}/{schema_file_name}')


def schema_name_to_partial(
    value,
    sep='-',
    directory='views/partials',
    use_sub_directory=False,
    prefix='partial',
):
    """Parse a kintaro schema name to determine if it is a partial."""
    if value.lower().startswith(prefix):
        basename = value[len(prefix) :]
        basename = PARTIAL_CONVERSION.sub(rf'{sep}\1', basename)[1:]
        if use_sub_directory:
            directory = f'{directory}/{basename.lower()}'
        return f'/{directory}/{basename.lower()}.html'
    return None


class KintaroExtension(Extension):
    """Add filters for Jinja2 that assist with Kintaro transformations."""

    def __init__(self, environment):
        super().__init__(environment)
        environment.filters['kintaro.schema_name_to_partial'] = schema_name_to_partial
        environment.filters['kintaro.doc_to_schema_fields'] = doc_to_schema_fields
        environment.filters['kintaro.doc_to_schema'] = doc_to_schema
