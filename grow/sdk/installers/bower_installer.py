"""Bower installer class."""

import subprocess
from grow.sdk.installers import base_installer


class BowerInstaller(base_installer.BaseInstaller):
    """Bower installer."""

    KIND = 'bower'

    @property
    def should_run(self):
        """Should the installer run?"""
        return self.pod.file_exists('/bower.json')

    def check_prerequisites(self):
        """Check if required prerequisites are installed or available."""
        status_command = 'bower --version > /dev/null 2>&1'
        not_found = subprocess.call(
            status_command, **self.subprocess_args(shell=True)) == 127
        if not_found:
            install_commands = [
                'Either add bower to package.json or install globally using:'
                ' `sudo npm install -g bower`']
            raise base_installer.MissingPrerequisiteError(
                'The `bower` command was not found.', install_commands=install_commands)

    def install(self):
        """Install dependencies."""
        install_command = 'bower install'
        process = subprocess.Popen(
            install_command, **self.subprocess_args(shell=True))
        code = process.wait()
        if not code:
            return
        raise base_installer.InstallError(
            'There was an error running `{}`.'.format(install_command))
