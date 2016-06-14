from . import base
from grow.common import sdk_utils
from protorpc import messages
from xtermcolor import colorize
import os
import re
import shlex
import subprocess
import sys



class Config(messages.Message):
    build_task = messages.StringField(1, default='build')
    run_task = messages.StringField(2, default='')
    command = messages.StringField(3, default='gulp')



class GulpPreprocessor(base.BasePreprocessor):
    KIND = 'gulp'
    Config = Config

    def run(self, build=True):
        # Avoid restarting the Gulp subprocess if the preprocessor is
        # being run as a result of restarting the server.
        if 'RESTARTED' in os.environ:
            return
        args = sdk_utils.get_popen_args(self.pod)
        task = self.config.build_task if build else self.config.run_task
        raw_command = '{} {}'.format(self.config.command, task)
        command = shlex.split(raw_command)
        process = subprocess.Popen(command, **args)
        if not build:
            return
        code = process.wait()
        if code != 0:
            text = 'Failed to run: {}'.format(raw_command)
            raise base.PreprocessorError(text)
