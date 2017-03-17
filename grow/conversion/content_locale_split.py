"""
Utility for converting Grow sites that use multiple locales in one repository
over to a format that uses separate files for each locale.

This is required for all versions of Grow after 0.1.0.

Usage:

    grow convert --version=0.1.0
"""

from boltons import iterutils
from collections import OrderedDict
import collections
import copy
import logging
import os
import re
import yaml

try:
    from yaml import CLoader as yaml_Loader
except ImportError:
    from yaml import Loader as yaml_Loader


class Error(Exception):
    pass


class LocaleExistsError(Error):
    pass


class LocaleMissingError(Error):
    pass


BOUNDARY_REGEX = re.compile(r'^-{3,}$', re.MULTILINE)
DEFAULT_LOCALE_REGEX = re.compile(r'^[ ]{2,4}default_locale:[ ]+(.*)')
LOCALE_REGEX = re.compile(r'^\$locale:(.*)')
LOCALES_REGEX = re.compile(r'^\$locales:$')
LOCALIZED_KEY_REGEX = re.compile('(.*)@([^@]+)$')
LOCALIZATION_REGEX = re.compile(r'^\$localization:$')
ARRAY_ITEM_REGEX = re.compile(r'^[ ]*-[ ]+(.*)')
SUB_ITEM_REGEX = re.compile(r'^[ ]{2,4}')
COMBINED_TEMPLATE = '---\n{}\n---\n{}\n'
SINGLE_TEMPLATE = '{}\n'


def _update_deep(orig_dict, new_dict):
    for k, v in new_dict.iteritems():
        if (k in orig_dict and isinstance(orig_dict[k], dict)
                and isinstance(new_dict[k], collections.Mapping)):
            _update_deep(orig_dict[k], new_dict[k])
        else:
            orig_dict[k] = new_dict[k]


class PlainText(object):

    def __init__(self, tag, value):
        self.tag = tag
        self.value = value


class PlainTextYamlLoader(yaml_Loader):

    def construct_plaintext(self, node):
        return PlainText(node.tag, node.value)


class PlainTextYamlDumper(yaml.Dumper):
    pass


def dict_constructor(loader, node):
    return OrderedDict(loader.construct_pairs(node))


def dict_representer(dumper, data):
    return dumper.represent_dict(data.iteritems())


def plain_text_representer(dumper, data):
    return dumper.represent_scalar(data.tag, data.value)


# Don't want to actually process the constructors, just keep the values
_mapping_tag = yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG
PlainTextYamlDumper.add_representer(OrderedDict, dict_representer)
PlainTextYamlDumper.add_representer(PlainText, plain_text_representer)
PlainTextYamlLoader.add_constructor(_mapping_tag, dict_constructor)
PlainTextYamlLoader.add_constructor(
    u'!_', PlainTextYamlLoader.construct_plaintext)
PlainTextYamlLoader.add_constructor(
    u'!g.csv', PlainTextYamlLoader.construct_plaintext)
PlainTextYamlLoader.add_constructor(
    u'!g.doc', PlainTextYamlLoader.construct_plaintext)
PlainTextYamlLoader.add_constructor(
    u'!g.json', PlainTextYamlLoader.construct_plaintext)
PlainTextYamlLoader.add_constructor(
    u'!g.static', PlainTextYamlLoader.construct_plaintext)
PlainTextYamlLoader.add_constructor(
    u'!g.url', PlainTextYamlLoader.construct_plaintext)
PlainTextYamlLoader.add_constructor(
    u'!g.yaml', PlainTextYamlLoader.construct_plaintext)


class ConversionDocument(object):

    def __init__(self, pod, file_name, default_locale):
        self.default_locale = default_locale
        self.pod = pod
        self.file_name = file_name
        self.raw_content = pod.read_file(file_name)
        self.normalize_raw_content()

    @staticmethod
    def determine_default_locale(front_matter):
        parsed = yaml.load(front_matter, Loader=PlainTextYamlLoader)
        if '$localization' in parsed:
            return parsed['$localization'].get('default_locale', None)
        return None

    @staticmethod
    def determine_locales(front_matter, default_locale=None,
                          remove_default_locale=True, remove_locales=True):
        if not front_matter:
            return [], None

        parsed = yaml.load(front_matter, Loader=PlainTextYamlLoader)
        if isinstance(parsed, str):
            parsed = OrderedDict()
        locales = parsed.get('$locales', [])

        if '$locale' in parsed:
            locales.append(parsed['$locale'])

        if remove_default_locale:
            if default_locale in locales:
                locales.pop(locales.index(default_locale))
            if '$locales' in parsed and default_locale in parsed['$locales']:
                parsed['$locales'].pop(
                    parsed['$locales'].index(default_locale))
            if '$locale' in parsed and parsed['$locale'] == default_locale:
                del parsed['$locale']

        if remove_locales:
            if '$locales' in parsed:
                del parsed['$locales']
            if '$locale' in parsed:
                del parsed['$locale']

        return locales, yaml.dump(
            parsed, Dumper=PlainTextYamlDumper,
            allow_unicode=True, default_flow_style=False).strip() if parsed else ''

    @staticmethod
    def convert_for_locale(front_matter, locale, base=None):
        if not front_matter:
            parsed = {}
        else:
            parsed = yaml.load(front_matter, Loader=PlainTextYamlLoader)

            def visit(path, key, value):
                if not isinstance(key, basestring):
                    return key, value
                if key.endswith('@#'):
                    return key, value

                match = LOCALIZED_KEY_REGEX.match(key)
                if not match:
                    return key, value

                base_key = match.group(1)
                locale_from_key = match.group(2)
                if locale_from_key == locale:
                    # If there is a key without the trailing @ then override it.
                    parent = parsed
                    for path_key in path:
                        parent = parent[path_key]
                    if base_key in parent:
                        return base_key, value
                    return '{}@'.format(base_key), value
                return False

            parsed = iterutils.remap(parsed, visit=visit)

        # If there are pre-existing fields, use them as a base for the locale
        # specific values.
        result = base or {}
        _update_deep(result, parsed)

        return result

    @staticmethod
    def format_file(front_matter=None, content=None):
        if front_matter is None or front_matter.strip() == '':
            return SINGLE_TEMPLATE.format(content.lstrip())
        if content is None or content.strip() == '':
            return SINGLE_TEMPLATE.format(front_matter.lstrip())
        return COMBINED_TEMPLATE.format(front_matter.lstrip(), content.lstrip())

    @staticmethod
    def gather_for_locale(front_matter, locale):
        if not front_matter:
            return ''

        parsed = yaml.load(front_matter, Loader=PlainTextYamlLoader)
        locale_extra = OrderedDict()

        def visit(path, key, value):
            if not isinstance(key, basestring):
                return key, value
            if key.endswith('@#'):
                return key, value

            match = LOCALIZED_KEY_REGEX.match(key)
            if not match:
                return key, value

            base_key = match.group(1)
            locale_from_key = match.group(2)
            if locale_from_key == locale:
                # If there is a key without the trailing @ then override it.
                parent = parsed
                locale_parent = locale_extra

                for path_key in path:
                    parent = parent[path_key]

                    if isinstance(locale_parent, list):
                        locale_parent = locale_parent[path_key]
                    elif path_key not in locale_parent:
                        if isinstance(parent, list):
                            locale_parent[path_key] = copy.deepcopy(parent)
                        else:
                            locale_parent[path_key] = OrderedDict()
                        locale_parent = locale_parent[path_key]
                    else:
                        locale_parent = locale_parent[path_key]

                if base_key in parent:
                    locale_parent[base_key] = value
                else:
                    locale_parent['{}@'.format(base_key)] = value

                if key in locale_parent:
                    locale_parent.pop(key, None)

                return False
            return key, value

        parsed = iterutils.remap(parsed, visit=visit)

        return (yaml.dump(
            parsed, Dumper=PlainTextYamlDumper,
            allow_unicode=True, default_flow_style=False).strip() if parsed else '',
            locale_extra)

    def convert(self):
        # Files with @ in them should already be converted.
        if '@' in self.file_name:
            logging.info(
                'Filename contains a @, skipping: {}'.format(self.file_name))
            return

        # Ignore hidden files.
        if self.file_name.startswith('.'):
            logging.info(
                'Filename starts with ., skipping: {}'.format(self.file_name))
            return

        # Ignore files that don't have an extention
        _, file_extension = os.path.splitext(self.file_name)
        if not file_extension:
            logging.info(
                'Filename does not have an extension, skipping: {}'.format(self.file_name))
            return

        pairs = list(self.split())

        if len(pairs) <= 1:
            logging.info(
                'Single locale detected, skipping: {}'.format(self.file_name))
            return

        logging.info('Converting: {}'.format(self.file_name))
        logging.info(' - Number of content pairs: {}'.format(len(pairs)))

        # Determine if there is a file specific default_locale in first pair.
        default_locale = ConversionDocument.determine_default_locale(
            pairs[0][0]) or self.default_locale
        logging.info(' - Using default_locale: {}'.format(default_locale))

        # Base content will be pruned of localized values that belong in files.
        base_front_matter = pairs[0][0]

        for pair in pairs[1:]:
            locales, _ = ConversionDocument.determine_locales(
                pair[0], default_locale, remove_locales=False,
                remove_default_locale=False)

            if not locales:
                raise LocaleMissingError(
                    'A section in {} is missing a locale and would be lost.'.format(self.file_name))

            # Ensure that there are not existing files for the Locales.
            for locale in locales:
                locale_filename = self.file_name_for_locale(locale)

                if self.pod.file_exists(locale_filename):
                    raise LocaleExistsError(
                        '{} locale section (defined in {}) already has a localized file ({}).\nPlease resolve this confilict and re-run the conversion.'.format(
                            locale, self.file_name, locale_filename))

        # Store each locale contents until the end so we can combine multiple
        # sections that may use the same locale.
        locale_to_content = {}
        locale_to_front_matter = {}

        for pair in pairs[1:]:
            locales, front_matter = ConversionDocument.determine_locales(
                pair[0], default_locale, remove_locales=True,
                remove_default_locale=False)

            for locale in locales:
                locale_to_content[locale] = pair[1]

                if locale in locale_to_front_matter:
                    locale_extra = locale_to_front_matter[locale]
                else:
                    base_front_matter, locale_extra = ConversionDocument.gather_for_locale(
                        base_front_matter, locale)

                # Combine the extra front_matter from the base document with
                # the pair specific front_matter.
                locale_front_matter = ConversionDocument.convert_for_locale(
                    front_matter, locale, base=locale_extra)

                # Store the front matter in case another section adds to it.
                locale_to_front_matter[locale] = locale_front_matter

        # Write the final locale files.
        for locale, locale_front_matter in locale_to_front_matter.iteritems():
            content = locale_to_content.get(locale, None)
            locale_filename = self.file_name_for_locale(locale)
            logging.info('Writing: {}'.format(locale_filename))
            locale_front_matter_dump = yaml.dump(
                locale_front_matter, Dumper=PlainTextYamlDumper, allow_unicode=True,
                default_flow_style=False).strip() if locale_front_matter else ''
            output = ConversionDocument.format_file(
                locale_front_matter_dump, content)
            self.pod.write_file(locale_filename, output)

        # Do the base file after specific tagged fields are removed.
        pair = pairs[0]
        content = pair[1]
        _, base_front_matter = ConversionDocument.determine_locales(
            base_front_matter, default_locale, remove_locales=False,
            remove_default_locale=True)
        logging.info('Writing: {}'.format(self.file_name))
        output = ConversionDocument.format_file(base_front_matter, content)
        self.pod.write_file(self.file_name, output)

    def file_name_for_locale(self, locale_identifier):
        if locale_identifier is None:
            return self.file_name
        file_parts = self.file_name.split('.')
        return '{}@{}.{}'.format(
            '.'.join(file_parts[:-1]), locale_identifier, file_parts[-1])

    def normalize_raw_content(self):
        # Clean and rewrite the yaml files that start with an empty section.
        if self.file_name.endswith('.yaml') and self.raw_content.lstrip().startswith('---'):
            logging.info('Normalizing: {}'.format(self.file_name))
            self.raw_content = self.raw_content.lstrip()[3:].lstrip()
            self.pod.write_file(self.file_name, self.raw_content)

    def split(self):
        parts = BOUNDARY_REGEX.split(self.raw_content)

        # Remove the first, empty list item.
        if parts[0].strip() == '':
            parts.pop(0)

        # Yaml files have no 'content'
        if self.file_name.endswith('.yaml'):
            while parts:
                yield parts.pop(0).strip(), None
        else:
            while parts:
                if len(parts) == 1:
                    yield None, parts.pop(0).strip()
                    break

                front_matter = None
                content = ''
                if parts:
                    front_matter = parts.pop(0).strip() or None
                if parts:
                    content = parts.pop(0).strip() or None
                yield front_matter, content


class Converter(object):

    @staticmethod
    def convert(pod):
        default_locale = pod.podspec.default_locale

        logging.info('Using default locale: {}'.format(default_locale))

        # Go through each document and convert to the updated format.
        for root, dirs, files in pod.walk('/content'):
            pod_dir = root.replace(pod.root, '')

            for file_name in files:
                doc = ConversionDocument(
                    pod, os.path.join(pod_dir, file_name), default_locale)
                try:
                    doc.convert()
                except:
                    print 'Error trying to convert: {}'.format(
                        os.path.join(pod_dir, file_name))
                    raise
