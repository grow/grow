"""Document formatting specifics for parsing and working with documents."""

import markdown
from markdown.extensions import tables
from grow.common import markdown_extensions
from grow.common import structures
from grow.common import utils
from grow.documents import document_front_matter as doc_front_matter


BOUNDARY_SEPARATOR = '---'


class Error(Exception):
    pass


class BadFormatError(Error, ValueError):
    pass


class BadLocalesError(BadFormatError):
    pass


class DocumentFormat(object):
    """
    Document formatting specifics for parsing and working with documents.

    Defines how to handle documents formatted in various syntax formats.
    """

    def __init__(self, doc):
        self._doc = doc
        self._content = None
        self._raw_content = None

    @staticmethod
    def from_doc(*args, **kwargs):
        doc = kwargs.get('doc', None)
        if not doc:
            raise BadFormatError(
                'Missing `doc` keyword argument for creating format')
        if doc.ext in ('.html', '.htm'):
            return HtmlDocumentFormat(*args, **kwargs)
        if doc.ext in ('.markdown', '.mdown', '.mkdn', '.mkd', '.md'):
            return MarkdownDocumentFormat(*args, **kwargs)
        if doc.ext in ('.yaml', '.yml'):
            return YamlDocumentFormat(*args, **kwargs)
        return TextDocumentFormat(*args, **kwargs)

    @staticmethod
    def format_doc(front_matter, content):
        if front_matter and content:
            return '{0}\n{1}\n{0}\n{2}\n'.format(
                BOUNDARY_SEPARATOR, front_matter.strip(), content.strip())
        elif front_matter:
            return '{}\n'.format(front_matter.strip())
        return '{}\n'.format(content.strip())

    def _parse_content(self):
        """Parse the content from the raw content."""
        _, parsed_content = doc_front_matter.DocumentFrontMatter\
            .split_front_matter(self.raw_content)
        return parsed_content

    def _parse_front_matter(self):
        """Parse the front matter from the raw content."""
        return doc_front_matter.DocumentFrontMatter(
            self._doc)

    @property
    def content(self):
        """Lazy load the content after checking the content cache."""
        if self._content:
            return self._content
        self._content = self._parse_content()
        return self._content

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

    @property
    def raw_content(self):
        if self._raw_content:
            return self._raw_content
        if self._doc.exists:
            self._raw_content = self._doc.pod.read_file(self._doc.pod_path)
        return self._raw_content

    @utils.cached_property
    def formatted(self):
        return self.content

    def to_raw_content(self):
        """Formats the front matter and content into a raw_content string."""
        raw_front_matter = self.front_matter.export()
        return self.format_doc(raw_front_matter, self.content)

    def update(self, fields=utils.SENTINEL, content=utils.SENTINEL):
        """Updates content and frontmatter."""
        if fields is not utils.SENTINEL:
            raw_front_matter = utils.dump_yaml(fields)
            self.front_matter.update_raw_front_matter(raw_front_matter)
            self._doc.pod.podcache.document_cache.add_property(
                self._doc, 'front_matter', self.front_matter.export())

        if content is not utils.SENTINEL:
            self._content = content

        self._raw_content = self.to_raw_content()


class HtmlDocumentFormat(DocumentFormat):

    @utils.cached_property
    def formatted(self):
        val = self.content
        return val.decode('utf-8') if val is not None else None


class MarkdownDocumentFormat(DocumentFormat):

    def get_markdown_config(self, kind):
        """Get the markdown config for a specific extension."""
        if 'markdown' in self._doc.pod.podspec:
            markdown_config = self._doc.pod.podspec.markdown
            if 'extensions' in markdown_config:
                for extension in markdown_config['extensions']:
                    if extension.get('kind', '') != kind:
                        continue
                    return structures.AttributeDict(extension)
        return structures.AttributeDict({})

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
                'markdown.extensions.fenced_code',
                'markdown.extensions.codehilite',
            ]
            config = self.get_markdown_config('markdown.extensions.codehilite')
            codehilite_config = {
                'pygments_style': 'default',
                'noclasses': True,
                'css_class': 'code',
            }
            if 'theme' in config:
                codehilite_config['pygments_style'] = config.theme
            if 'classes' in config:
                codehilite_config['noclasses'] = not config.classes
            if 'class_name' in config:
                codehilite_config['css_class'] = config.class_name
            extension_configs = {
                'markdown.extensions.codehilite': codehilite_config,
            }
            val = markdown.markdown(
                val.decode('utf-8'), extensions=extensions, extension_configs=extension_configs)
        return val


class TextDocumentFormat(DocumentFormat):
    pass


class YamlDocumentFormat(DocumentFormat):

    def _parse_content(self):
        return None

    def _parse_front_matter(self):
        return doc_front_matter.DocumentFrontMatter(
            self._doc, raw_front_matter=self.raw_content)
