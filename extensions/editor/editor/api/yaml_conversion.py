"""Utility for working with YAML from the editor client."""

import datetime
import re

import yaml

from grow.common import utils

DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')
DATETIME_RE = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$')


def convert_fields(fields):
    """Convert raw field data from submission to typed YAML objects."""

    def _walk_field(item, key, node, parent_node):
        try:
            value = node[key]
            if isinstance(value, str):
                if DATETIME_RE.match(value):
                    node[key] = datetime.datetime.strptime(value, '%Y-%m-%dT%H:%M')
                elif DATE_RE.match(value):
                    temp_value = datetime.datetime.strptime(value, '%Y-%m-%d')
                    node[key] = datetime.date(temp_value.year, temp_value.month, temp_value.day)
        except (KeyError, TypeError, ValueError):
            pass

        if key == 'tag' and isinstance(item, str) and item.startswith('!g.') and 'value' in node:
            new_value = None if not node['value'] else ConstructorReference(item, node['value'])
            if isinstance(parent_node, list):
                for index, elem in enumerate(parent_node):
                    if elem == node:
                        parent_node[index] = new_value
                        break
            elif isinstance(parent_node, dict):
                for parent_key, elem in parent_node.items():
                    if elem == node:
                        parent_node[parent_key] = new_value
                        break

    utils.walk(fields, _walk_field)
    return fields


class ConstructorReference:
    """Helper class to serialize !g.* fields."""

    def __init__(self, tag, pod_path):
        self.tag = tag
        self.pod_path = pod_path


def g_representer(dumper, data):
    return dumper.represent_scalar(data.tag, data.pod_path)


yaml.SafeDumper.add_representer(ConstructorReference, g_representer)
