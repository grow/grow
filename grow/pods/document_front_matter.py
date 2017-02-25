"""
Parsing and manipulation of front matter elements of a document.
"""

from grow.common import utils
import re
import yaml

BOUNDARY_REGEX = re.compile(r'^-{3,}$', re.MULTILINE)

class Error(Exception):
    pass


class BadFormatError(Error, ValueError):
    pass


class DocumentFrontMatter(object):

    def __init__(self, doc, raw_front_matter=None):
        self._doc = doc
        self.data = {}
        self._load_front_matter(raw_front_matter)

    @staticmethod
    def split_front_matter(content):
        parts = BOUNDARY_REGEX.split(content)
        if len(parts) == 3:
            return parts[1].strip(), parts[2].strip()
        return None, content.strip()

    def _load_front_matter(self, raw_front_matter):
        """
        Documents with localization need to base the front-matter off the base
        document to extend or overwrite the base fields.
        """
        # Load base locales from the raw yaml to prevent shared variables.
        for locale_path in reversed(self._doc.locale_paths[1:]):
            if self._doc.pod.file_exists(locale_path):
                locale_doc = self._doc.pod.get_doc(locale_path)
                self.data.update(self._load_yaml(
                    locale_doc.format_x.front_matter.export()))

        if raw_front_matter:
            self._raw_front_matter = raw_front_matter
        else:
            self._raw_front_matter, _ = DocumentFrontMatter.split_front_matter(
                self._doc.raw_content)
        if self._raw_front_matter:
            self.data.update(self._load_yaml(self._raw_front_matter))

    def _load_yaml(self, raw_yaml):
        if not raw_yaml:
            return
        try:
            return utils.load_yaml(
                raw_yaml, doc=self._doc, pod=self._doc.pod)
        except (yaml.parser.ParserError,
                yaml.composer.ComposerError,
                yaml.scanner.ScannerError) as e:
            message = 'Error parsing {}: {}'.format(self._doc.pod_path, e)
            raise BadFormatError(message)

    def export(self):
        """
        Exports the front matter in a raw format.

        This allows it to be cached in a file and parsed when recontructed.
        If exported in the parsed form then any yaml constructors will have
        already run and it will fail since it cannot write the referenced
        objects in the cache file. Also the size can be much larger after the
        yaml has been parsed.
        """
        return self._raw_front_matter
