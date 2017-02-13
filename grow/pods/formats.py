"""
    Consolidates operations related to dealing with content that has both
    frontmatter and body content. Supports documents formatted in various ways
    (yaml, html, markdown, etc.).
"""

from grow.common import markdown_extensions
from grow.common import utils
from markdown.extensions import tables
import collections
import logging
import markdown
import os
import re
import yaml


BOUNDARY_REGEX = re.compile(r'^-{3,}$', re.MULTILINE)
PATH_LOCALE_REGEX = re.compile('(.*)@([^\.]*)\.(.*)')


class Error(Exception):
    pass


class BadFormatError(Error, ValueError):
    pass


class BadLocalesError(BadFormatError):
    pass


class Format(object):

    def __init__(self, doc):
        self.doc = doc
        self.pod_path = self.doc.pod_path
        self._body = None

        if self._from_cache():
            return

        self._has_front_matter = Format.has_front_matter(self.content)
        self._locales_from_base = []
        self._locales_from_parts = []
        self.fields = {}
        self.load()
        self._to_cache()

    def _from_cache(self):
        cached = self.doc.pod.podcache.document_cache.get_cached_doc(self.doc)

        # print 'retrieved cache: {}'.format(cached)

        if not cached:
            return False

        self._has_front_matter = cached['_has_front_matter']
        self._locales_from_base = cached['_locales_from_base']
        self._locales_from_parts = cached['_locales_from_parts']
        self.fields = cached['fields']
        return True

    def _to_cache(self):
        cached = {}
        cached['_has_front_matter'] = self._has_front_matter
        cached['_locales_from_base'] = self._locales_from_base
        cached['_locales_from_parts'] = self._locales_from_parts
        cached['fields'] = self.fields

        # print 'caching: {}'.format(cached)

        self.doc.pod.podcache.document_cache.cache_doc(self.doc, cached)

    @staticmethod
    def _normalize_frontmatter(pod_path, content, locale=None):
        content = '' if content == '{}\n' else content  # Hack for JSON-formatted YAML.
        if Format.has_front_matter(content):
            if locale:
                fields, body = Format.split_front_matter(content)
                fields += '\n"$locale": "{}"\n'.format(locale)
                return '---\n{}\n---\n{}'.format(fields, body)
            return content
        if pod_path.endswith('.md'):
            if locale:
                return '---\n"$locale": "{}"\n---\n{}'.format(locale, content)
            else:
                return '---\n\n---\n{}'.format(content)
        if locale:
            return '---\n"$locale": "{}"\n{}'.format(locale, content)
        else:
            return '---\n{}'.format(content)

    @staticmethod
    def has_front_matter(content):
        return content.startswith('---')

    @staticmethod
    def split_front_matter(content):
        parts = BOUNDARY_REGEX.split(content)
        return parts[1:]

    @staticmethod
    def update(content, fields=utils.SENTINEL, body=utils.SENTINEL):
        """Updates content with frontmatter. The existing fields and the
        existing body are preserved if they are not specified in arguments."""
        parts = Format.split_front_matter(content) or ['', '']
        if fields is not utils.SENTINEL:
            fields = '\n' + utils.dump_yaml(fields)
            parts[0] = fields
        if body is not utils.SENTINEL and len(parts) > 1:
            parts[1] = '\n' + body
        result = '---' + '---'.join(parts)
        if result.endswith('---\n'):
            return result[:-5]
        return result

    @classmethod
    def get(cls, doc):
        if doc.ext == '.html':
            return HtmlFormat(doc)
        elif doc.ext in ('.yaml', '.yml'):
            return YamlFormat(doc)
        elif doc.ext == '.md':
            return MarkdownFormat(doc)
        text = 'Unsupported extension for content document: {}'
        raise BadFormatError(text.format(doc.basename))

    @classmethod
    def localize_path(cls, pod_path, locale):
        """Returns a localized path (formatted <base>@<locale>.<ext>) for
        multi-file localization."""
        base, ext = os.path.splitext(pod_path)
        return '{}@{}{}'.format(base, locale, ext)

    @classmethod
    def parse_localized_path(cls, pod_path):
        """Returns a tuple containing the root pod path and the locale, parsed
        from a localized pod path (formatted <base>@<locale>.<ext>). If the
        supplied pod path does not contain a locale, the pod path is returned
        along with None."""
        locale_match = PATH_LOCALE_REGEX.match(pod_path)
        if locale_match:
            groups = locale_match.groups()
            locale = groups[1]
            root_pod_path = '{}.{}'.format(groups[0], groups[2])
            return root_pod_path, locale
        return pod_path, None

    @property
    @utils.memoize
    def body(self):
        self.load()
        return self._body

    @property
    @utils.memoize
    def content(self):
        print 'CONTENTS READ!!! : {}'.format(self.pod_path)
        root_pod_path, locale_from_path = \
            Format.parse_localized_path(self.pod_path)
        if locale_from_path:
            if self.doc.pod.file_exists(root_pod_path):
                root_content = self.doc.pod.read_file(root_pod_path)
            else:
                root_content = ''
            localized_content = self.doc.pod.read_file(self.pod_path)
            root_content_with_frontmatter = Format._normalize_frontmatter(
                root_pod_path, root_content)
            localized_content_with_frontmatter = Format._normalize_frontmatter(
                self.pod_path, localized_content, locale=locale_from_path)
            return '{}\n{}'.format(
                root_content_with_frontmatter,
                localized_content_with_frontmatter)
        if self.doc.pod.file_exists(self.pod_path):
            return self.doc.pod.read_file(self.pod_path)
        return ''

    @property
    def has_localized_parts(self):
        return bool(self._locales_from_parts)

    @property
    def html(self):
        return None

    def load(self):
        raise NotImplementedError


class _SplitDocumentFormat(Format):

    def _get_base_default_locale(self, fields):
        if '$localization' in fields:
            if 'default_locale' in fields['$localization']:
                return fields['$localization']['default_locale']
        return self.doc.collection.default_locale

    def _get_locales_of_part(self, fields):
        if '$locales' in fields:
            return fields['$locales']
        else:
            return [fields.get('$locale')]  # None for base document.

    def _handle_pairs_of_parts_and_bodies(self):
        locales_to_fields = collections.defaultdict(dict)
        locales_to_bodies = {}
        locale = self.doc._locale_kwarg
        base_default_locale = None

        for i, parts in enumerate(self._iterate_content()):
            part, body = parts
            fields = self._load_yaml(part) or {}
            self._validate_fields(fields)
            if i == 0:
                self._validate_base_part(fields)
                base_default_locale = self._get_base_default_locale(fields)
                if '$localization' in fields:
                    if 'locales' in fields['$localization']:
                        self._locales_from_base += \
                            fields['$localization']['locales']
            else:
                self._validate_non_base_part(fields)
            for part_locale in self._get_locales_of_part(fields):
                locales_to_fields[part_locale] = fields
                locales_to_bodies[part_locale] = body
                if part_locale:
                    self._locales_from_parts.append(part_locale)

        # Allow $locale to override base locale.
        if locale is None and base_default_locale:
            locale = base_default_locale

        # Merge localized fields into base fields.
        self.fields = locales_to_fields.get(None)
        localized_fields = locales_to_fields.get(locale, {})
        self.fields.update(localized_fields)

        # Merge localized bodies into base body.
        base_body = locales_to_bodies.get(None)
        self._body = locales_to_bodies.get(locale, base_body)
        self._body = self._body.strip() if self._body is not None else None

    def _iterate_content(self):
        parts = [(part, part) for part in Format.split_front_matter(self.content)]
        if not parts[-1][0].strip():
            parts.pop()
        return parts

    def _load_yaml(self, part):
        try:
            return utils.load_yaml(part, doc=self.doc, pod=self.doc.pod)
        except (yaml.parser.ParserError,
                yaml.composer.ComposerError,
                yaml.scanner.ScannerError) as e:
            message = 'Error parsing {}: {}'.format(self.doc.pod_path, e)
            raise BadFormatError(message)

    def _validate_base_part(self, fields):
        self._validate_fields(fields)

    def _validate_fields(self, fields):
        if '$locale' in fields and '$locales' in fields:
            text = 'You must specify either $locale or $locales, not both.'
            raise BadLocalesError(text)

    def _validate_non_base_part(self, fields):
        # Any additional parts after base part MUST declare one or more locales
        # (otherwise there's no point)
        if '$locale' not in fields and '$locales' not in fields:
            text = 'You must specify either $locale or $locales for each document part.'
            raise BadLocalesError(text)
        self._validate_fields(fields)


class HtmlFormat(_SplitDocumentFormat):

    def _iterate_content(self):
        pairs = utils.every_two(Format.split_front_matter(self.content))
        return [(part, body) for part, body in pairs]

    @property
    def html(self):
        if self.body is not None:
            return self.body.decode('utf-8')

    def load(self):
        if not self._has_front_matter:
            self.fields = {}
            self._body = self.content
            return
        self._handle_pairs_of_parts_and_bodies()


class MarkdownFormat(HtmlFormat):

    @property
    def html(self):
        val = self.body
        if val is not None:
            extensions = [
                tables.TableExtension(),
                markdown_extensions.TocExtension(pod=self.doc.pod),
                markdown_extensions.CodeBlockExtension(self.doc.pod),
                markdown_extensions.IncludeExtension(self.doc.pod),
                markdown_extensions.UrlExtension(self.doc.pod),
            ]
            val = markdown.markdown(val.decode('utf-8'), extensions=extensions)
        return val


class YamlFormat(_SplitDocumentFormat):

    def load(self):
        try:
            if self._has_front_matter:
                self._handle_pairs_of_parts_and_bodies()
            else:
                self._body = self.content
                self.fields = utils.load_yaml(
                    self.content,
                    doc=self.doc,
                    pod=self.doc.pod) or {}
        except (yaml.composer.ComposerError, yaml.scanner.ScannerError) as e:
            message = 'Error parsing {}: {}'.format(self.doc.pod_path, e)
            logging.exception(message)
            raise BadFormatError(message)
