"""
Document formatting specifics for parsing and working with documents.

Defines how to handle documents formatted in various syntax formats.
"""

from . import document_front_matter as doc_front_matter
from grow.common import markdown_extensions
from grow.common import utils
from markdown.extensions import tables
import markdown


BOUNDARY_SEPARATOR = '---'


class Error(Exception):
    pass


class BadFormatError(Error, ValueError):
    pass


class BadLocalesError(BadFormatError):
    pass


class DocumentFormat(object):

    def __init__(self, doc):
        self._doc = doc

    @staticmethod
    def from_doc(*args, **kwargs):
        doc = kwargs.get('doc', None)
        if not doc:
            raise BadFormatError(
                'Missing `doc` keyword argument for creating format')
        if doc.ext == ('.html'):
            return HtmlDocumentFormat(*args, **kwargs)
        if doc.ext in ('.markdown', '.md', '.mdown', '.mkdn', '.mkd', '.md'):
            return MarkdownDocumentFormat(*args, **kwargs)
        if doc.ext in ('.yaml', '.yml'):
            return YamlDocumentFormat(*args, **kwargs)
        return TextDocumentFormat(*args, **kwargs)

    def _parse_content(self):
        """Parse the content from the raw content."""
        _, parsed_content = doc_front_matter.DocumentFrontMatter\
            .split_front_matter(self.raw_content)
        return parsed_content

    def _parse_front_matter(self):
        """Parse the front matter from the raw content."""
        return doc_front_matter.DocumentFrontMatter(
            self._doc)

    @utils.cached_property
    def content(self):
        """Lazy load the content after checking the content cache."""
        return self._parse_content()

    @utils.cached_property
    def front_matter(self):
        cached_front_matter = self._doc.pod.podcache.document_cache\
            .get_property(self._doc, 'front_matter')
        if cached_front_matter:
            return doc_front_matter.DocumentFrontMatter(
                self._doc, raw_front_matter=cached_front_matter)

        front_matter = self._parse_front_matter()
        self._doc.pod.podcache.document_cache.add_property(
            self._doc, 'front_matter', front_matter.export())
        return front_matter

    @utils.cached_property
    def raw_content(self):
        return self._doc.pod.read_file(self._doc.pod_path)

    @utils.cached_property
    def formatted(self):
        return self.content

    def to_raw_content(self):
        """Formats the front matter and content into a raw_content string."""
        raw_content = ''

        raw_front_matter = self.front_matter.export()
        content = self.content

        if raw_front_matter and content:
            raw_content = '{0}\n{1}\n{0}\n{2}\n'.format(
                BOUNDARY_SEPARATOR, raw_front_matter.strip(), content.strip())
        elif raw_front_matter:
            raw_content = '{}\n'.format(raw_front_matter.strip())
        else:
            raw_content = '{}\n'.format(content.strip())

        return raw_content

    def update(self, fields=utils.SENTINEL, content=utils.SENTINEL):
        """Updates content and frontmatter."""
        if fields is not utils.SENTINEL:
            raw_front_matter = utils.dump_yaml(fields)
            self.front_matter._load_front_matter(raw_front_matter)
            self._doc.pod.podcache.document_cache.add_property(
                self._doc, 'front_matter', self.front_matter.export())

        if content is not utils.SENTINEL:
            self.content = content

        self.raw_content = self.to_raw_content()


class HtmlDocumentFormat(DocumentFormat):

    @utils.cached_property
    def formatted(self):
        val = self.content
        return val.decode('utf-8') if val is not None else None


class MarkdownDocumentFormat(DocumentFormat):

    @utils.cached_property
    def formatted(self):
        val = self.content
        if val is not None:
            extensions = [
                tables.TableExtension(),
                markdown_extensions.TocExtension(pod=self._doc.pod),
                markdown_extensions.CodeBlockExtension(self._doc.pod),
                markdown_extensions.IncludeExtension(self._doc.pod),
                markdown_extensions.UrlExtension(self._doc.pod),
            ]
            val = markdown.markdown(val.decode('utf-8'), extensions=extensions)
        return val


class TextDocumentFormat(DocumentFormat):
    pass


class YamlDocumentFormat(DocumentFormat):

    def _parse_content(self):
        return None

    def _parse_front_matter(self):
        return doc_front_matter.DocumentFrontMatter(
            self._doc, raw_front_matter=self.raw_content)
