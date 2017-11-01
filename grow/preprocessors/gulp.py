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

    def _get_nvm_use_prefix(self):
        """Return the nvm command to run ahead of gulp (if any)."""
        if sdk_utils.has_nvmrc(self.pod):
            return '{};'.format(sdk_utils.format_nvm_shell_command('use'))
        return None

    def _get_command(self, task):
        """Construct the command to run the given gulp task."""
        commands = [self.config.command, task]
        nvm_use_command = self._get_nvm_use_prefix()
        if nvm_use_command:
            commands = [nvm_use_command] + commands
        return ' '.join(commands)

    def run(self, build=True):
        # Avoid restarting the Gulp subprocess if the preprocessor is
        # being run as a result of restarting the server.
        if 'RESTARTED' in os.environ:
            return
        args = sdk_utils.get_popen_args(self.pod)
        task = self.config.build_task if build else self.config.run_task
        command = self._get_command(task)
        process = subprocess.Popen(command, shell=True, **args)
        if not build:
            return
        code = process.wait()
        if code != 0:
            text = 'Failed to run: {}'.format(command)
            raise base.PreprocessorError(text)
