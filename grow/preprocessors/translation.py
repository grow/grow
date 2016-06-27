from . import base
from grow.common import sdk_utils
from xtermcolor import colorize
import os
import re
import sys

SUFFIXES = frozenset(['po'])
SUFFIX_PATTERN = re.compile('[.](' + '|'.join(map(re.escape, SUFFIXES)) + ')$')


class TranslationPreprocessor(base.BasePreprocessor):
    """Automatically recompiles translations when needed."""
    KIND = '_translation'

    def __init__(self, pod):
        self.pod = pod

    def run(self, build=True):
        self.pod.catalogs.compile()

    def list_watched_dirs(self):
        return ['/translations/']
