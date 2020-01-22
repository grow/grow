"""Custom yaml loaders for Grow."""

import datetime
import types
from collections import OrderedDict
import yaml
from yaml.representer import Representer
from yaml.representer import SafeRepresenter

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
    return dumper.represent_dict(data.items())


def plain_text_representer(dumper, data):
    return dumper.represent_scalar(data['tag'], data['value'])


# Don't want to actually process the constructors, just keep the values
PlainTextYamlDumper.add_representer(OrderedDict, plain_text_dict_representer)
PlainTextYamlDumper.add_representer(PlainText, plain_text_representer)
PlainTextYamlDumper.add_representer(type(None), SafeRepresenter.represent_none)
PlainTextYamlDumper.add_representer(str, SafeRepresenter.represent_str)
PlainTextYamlDumper.add_representer(bool, SafeRepresenter.represent_bool)
PlainTextYamlDumper.add_representer(int, SafeRepresenter.represent_int)
PlainTextYamlDumper.add_representer(float, SafeRepresenter.represent_float)
PlainTextYamlDumper.add_representer(list, SafeRepresenter.represent_list)
PlainTextYamlDumper.add_representer(tuple, SafeRepresenter.represent_list)
PlainTextYamlDumper.add_representer(dict, SafeRepresenter.represent_dict)
PlainTextYamlDumper.add_representer(set, SafeRepresenter.represent_set)
PlainTextYamlDumper.add_representer(
    datetime.date, SafeRepresenter.represent_date)
PlainTextYamlDumper.add_representer(
    datetime.datetime, SafeRepresenter.represent_datetime)
PlainTextYamlDumper.add_representer(None, SafeRepresenter.represent_undefined)
PlainTextYamlDumper.add_multi_representer(object, Representer.represent_object)


PlainTextYamlLoader.add_constructor(
    '!_', PlainTextYamlLoader.construct_plaintext)
PlainTextYamlLoader.add_constructor(
    '!g.csv', PlainTextYamlLoader.construct_plaintext)
PlainTextYamlLoader.add_constructor(
    '!g.doc', PlainTextYamlLoader.construct_plaintext)
PlainTextYamlLoader.add_constructor(
    '!g.json', PlainTextYamlLoader.construct_plaintext)
PlainTextYamlLoader.add_constructor(
    '!g.static', PlainTextYamlLoader.construct_plaintext)
PlainTextYamlLoader.add_constructor(
    '!g.string', PlainTextYamlLoader.construct_plaintext)
PlainTextYamlLoader.add_constructor(
    '!g.url', PlainTextYamlLoader.construct_plaintext)
PlainTextYamlLoader.add_constructor(
    '!g.yaml', PlainTextYamlLoader.construct_plaintext)
