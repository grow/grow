"""Document formatting specifics for parsing and working with documents."""

import collections
import logging
from grow.common import utils
from grow.documents import document_front_matter as doc_front_matter


# Set markdown logging level to info.
logging.getLogger('MARKDOWN').setLevel(logging.INFO)


BOUNDARY_SEPARATOR = '---'


class Error(Exception):

    def __init__(self, message):
        super(Error, self).__init__(message)
        self.message = message


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

    def organize_fields(self, fields):
        """Structure the fields data to keep some minimal structure."""
        new_fields = collections.OrderedDict()

        # Deep sort all fields by default.
        def _walk_field(item, key, node, parent_node):
            try:
                value = node[key]
                new_value = collections.OrderedDict()
                for sub_key in sorted(value.keys()):
                    new_value[sub_key] = value[sub_key]
                node[key] = new_value
            except:
                pass
        utils.walk(fields, _walk_field)

        # Organization rules:
        # $ prefixed fields should come first.
        # Partials key is last.
        # Partials' partial key should be first in partial data.
        # Sort the fields to keep consistent between saves.

        other_keys = []
        for key in sorted(fields.keys()):
            if key.startswith('$'):
                new_fields[key] = fields[key]
            elif key == 'partials':
                pass
            else:
                other_keys.append(key)

        for key in other_keys:
            new_fields[key] = fields[key]

        if 'partials' in fields:
            new_partials = []

            for partial in fields['partials']:
                new_partial = collections.OrderedDict()

                try:
                    # Put the partial name first for easy readability.
                    if 'partial' in partial:
                        new_partial['partial'] = partial['partial']

                    for key in sorted(partial.keys()):
                        if key != 'partial':
                            new_partial[key] = partial[key]

                    new_partials.append(new_partial)
                except TypeError:
                    # When unable to sort the partial keys, use original.
                    new_partials.append(partial)

            new_fields['partials'] = new_partials

        return new_fields

    def to_raw_content(self):
        """Formats the front matter and content into a raw_content string."""
        raw_front_matter = self.front_matter.export()
        return self.format_doc(raw_front_matter, self.content)

    def update(self, fields=utils.SENTINEL, content=utils.SENTINEL):
        """Updates content and frontmatter."""
        if fields is not utils.SENTINEL:
            # Organize some of the fields for minimal consistency.
            fields = self.organize_fields(fields)

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
        return val if val is not None else None


class MarkdownDocumentFormat(DocumentFormat):

    @utils.cached_property
    def markdown(self):
        """Instance of pod flavored markdown."""
        return self._doc.pod.markdown

    @property
    def toc(self):
        """Markdown TOC extension."""
        # Make sure that the document conversion has happened.
        _ = self.formatted
        # pylint: disable=no-member
        return self.markdown.toc

    @utils.cached_property
    def formatted(self):
        """Markdown formatted content."""
        return self.markdown.convert(
            self.content) if self.content else None


class TextDocumentFormat(DocumentFormat):
    pass


class YamlDocumentFormat(DocumentFormat):

    def _parse_content(self):
        return None

    def _parse_front_matter(self):
        return doc_front_matter.DocumentFrontMatter(
            self._doc, raw_front_matter=self.raw_content)
