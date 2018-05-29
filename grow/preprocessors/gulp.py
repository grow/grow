"""Preprocessor for running gulp tasks."""

import os
import atexit
import subprocess
from protorpc import messages
from grow.preprocessors import base
from grow.sdk import sdk_utils


# Keep track of any child processes to terminate on exit.
# pylint: disable=invalid-name
_child_processes = []


class Config(messages.Message):
    """Config for Gulp preprocessor."""
    build_task = messages.StringField(1, default='build')
    run_task = messages.StringField(2, default='')
    command = messages.StringField(3, default='gulp')


class GulpPreprocessor(base.BasePreprocessor):
    """Preprocessor for Gulp."""

    KIND = 'gulp'
    Config = Config

    def _get_command(self, task):
        """Construct the command to run the given gulp task."""
        commands = [self.config.command, task]
        if self.pod.file_exists('/.nvmrc'):
            # Need to source NVM first to get the nvm command to work.
            commands = ['. $NVM_DIR/nvm.sh && nvm exec'] + commands
        return ' '.join(commands)

    def run(self, build=True):
        # Avoid restarting the Gulp subprocess if the preprocessor is
        # being run as a result of restarting the server.
        if 'RESTARTED' in os.environ:
            return
        task = self.config.build_task if build else self.config.run_task
        command = self._get_command(task)
        args = sdk_utils.subprocess_args(self.pod, shell=True)
        process = subprocess.Popen(command, **args)
        _child_processes.append(process)
        if not build:
            return
        code = process.wait()
        if code != 0:
            text = 'Failed to run: {}'.format(command)
            raise base.PreprocessorError(text)


@atexit.register
def _kill_child_process():
    """Sometimes the child process keeps going after grow is done running."""
    for process in _child_processes:
        try:
            process.terminate()
            process.wait()
        except OSError:
            # Ignore the error.  The OSError doesn't seem to be documented(?)
            pass
