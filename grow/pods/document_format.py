"""
Document formatting specifics for parsing and working with documents.

Defines how to handle documents formatted in various syntax formats.
"""

from . import document_front_matter as doc_front_matter
from grow.common import utils

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

    @property
    def body(self):
        raise NotImplementedError

    @utils.cached_property
    def content(self):
        """
        Lazy load the content after checking the content cache.
        """
        cached = self._doc.pod.podcache.content_cache.get_property(
            self._doc, 'content')
        if cached:
            return cached

        _, parsed_content = doc_front_matter.DocumentFrontMatter\
            .split_front_matter(self.raw_content)
        self._doc.pod.podcache.content_cache.add_property(
            self._doc, 'content', parsed_content)
        return parsed_content

    @utils.cached_property
    def front_matter(self):
        cached_front_matter = self._doc.pod.podcache.document_cache\
            .get_property(self._doc, 'front_matter')
        if cached_front_matter:
            self._front_matter = doc_front_matter.DocumentFrontMatter(
                self._doc, raw_front_matter=cached_front_matter)
        else:
            self._front_matter = doc_front_matter.DocumentFrontMatter(
                self._doc)
            self._doc.pod.podcache.document_cache.add_property(
                self._doc, 'front_matter', self._front_matter.export())
        return self._front_matter

    @utils.cached_property
    def raw_content(self):
        return self._doc.pod.read_file(self._doc.pod_path)


class HtmlDocumentFormat(DocumentFormat):
    pass


class MarkdownDocumentFormat(DocumentFormat):
    pass


class TextDocumentFormat(DocumentFormat):
    pass


class YamlDocumentFormat(DocumentFormat):
    pass
