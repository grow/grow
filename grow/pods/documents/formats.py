from grow.common import markdown_extensions
from grow.common import utils
from markdown.extensions import tables
from markdown.extensions import toc
import collections
import logging
import markdown
import re
import yaml

BOUNDARY = re.compile(r'^-{3,}$', re.MULTILINE)


class Error(Exception):
  pass


class BadFormatError(Error, ValueError):
  pass


class Format(object):

  def __init__(self, doc):
    self.doc = doc
    self.pod = doc.pod
    self.body = None
    self.content = self.pod.read_file(self.doc.pod_path)
    self.has_front_matter = self.content.startswith('---')
    self.fields = {}
    self.load()

  @classmethod
  def get(cls, doc):
    if doc.ext == '.html':
      return HtmlFormat(doc)
    elif doc.ext == '.yaml':
      return YamlFormat(doc)
    elif doc.ext == '.md':
      return MarkdownFormat(doc)
    text = 'Unsupported extension for content file: {}'
    raise BadFormatError(text.format(doc.basename))

  @staticmethod
  def split_front_matter(content):
    parts = BOUNDARY.split(content)
    return parts[1:]

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
      return utils.load_yaml(part, pod=self.doc.pod)
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
      fields = self._load_yaml(part)
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
      if not self.has_front_matter:
        self.fields = utils.load_yaml(self.content, pod=self.doc.pod)
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
    if not self.has_front_matter:
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
          markdown_extensions.CodeBlockExtension(),
          markdown_extensions.IncludeExtension(self.doc.pod),
          markdown_extensions.UrlExtension(self.doc.pod),
      ]
      val = markdown.markdown(val.decode('utf-8'), extensions=extensions)
    return val
