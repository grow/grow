"""Nvm installer class."""

import os
import subprocess
from grow.sdk import sdk_utils
from grow.sdk.installers import base_installer


class NvmInstaller(base_installer.BaseInstaller):
    """Nvm installer."""

    KIND = 'nvm'

    @property
    def should_run(self):
        """Should the installer run?"""
        return self.pod.file_exists('/.nvmrc')

    def check_prerequisites(self):
        """Check if required prerequisites are installed or available."""
        if 'NVM_DIR' not in os.environ:
            install_commands = [
                'Download nvm from https://github.com/creationix/nvm']
            raise base_installer.MissingPrerequisiteError(
                'The `nvm` command was not found.', install_commands=install_commands)

    def install(self):
        """Install dependencies."""
        install_command = sdk_utils.get_nvm_command('install')
        process = subprocess.Popen(
            install_command, **self.subprocess_args(shell=True))
        code = process.wait()
        if not code:
            use_command = sdk_utils.get_nvm_command('use')
            process = subprocess.Popen(
                use_command, **self.subprocess_args(shell=True))
            code = process.wait()
            if not code:
                return
            raise base_installer.InstallError(
                'There was an error running `{}`.'.format(use_command))
        raise base_installer.InstallError(
            'There was an error running `{}`.'.format(install_command))
