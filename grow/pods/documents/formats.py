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

  def _handle_pairs_of_parts_and_bodies(self):
    try:
      locales_to_fields = collections.defaultdict(dict)
      locales_to_bodies = {}
      locale = self.doc._locale_kwarg
      default_locale = None
      document_level_default_locale = None
      split_content = Format.split_front_matter(self.content)
      for i, parts in enumerate(self._iterate_content()):
        part, body = parts
        fields = utils.load_yaml(part, pod=self.doc.pod)

        # Acquires the default locale from the document.
        if i == 0 and '$localization' in fields:
          if 'default_locale' in fields['$localization']:
            document_level_default_locale = fields['$localization']['default_locale']

        if '$locale' in fields and '$locales' in fields:
          text = 'You must specify either $locale or $locales, not both.'
          raise BadFormatError(text)
        if '$locales' in fields:
          doc_locales = fields['$locales']
        else:
          doc_locales = [fields.get('$locale', default_locale)]
        for doc_locale in doc_locales:
          locales_to_fields[doc_locale] = fields
          locales_to_bodies[doc_locale] = body
      fields = locales_to_fields.get(default_locale)

      # Support overriding the base document by specifying another document
      # with the default locale's locale.
      fields = locales_to_fields.get(default_locale)
      if locale is None and document_level_default_locale:
        locale = document_level_default_locale

      if document_level_default_locale in locales_to_fields:
        localized_fields = locales_to_fields[locale]
        fields.update(localized_fields)
      default_body = locales_to_bodies.get(default_locale)
      self.body = locales_to_bodies.get(locale, default_body)
      self.body = self.body.strip() if self.body is not None else None
      self.fields = fields
    except (yaml.composer.ComposerError, yaml.scanner.ScannerError) as e:
      message = 'Error parsing {}: {}'.format(self.doc.pod_path, e)
      logging.exception(message)
      raise BadFormatError(message)


class YamlFormat(_SplitDocumentFormat):

  def _iterate_content(self):
    return [(part, part) for part in Format.split_front_matter(self.content)]

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
    return [(part, body) for part, body in utils.every_two(Format.split_front_matter(self.content))]

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
