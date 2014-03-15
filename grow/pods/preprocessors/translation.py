from grow.common import utils
from grow.pods.preprocessors import base
import logging
import re

SUFFIXES = frozenset(['po'])
SUFFIX_PATTERN = re.compile('[.](' + '|'.join(map(re.escape, SUFFIXES)) + ')$')



class TranslationPreprocessor(base.BasePreprocessor):

  KIND = '_translation'

  def __init__(self, pod):
    self.pod = pod

  def first_run(self):
    # Recompile MO files.
    translations_obj = self.pod.get_translations()
    translations_obj.recompile_mo_files()

  def run(self):
    # TODO(jeremydw): Ideally, this would be capable of flushing the gettext cache and
    # recompiling the translations itself without requiring user action.
    text = '{yellow}Detected changes to translations.{/yellow} Restart the server to see changes.'
    logging.info(utils.colorize(text))

  def list_watched_dirs(self):
    return ['/translations/']
