"""Preprocessor for running gulp tasks."""

import os
import shlex
import subprocess
from protorpc import messages
from grow.common import sdk_utils
from . import base


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
        if sdk_utils.has_nvmrc(self.pod):
            nvm_use_command = '{};'.format(
                sdk_utils.format_nvm_shell_command('use'))
        else:
            nvm_use_command = ''

        raw_command = '{} {} {}'.format(
            nvm_use_command, self.config.command, task)

        process = subprocess.Popen(raw_command, shell=True, **args)
        if not build:
            return
        code = process.wait()
        if code != 0:
            text = 'Failed to run: {}'.format(raw_command)
            raise base.PreprocessorError(text)
