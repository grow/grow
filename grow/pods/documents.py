from . import formats
from . import messages
from grow.common import utils
from grow.pods import locales
from grow.pods import urls
import datetime
import json
import logging
import os
import re


class Error(Exception):
    pass


class PathFormatError(Error, ValueError):
    pass


class DocumentDoesNotExistError(Error, ValueError):
    pass


class DocumentExistsError(Error, ValueError):
    pass


class Document(object):

    def __init__(self, pod_path, _pod, locale=None, _collection=None):
        self._locale_kwarg = locale
        utils.validate_name(pod_path)
        self.pod_path = pod_path
        self.root_pod_path = pod_path  # For multi-file localization.
        self.basename = Document._clean_basename(pod_path)
        self.base, self.ext = os.path.splitext(self.basename)
        self.pod = _pod
        self.collection = _collection
        self.locale = self._init_locale(locale, pod_path)

    def __repr__(self):
        if self.locale:
            return "<Document({}, locale='{}')>".format(self.pod_path, self.locale)
        return "<Document({})>".format(self.pod_path)

    def __cmp__(self, other):
        return self.pod_path == other.pod_path and self.pod == other.pod

    def __ne__(self, other):
        return self.pod_path != other.pod_path or self.pod != other.pod

    def _init_locale(self, locale, pod_path):
        try:
            self.root_pod_path, locale_from_path = \
                formats.Format.parse_localized_path(pod_path)
            if locale_from_path:
                locale = locale_from_path
            return self.pod.normalize_locale(
                locale, default=self.default_locale)
        except IOError as exc:  # Document does not exist.
            if '[Errno 2] No such file or directory' in str(exc):
                return None
            else:
                raise

    def __eq__(self, other):
        return (isinstance(self, Document)
                and isinstance(other, Document)
                and self.pod_path == other.pod_path)

    def __getattr__(self, name):
        if name == 'locale':
            return self._locale_kwarg
        try:
            return self.fields[name]
        except KeyError:
            return object.__getattribute__(self, name)

    @classmethod
    def _clean_basename(cls, pod_path):
        pod_path, _ = formats.Format.parse_localized_path(pod_path)
        return os.path.basename(pod_path)

    @utils.cached_property
    def default_locale(self):
        if ('$localization' in self.fields
            and 'default_locale' in self.fields['$localization']):
            locale = self.fields['$localization']['default_locale']
        elif (self.collection.localization
              and 'default_locale' in self.collection.localization):
            locale = self.collection.localization['default_locale']
        else:
            locale = self.pod.podspec.default_locale
        locale = locales.Locale.parse(locale)
        if locale:
            locale.set_alias(self.pod)
        return locale

    @utils.cached_property
    def fields(self):
        tagged_fields = self.get_tagged_fields()
        fields = utils.untag_fields(tagged_fields)
        return {} if not fields else fields

    def get_tagged_fields(self):
        format = formats.Format.get(self)
        return format.fields

    @utils.cached_property
    def format(self):
        return formats.Format.get(self)

    @property
    def url(self):
        path = self.get_serving_path()
        if path:
            return urls.Url(
                path=path,
                host=self.pod.env.host,
                port=self.pod.env.port,
                scheme=self.pod.env.scheme)

    @property
    def slug(self):
        if '$slug' in self.fields:
            return self.fields['$slug']
        return utils.slugify(self.title) if self.title is not None else None

    @property
    def order(self):
        return self.fields.get('$order')

    @property
    def sitemap(self):
        return self.fields.get('$sitemap')

    @property
    def title(self):
        return self.fields.get('$title')

    def titles(self, title_name=None):
        if title_name is None:
            return self.title
        titles = self.fields.get('$titles', {})
        return titles.get(title_name, self.title)

    @property
    def category(self):
        return self.fields.get('$category')

    @property
    def date(self):
        return self.fields.get('$date')

    @property
    def view(self):
        view_format = self.fields.get('$view', self.collection.view)
        if view_format is not None:
            return self._format_path(view_format)

    def dates(self, date_name=None):
        if date_name is None:
            return self.date
        dates = self.fields.get('$dates', {})
        return dates.get(date_name, self.date)

    def delete(self):
        self.pod.delete_file(self.pod_path)

    @property
    def exists(self):
        return self.pod.file_exists(self.pod_path)

    def localize(self, locale):
        return self.collection.get_doc(self.root_pod_path, locale=locale)

    @property
    @utils.memoize
    def path_format(self):
        val = None
        if (self.locale
            and self.default_locale
            and self.locale != self.default_locale):
            if ('$localization' in self.fields
                and 'path' in self.fields['$localization']):
                val = self.fields['$localization']['path']
            elif self.collection.localization:
                val = self.collection.localization['path']
        if val is None:
            return self.fields.get('$path', self.collection.path_format)
        return val

    @property
    @utils.memoize
    def parent(self):
        if '$parent' not in self.fields:
            return None
        parent_pod_path = self.fields['$parent']
        return self.collection.get_doc(parent_pod_path, locale=self.locale)

    @utils.memoize
    def has_serving_path(self):
        return bool(self.path_format)

    @utils.memoize
    def get_serving_path(self):
        # Get root path.
        locale = str(self.locale)
        config = self.pod.get_podspec().get_config()
        root_path = config.get('flags', {}).get('root_path', '')
        if locale == self.default_locale:
            root_path = config.get('localization', {}).get('root_path', root_path)
        path_format = self.path_format
        if path_format is None:
            raise PathFormatError(
                'No path format found for {}. You must specify a path '
                'format in either the blueprint or the document.'.format(self))
        path_format = (path_format
                       .replace('<grow:locale>', '{locale}')
                       .replace('<grow:slug>', '{slug}'))

        # Prevent double slashes when combining root path and path format.
        if path_format.startswith('/') and root_path.endswith('/'):
            root_path = root_path[0:len(root_path) - 1]
        path_format = root_path + path_format

        # Handle default date formatting in the url.
        while '{date|' in path_format:
            re_date = r'({date\|(?P<date_format>[a-zA-Z0-9_%-]+)})'
            match = re.search(re_date, path_format)
            if match:
                formatted_date = self.date
                formatted_date = formatted_date.strftime(match.group('date_format'))
                path_format = (path_format[:match.start()] + formatted_date +
                               path_format[match.end():])
            else:
                # Does not match expected format, let the normal format attempt it.
                break

        # Handle the special formatting of dates in the url.
        while '{dates.' in path_format:
            re_dates = r'({dates\.(?P<date_name>\w+)(\|(?P<date_format>[a-zA-Z0-9_%-]+))?})'
            match = re.search(re_dates, path_format)
            if match:
                formatted_date = self.dates(match.group('date_name'))
                date_format = match.group('date_format') or '%Y-%m-%d'
                formatted_date = formatted_date.strftime(date_format)
                path_format = (path_format[:match.start()] + formatted_date +
                               path_format[match.end():])
            else:
                # Does not match expected format, let the normal format attempt it.
                break

        try:
            return self._format_path(path_format)
        except KeyError:
            logging.error('Error with path format: {}'.format(path_format))
            raise

    def _format_path(self, path_format):
        podspec = self.pod.get_podspec()
        locale = self.locale.alias if self.locale is not None else self.locale
        formatters = {
            'base': self.base,
            'category': self.category,
            'collection.basename': self.collection.basename,
            'collection.root': self.collection.root,
            'env.fingerpint': self.pod.env.fingerprint,
            'locale': locale,
            'parent': self.parent if self.parent else utils.DummyDict(),
            'root': podspec.root,
            'slug': self.slug,
        }
        if '{date' in path_format:
            if isinstance(self.date, datetime.datetime):
                formatters['date'] = self.date.date()
            else:
                formatters['date'] = self.date
        if '|lower' in path_format:
            for key, value in formatters.items():
                if isinstance(value, basestring):
                    formatters['{}|lower'.format(key)] = value.lower()
        return path_format.format(**formatters).replace('//', '/')

    @utils.cached_property
    def locales(self):
        localized = '$localization' in self.fields
        if localized and 'locales' in self.fields['$localization']:
            codes = self.fields['$localization']['locales']
            if codes is None:
                return []
            return locales.Locale.parse_codes(codes)
        return self.collection.locales

    @property
    @utils.memoize
    def body(self):
        return self.format.body.decode('utf-8') if self.format.body else None

    @property
    def content(self):
        return self.format.content.decode('utf-8')

    @property
    def html(self):
        return self.format.html

    @property
    def hidden(self):
        return self.fields.get('$hidden', False)

    def next(self, docs=None):
        if docs is None:
            docs = self.collection.list_docs()
        for i, doc in enumerate(docs):
            if type(doc) != self.__class__:
                raise ValueError('Usage: {{doc.next(<docs>)}}.')
            if doc == self:
                n = i + 1
                if n == len(docs):
                    return None
                return docs[i + 1]

    def prev(self, docs=None):
        if docs is None:
            docs = self.collection.list_docs()
        for i, doc in enumerate(docs):
            if type(doc) != self.__class__:
                raise ValueError('Usage: {{doc.prev(<docs>)}}.')
            if doc == self:
                n = i - 1
                if n < 0:
                    return None
                return docs[i - 1]

    def to_message(self):
        message = messages.DocumentMessage()
        message.basename = self.basename
        message.pod_path = self.pod_path
        message.collection_path = self.collection.collection_path
        message.body = self.body
        message.content = self.content
        message.fields = json.dumps(self.fields, cls=utils.JsonEncoder)
        message.serving_path = self.get_serving_path()
        return message

    def write(self, fields=utils.SENTINEL, body=utils.SENTINEL):
        content = self.content if self.exists else ''
        new_content = formats.Format.update(content, fields=fields, body=body)
        self.pod.write_file(self.pod_path, new_content)

    def inject(self, fields=utils.SENTINEL, body=utils.SENTINEL):
        """Injects without updating the copy on the filesystem."""
        if fields != utils.SENTINEL:
            self.fields.update(fields)
        if body != utils.SENTINEL:
            self.format.body = body
        self.pod.logger.info('Injected -> {}'.format(self.pod_path))
