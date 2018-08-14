"""Nvm installer class."""

import subprocess
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
        status_command = '. $NVM_DIR/nvm.sh && nvm --version > /dev/null 2>&1'
        not_found = subprocess.call(
            status_command, **self.subprocess_args(shell=True)) == 127
        if not_found:
            install_commands = [
                'Download nvm from https://github.com/creationix/nvm']
            raise base_installer.MissingPrerequisiteError(
                'The `nvm` command was not found.', install_commands=install_commands)

    def install(self):
        """Install dependencies."""
        install_command = '. $NVM_DIR/nvm.sh && nvm install'
        process = subprocess.Popen(
            install_command, **self.subprocess_args(shell=True))
        code = process.wait()
        if not code:
            return
        raise base_installer.InstallError(
            'There was an error running `{}`.'.format(install_command))
