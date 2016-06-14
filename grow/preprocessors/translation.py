from . import base
from grow.common import sdk_utils
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

    def run(self, build=True):
        # Indicate the server was restarted to avoid re-running
        # preprocessors that shouldn't be re-run.
        env = sdk_utils.get_popen_args(self.pod)['env']
        env['RESTARTED'] = '1'
        self.pod.logger.info('Detected changes to translations. Restarting.')
        args = [arg for arg in sys.argv if arg not in ['-b', '--browser']]
        args.append(env)
        os.execle(args[0], *args)

    def list_watched_dirs(self):
        return ['/translations/']
