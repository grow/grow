from . import document_fields
from . import document_format
from . import footnotes
from . import locales
from . import messages
from . import urls
from grow.common import utils
import datetime
import json
import logging
import os
import re


PATH_LOCALE_REGEX = re.compile(r'@([^-_]+)([-_]?)([^\.]*)(\.[^\.]+)$')


class Error(Exception):
    pass


class DocumentDoesNotExistError(Error, ValueError):
    pass


class DocumentExistsError(Error, ValueError):
    pass


class PathFormatError(Error, ValueError):
    pass


class Document(object):

    def __cmp__(self, other):
        return self.pod_path == other.pod_path and self.pod == other.pod

    def __eq__(self, other):
        return (isinstance(self, Document)
                and isinstance(other, Document)
                and self.root_pod_path == other.root_pod_path)

    def __getattr__(self, name):
        if name == 'locale':
            return self._locale_kwarg
        try:
            return self.fields[name]
        except KeyError:
            return object.__getattribute__(self, name)

    def __init__(self, pod_path, _pod, locale=None, _collection=None):
        self._locale_kwarg = locale
        utils.validate_name(pod_path)
        self.pod_path = pod_path
        self.root_pod_path = pod_path  # For multi-file localization.
        self.basename = Document._clean_basename(pod_path)
        self.base, self.ext = os.path.splitext(self.basename)
        self.pod = _pod
        self.collection = _collection
        self._locale = utils.SENTINEL

    def __ne__(self, other):
        return self.pod_path != other.pod_path or self.pod != other.pod

    def __repr__(self):
        if self.locale:
            return "<Document({}, locale='{}')>".format(self.pod_path, self.locale)
        return "<Document({})>".format(self.pod_path)

    @classmethod
    def _clean_basename(cls, pod_path):
        base_pod_path = cls._locale_paths(pod_path)[-1]
        return os.path.basename(base_pod_path)

    @classmethod
    def _locale_paths(cls, pod_path):
        paths = [pod_path]
        parts = PATH_LOCALE_REGEX.split(pod_path)
        if len(parts) > 1:
            if parts[3]: # [3] -> Country Code
                paths.append('{}@{}{}'.format(parts[0], parts[1], parts[4]))
            paths.append('{}{}'.format(parts[0], parts[4]))
        return paths

    @classmethod
    def clean_localized_path(cls, pod_path, locale):
        """Removed the localized part of the path."""
        if '@' in pod_path and locale is not None:
            base, _ = os.path.splitext(pod_path)
            if not base.endswith('@{}'.format(locale)):
                pod_path = cls._locale_paths(pod_path)[-1]
        return pod_path

    @classmethod
    def is_localized_path(cls, pod_path):
        return '@' in pod_path

    @classmethod
    def localize_path(cls, pod_path, locale):
        """Returns a localized path (formatted <base>@<locale>.<ext>) for
        multi-file localization."""
        pod_path = cls.clean_localized_path(pod_path, locale)
        if locale is None:
            return pod_path
        base, ext = os.path.splitext(pod_path)
        return '{}@{}{}'.format(base, locale, ext)

    @classmethod
    def parse_localized_path(cls, pod_path):
        """Returns a tuple containing the root pod path and the locale, parsed
        from a localized pod path (formatted <base>@<locale>.<ext>). If the
        supplied pod path does not contain a locale, the pod path is returned
        along with None."""
        groups = PATH_LOCALE_REGEX.split(pod_path)
        if len(groups) > 1:
            if groups[3]:
                locale = '{}{}{}'.format(groups[1], groups[2], groups[3])
            else:
                locale = groups[1]
            root_pod_path = '{}{}'.format(groups[0], groups[4])
            return root_pod_path, locale
        return pod_path, None

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

    def _init_locale(self, locale, pod_path):
        try:
            self.root_pod_path, locale_from_path = \
                Document.parse_localized_path(pod_path)
            if locale_from_path:
                locale = locale_from_path
            return self.pod.normalize_locale(
                locale, default=self.default_locale)
        except IOError as exc:  # Document does not exist.
            if '[Errno 2] No such file or directory' in str(exc):
                return None
            else:
                raise

    @property
    def body(self):
        return self.format.content.decode('utf-8') if self.format.content else None

    @property
    def category(self):
        return self.fields.get('$category')

    @property
    def content(self):
        return self.format.raw_content.decode('utf-8')

    @property
    def date(self):
        return self.fields.get('$date')

    @utils.cached_property
    def default_locale(self):
        if (self.fields.get('$localization')
            and 'default_locale' in self.fields['$localization']):
            identifier = self.fields['$localization']['default_locale']
            locale = locales.Locale.parse(identifier)
            if locale:
                locale.set_alias(self.pod)
            return locale
        return self.collection.default_locale

    @property
    def exists(self):
        return self.pod.file_exists(self.pod_path)

    @utils.cached_property
    def fields(self):
        locale_identifier = str(
            self._locale_kwarg or self.collection.default_locale)
        return document_fields.DocumentFields(
            self.format.front_matter.data, locale_identifier)

    @utils.cached_property
    def footnotes(self):
        # Configure the footnotes based on the doc or podspec settings.
        footnote_config = self.fields.get(
            '$footnotes', self.pod.podspec.fields.get('footnotes', {}))
        locale = str(self.locale) if self.locale else None
        symbols = footnote_config.get('symbols', None)
        use_numeric_symbols = footnote_config.get('use_numeric_symbols', None)
        numeric_locales_pattern = footnote_config.get(
            'numeric_locales_pattern', None)
        return footnotes.Footnotes(
            locale, symbols=symbols, use_numeric_symbols=use_numeric_symbols,
            numeric_locales_pattern=numeric_locales_pattern)

    @utils.cached_property
    def format(self):
        return document_format.DocumentFormat.from_doc(doc=self)

    @property
    def formatted(self):
        return self.format.formatted

    @property
    def hidden(self):
        return self.fields.get('$hidden', False)

    @property
    def html(self):
        return self.formatted

    @utils.cached_property
    def locale(self):
        if self._locale is utils.SENTINEL:
            self._locale = self._init_locale(self._locale_kwarg, self.pod_path)
        return self._locale

    @utils.cached_property
    def locale_paths(self):
        return Document._locale_paths(self.pod_path)

    @utils.cached_property
    def locales(self):
        # Use $localization:locales if present, else use collection's locales.
        localized = '$localization' in self.fields
        if localized:
            localization = self.fields['$localization']
            # Disable localization with $localization:~.
            if localization is None:
                return []
            if 'locales' in localization:
                codes = localization['locales'] or []
                return locales.Locale.parse_codes(codes)
        return self.collection.locales

    @property
    def order(self):
        return self.fields.get('$order')

    @property
    @utils.memoize
    def parent(self):
        if '$parent' not in self.fields:
            return None
        parent_pod_path = self.fields['$parent']
        return self.collection.get_doc(parent_pod_path, locale=self.locale)

    @property
    @utils.memoize
    def path_format(self):
        val = None
        if (self.locale
            and self.locale != self.default_locale):
            if ('$localization' in self.fields
                and 'path' in self.fields['$localization']):
                val = self.fields['$localization']['path']
            elif self.collection.localization:
                val = self.collection.localization.get('path')
        if val is None:
            return self.fields.get('$path', self.collection.path_format)
        return val

    @property # Cached in document format.
    def raw_content(self):
        return self.format.raw_content

    @property
    def slug(self):
        if '$slug' in self.fields:
            return self.fields['$slug']
        return utils.slugify(self.title) if self.title is not None else None

    @property
    def sitemap(self):
        return self.fields.get('$sitemap')

    @property
    def title(self):
        return self.fields.get('$title')

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

    @utils.memoize
    def has_serving_path(self):
        return bool(self.path_format)

    def inject(self, fields=utils.SENTINEL, body=utils.SENTINEL):
        """Injects without updating the copy on the filesystem."""
        if fields != utils.SENTINEL:
            self.fields.update(fields)
        if body != utils.SENTINEL:
            self.format.body = body
        self.pod.logger.info('Injected -> {}'.format(self.pod_path))

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

    def localize(self, locale):
        return self.collection.get_doc(self.root_pod_path, locale=locale)

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

    def titles(self, title_name=None):
        if title_name is None:
            return self.title
        titles = self.fields.get('$titles', {})
        return titles.get(title_name, self.title)

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
        if body is utils.SENTINEL:
            body = self.body if self.exists else ''
        self.format.update(fields=fields, content=body)
        new_content = self.format.to_raw_content()
        self.pod.write_file(self.pod_path, new_content)
