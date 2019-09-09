"""Standard support for yaml loading without untagging."""

import yaml

try:
    from yaml import CLoader as YamlLoader
except ImportError:  # pragma: no cover
    from yaml import Loader as YamlLoader


def load_yaml(raw_yaml):
    """Load the yaml using the normal yaml loader."""
    return yaml.load(raw_yaml, Loader=YamlLoader)
