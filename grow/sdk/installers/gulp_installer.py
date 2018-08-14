"""Gulp installer class."""

import subprocess
from grow.sdk.installers import base_installer


class GulpInstaller(base_installer.BaseInstaller):
    """Gulp installer."""

    KIND = 'gulp'

    @property
    def should_run(self):
        """Should the installer run?"""
        return self.pod.file_exists('/gulpfile.js')

    def check_prerequisites(self):
        """Check if required prerequisites are installed or available."""
        status_command = 'gulp --version > /dev/null 2>&1'
        not_found = subprocess.call(
            status_command, **self.subprocess_args(shell=True)) == 127
        if not_found:
            install_commands = [
                'Either add gulp to package.json or install globally using:'
                ' `sudo npm install -g gulp`']
            raise base_installer.MissingPrerequisiteError(
                'The `gulp` command was not found.', install_commands=install_commands)

    def install(self):
        """Install dependencies."""
        pass
