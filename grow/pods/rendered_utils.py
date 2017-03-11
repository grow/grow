"""Utilities for rendering."""

from grow.common import utils
from grow.pods import footnotes


class RenderedUtilities(object):

    def __init__(self, doc):
        self.doc = doc

    @utils.cached_property
    def footnotes(self):
        # Configure the footnotes based on the doc or podspec settings.
        footnote_config = self.doc.fields.get(
            '$footnotes', self.doc.pod.podspec.fields.get('footnotes', {}))
        locale = str(self.doc.locale) if self.doc.locale else None
        symbols = footnote_config.get('symbols', None)
        use_numeric_symbols = footnote_config.get('use_numeric_symbols', None)
        numeric_locales_pattern = footnote_config.get(
            'numeric_locales_pattern', None)
        return footnotes.Footnotes(
            locale, symbols=symbols, use_numeric_symbols=use_numeric_symbols,
            numeric_locales_pattern=numeric_locales_pattern)
