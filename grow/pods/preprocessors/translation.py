from grow.pods.preprocessors import base
from xtermcolor import colorize
import os
import re
import sys

SUFFIXES = frozenset(['po'])
SUFFIX_PATTERN = re.compile('[.](' + '|'.join(map(re.escape, SUFFIXES)) + ')$')



class TranslationPreprocessor(base.BasePreprocessor):
  KIND = '_translation'

  def __init__(self, pod):
    self.pod = pod

  def run(self):
    self.pod.logger.info('Detected changes to translations. Restarting.')
    os.execl(sys.argv[0], *sys.argv)

  def list_watched_dirs(self):
    return ['/translations/']
