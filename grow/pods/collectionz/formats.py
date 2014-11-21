from . import messages
from grow.common import markdown_extensions
from grow.common import utils
from markdown.extensions import tables
from markdown.extensions import toc
import markdown
import re
import yaml


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
    text = 'Bad extension for content file: {}'
    raise BadFormatError(text.format(doc.basename))

  @staticmethod
  def split_front_matter(content):
    parts = re.split('(?:^|[\n])---', content, re.DOTALL)
    return parts[1:]

  @property
  def html(self):
    return self.body

  def load(self):
    raise NotImplementedError

  def write(self, content):
    self.content = content
    self.pod.write_file(self.pod_path, content)


class YamlFormat(Format):

  def load(self):
    if not self.has_front_matter:
      self.fields = yaml.load(self.content)
      return
    locales_to_fields = {}
    default_locale_fields = {}
    locale = str(self.doc.locale)
    default_locale = str(self.doc.default_locale)
    for part in Format.split_front_matter(self.content):
      fields = yaml.load(part)
      doc_locale = fields.get('$locale', default_locale)
      locales_to_fields[doc_locale] = fields
    fields = locales_to_fields.get(default_locale)
    if locale in locales_to_fields:
      localized_fields = locales_to_fields[locale]
      if fields is None:
        fields = {}
      fields.update(localized_fields)
    self.fields = fields


class HtmlFormat(YamlFormat):

  def _handle_pairs_of_parts_and_bodies(self):
    locales_to_bodies = {}
    locales_to_fields = {}
    default_locale_fields = {}
    locale = str(self.doc.locale)
    default_locale = str(self.doc.default_locale)
    for part, body in utils.every_two(Format.split_front_matter(self.content)):
      fields = yaml.load(part)
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
      self.fields = yaml.load(self.content)
      self.body = self.content
      return
    self._handle_pairs_of_parts_and_bodies()


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


def untag_fields(fields, catalog):
  """Untags fields, handling translation priority."""
  untagged_keys_to_add = {}
  nodes_and_keys_to_add = []
  nodes_and_keys_to_remove = []
  def callback(item, key, node):
    if not isinstance(key, basestring):
      return
    if key.endswith('@'):
      untagged_key = key.rstrip('@')
      priority = len(key) - len(untagged_key)
      content = node[key]
      nodes_and_keys_to_remove.append((node, key))
      if priority > 1 and untagged_key in untagged_keys_to_add:
        try:
          has_translation_for_higher_priority_key = content in catalog
        except AttributeError:
          has_translation_for_higher_priority_key = False
        if has_translation_for_higher_priority_key:
          untagged_keys_to_add[untagged_key] = True
          nodes_and_keys_to_add.append((node, untagged_key, content))
      elif priority <= 1:
        untagged_keys_to_add[untagged_key] = True
        nodes_and_keys_to_add.append((node, untagged_key, content))
  utils.walk(fields, callback)
  for node, key in nodes_and_keys_to_remove:
    del node[key]
  for node, untagged_key, content in nodes_and_keys_to_add:
    node[untagged_key] = content
  return fields
