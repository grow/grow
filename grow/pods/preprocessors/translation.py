from grow.pods.preprocessors import base
from xtermcolor import colorize
import re

SUFFIXES = frozenset(['po'])
SUFFIX_PATTERN = re.compile('[.](' + '|'.join(map(re.escape, SUFFIXES)) + ')$')



class TranslationPreprocessor(base.BasePreprocessor):
  KIND = '_translation'

  def __init__(self, pod):
    self.pod = pod

  def first_run(self):
    self.pod.catalogs.compile()

  def run(self):
    # TODO(jeremydw): Ideally, this would be capable of flushing the gettext cache and
    # recompiling the translations itself without requiring user action.
    text = 'Detected changes to translations. Restart the server to see changes.'
    print colorize(text, ansi=226)

  def list_watched_dirs(self):
    return ['/translations/']
