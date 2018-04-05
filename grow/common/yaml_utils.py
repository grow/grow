"""Custom yaml loaders for Grow."""

from collections import OrderedDict
import yaml

try:
    from yaml import CLoader as yaml_Loader
except ImportError:
    from yaml import Loader as yaml_Loader


class PlainText(dict):

    def __init__(self, tag, value):
        super(PlainText, self)
        self['tag'] = tag
        self['value'] = value


class PlainTextYamlLoader(yaml_Loader):
    """Loader for loading as plain text."""

    def construct_plaintext(self, node):
        return PlainText(node.tag, node.value)


class PlainTextYamlDumper(yaml.Dumper):
    """Dumper for working with plain text yaml."""
    pass


def plain_text_dict_constructor(loader, node):
    return OrderedDict(loader.construct_pairs(node))


def plain_text_dict_representer(dumper, data):
    return dumper.represent_dict(data.iteritems())


def plain_text_representer(dumper, data):
    return dumper.represent_scalar(data['tag'], data['value'])


# Don't want to actually process the constructors, just keep the values
PlainTextYamlDumper.add_representer(OrderedDict, plain_text_dict_representer)
PlainTextYamlDumper.add_representer(PlainText, plain_text_representer)
PlainTextYamlLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, plain_text_dict_constructor)
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
