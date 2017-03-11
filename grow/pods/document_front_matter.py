"""
Parsing and manipulation of front matter elements of a document.
"""

from grow.common import utils
import collections
import re
import yaml

BOUNDARY_REGEX = re.compile(r'^-{3,}$', re.MULTILINE)
CONVERT_MESSAGE = """Document contains too many parts: {},
    Please run `grow convert --type content_locale_split` to help update files."""


def _update_deep(orig_dict, new_dict):
    for k, v in new_dict.iteritems():
        if (k in orig_dict and isinstance(orig_dict[k], dict)
                and isinstance(new_dict[k], collections.Mapping)):
            _update_deep(orig_dict[k], new_dict[k])
        else:
            orig_dict[k] = new_dict[k]


class Error(Exception):
    pass


class BadFormatError(Error, ValueError):
    pass


class DocumentFrontMatter(object):

    def __init__(self, doc, raw_front_matter=None):
        self._doc = doc
        self.data = {}
        self._raw_front_matter = None
        self._load_front_matter(raw_front_matter)

    @staticmethod
    def split_front_matter(content):
        parts = BOUNDARY_REGEX.split(content)
        if parts[0].strip() == '':
            parts.pop(0)
        if len(parts) > 2:
            message = CONVERT_MESSAGE.format('')
            raise BadFormatError(message)
        if len(parts) == 2:
            return parts[0].strip() or None, parts[1].strip()
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
                raw_locale_front_matter = locale_doc.format.front_matter.export()
                if raw_locale_front_matter:
                    _update_deep(self.data, self._load_yaml(raw_locale_front_matter))

        if raw_front_matter:
            # There should be no boundary separators in the front-matter.
            if BOUNDARY_REGEX.search(raw_front_matter):
                message = CONVERT_MESSAGE.format(
                    self._doc.pod_path)
                raise BadFormatError(message)
            self._raw_front_matter = raw_front_matter
        elif self._doc.exists:
            self._raw_front_matter, _ = DocumentFrontMatter.split_front_matter(
                self._doc.raw_content)

        if self._raw_front_matter:
            _update_deep(self.data, self._load_yaml(self._raw_front_matter))

    def _load_yaml(self, raw_yaml):
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
