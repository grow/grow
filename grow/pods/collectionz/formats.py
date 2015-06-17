from grow.common import markdown_extensions
from grow.common import utils
from markdown.extensions import tables
from markdown.extensions import toc
import markdown
import re


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
    parts = re.split('(?:^|[\n])---', content, re.DOTALL)
    return parts[1:]

  @property
  def html(self):
    return None

  def load(self):
    raise NotImplementedError

  def write(self, content):
    self.content = content
    self.pod.write_file(self.pod_path, content)


class YamlFormat(Format):

  def load(self):
    if not self.has_front_matter:
      self.fields = utils.load_yaml(self.content)
      self.body = self.content
      return
    locales_to_fields = {}
    locales_to_bodies = {}
    locale = str(self.doc.locale)
    default_locale = str(self.doc.default_locale)
    for part in Format.split_front_matter(self.content):
      fields = utils.load_yaml(part)
      doc_locale = fields.get('$locale', default_locale)
      locales_to_fields[doc_locale] = fields
      locales_to_bodies[doc_locale] = part
    fields = locales_to_fields.get(default_locale)
    if locale in locales_to_fields:
      localized_fields = locales_to_fields[locale]
      if fields is None:
        fields = {}
      fields.update(localized_fields)
    self.body = locales_to_bodies.get(locale, locales_to_bodies.get(default_locale))
    self.body = self.body.strip() if self.body is not None else None
    self.fields = fields


class HtmlFormat(YamlFormat):

  def _handle_pairs_of_parts_and_bodies(self):
    locales_to_bodies = {}
    locales_to_fields = {}
    locale = str(self.doc.locale)
    default_locale = str(self.doc.default_locale)
    for part, body in utils.every_two(Format.split_front_matter(self.content)):
      fields = utils.load_yaml(part)
      doc_locale = fields.get('$locale', default_locale)
      locales_to_fields[doc_locale] = fields
      locales_to_bodies[doc_locale] = body
    fields = locales_to_fields.get(default_locale)
    if locale in locales_to_fields:
      localized_fields = locales_to_fields[locale]
      if fields is None:
        fields = {}
      fields.update(localized_fields)
    self.body = locales_to_bodies.get(locale, locales_to_bodies.get(default_locale))
    self.body = self.body.strip() if self.body is not None else None
    self.fields = fields

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

  def load(self):
    if not self.has_front_matter:
      self.fields = {}
      self.body = self.content
      return
    self._handle_pairs_of_parts_and_bodies()

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
