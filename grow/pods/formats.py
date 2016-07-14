"""
    Consolidates operations related to dealing with content that has both
    frontmatter and body content. Supports documents formatted in various ways
    (yaml, html, markdown, etc.).
"""

from grow.common import markdown_extensions
from grow.common import utils
from markdown.extensions import tables
from markdown.extensions import toc
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


class Format(object):

    def __init__(self, doc):
        self.doc = doc
        self.pod = doc.pod
        self.body = None
        self.pod_path = self.doc.pod_path
        self.root_pod_path = self.pod_path
        self.locale_from_path = None
        self.content = self._init_content(self.pod_path)
        self._has_front_matter = Format.has_front_matter(self.content)
        self.fields = {}
        self.load()

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

    @classmethod
    def localize_path(cls, pod_path, locale):
        """Returns a localized path (formatted <base>@<locale>.<ext>) for
        multi-file localization."""
        base, ext = os.path.splitext(pod_path)
        return '{}@{}{}'.format(base, locale, ext)

    def _init_content(self, pod_path):
        self.root_pod_path, self.locale_from_path = \
            Format.parse_localized_path(pod_path)
        if self.locale_from_path:
            if self.pod.file_exists(self.root_pod_path):
                root_content = self.pod.read_file(self.root_pod_path)
            else:
                root_content = ''
            localized_content = self.pod.read_file(pod_path)
            root_content_with_frontmatter = Format._normalize_frontmatter(
                self.root_pod_path, root_content)
            localized_content_with_frontmatter = Format._normalize_frontmatter(
                pod_path, localized_content, locale=self.locale_from_path)
            return '{}\n{}'.format(
                root_content_with_frontmatter,
                localized_content_with_frontmatter)
        if self.pod.file_exists(pod_path):
            return self.pod.read_file(pod_path)
        return ''

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

    @property
    def html(self):
        return None

    def load(self):
        raise NotImplementedError


class _SplitDocumentFormat(Format):

    def _iterate_content(self):
        return [(part, part) for part in Format.split_front_matter(self.content)]

    def _validate_fields(self, fields):
        if '$locale' in fields and '$locales' in fields:
            text = 'You must specify either $locale or $locales, not both.'
            raise BadFormatError(text)

    def _get_locales_of_part(self, fields):
        if '$locales' in fields:
            return fields['$locales']
        else:
            return [fields.get('$locale')]  # None for base document.

    def _get_base_default_locale(self, fields):
        if '$localization' in fields:
            if 'default_locale' in fields['$localization']:
                return fields['$localization']['default_locale']

    def _load_yaml(self, part):
        try:
            return utils.load_yaml(part, doc=self.doc, pod=self.doc.pod)
        except (yaml.parser.ParserError,
                yaml.composer.ComposerError,
                yaml.scanner.ScannerError) as e:
            message = 'Error parsing {}: {}'.format(self.doc.pod_path, e)
            raise BadFormatError(message)

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
                base_default_locale = self._get_base_default_locale(fields)
            for part_locale in self._get_locales_of_part(fields):
                locales_to_fields[part_locale] = fields
                locales_to_bodies[part_locale] = body

        # Allow $locale to override base locale.
        if locale is None and base_default_locale:
            locale = base_default_locale

        # Merge localized fields into base fields.
        self.fields = locales_to_fields.get(None)
        localized_fields = locales_to_fields.get(locale, {})
        self.fields.update(localized_fields)

        # Merge localized bodies into base body.
        base_body = locales_to_bodies.get(None)
        self.body = locales_to_bodies.get(locale, base_body)
        self.body = self.body.strip() if self.body is not None else None


class YamlFormat(_SplitDocumentFormat):

    def load(self):
        try:
            if not self._has_front_matter:
                self.fields = utils.load_yaml(
                    self.content,
                    doc=self.doc,
                    pod=self.doc.pod) or {}
                self.body = self.content
                return
            self._handle_pairs_of_parts_and_bodies()
        except (yaml.composer.ComposerError, yaml.scanner.ScannerError) as e:
            message = 'Error parsing {}: {}'.format(self.doc.pod_path, e)
            logging.exception(message)
            raise BadFormatError(message)


class HtmlFormat(YamlFormat):

    def _iterate_content(self):
        pairs = utils.every_two(Format.split_front_matter(self.content))
        return [(part, body) for part, body in pairs]

    def load(self):
        if not self._has_front_matter:
            self.fields = {}
            self.body = self.content
            return
        self._handle_pairs_of_parts_and_bodies()

    @property
    def html(self):
        if self.body is not None:
            return self.body.decode('utf-8')


class MarkdownFormat(HtmlFormat):

    @property
    def html(self):
        val = self.body
        if val is not None:
            extensions = [
                tables.TableExtension(),
                toc.TocExtension(),
                markdown_extensions.CodeBlockExtension(self.doc.pod),
                markdown_extensions.IncludeExtension(self.doc.pod),
                markdown_extensions.UrlExtension(self.doc.pod),
            ]
            val = markdown.markdown(val.decode('utf-8'), extensions=extensions)
        return val
