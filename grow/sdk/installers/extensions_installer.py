"""Grow extensions installer class."""

import subprocess
from grow.sdk.installers import base_installer


class ExtensionsInstaller(base_installer.BaseInstaller):
    """Grow extensions installer."""

    KIND = 'extensions'

    @property
    def post_install_messages(self):
        """List of messages to display after installing."""
        return ['Finished: Extensions -> {}/'.format(self.pod.extensions_dir)]

    @property
    def should_run(self):
        """Should the installer run?"""
        return self.pod.file_exists('/{}'.format(self.pod.FILE_EXTENSIONS))

    def check_prerequisites(self):
        """Check if required prerequisites are installed or available."""
        status_command = 'pip --version > /dev/null 2>&1'
        not_found = subprocess.call(
            status_command, **self.subprocess_args(shell=True)) == 127
        if not_found:
            raise base_installer.MissingPrerequisiteError(
                'The `pip` command was not found.')

    def install(self):
        """Install dependencies."""
        extensions_dir = self.pod.extensions_dir
        init_file_name = '/{}/__init__.py'.format(extensions_dir)
        if not self.pod.file_exists(init_file_name):
            self.pod.write_file(init_file_name, '')
        install_command = 'pip install -U -t {} -r {}'.format(
            extensions_dir, self.pod.FILE_EXTENSIONS)
        process = subprocess.Popen(
            install_command, **self.subprocess_args(shell=True))
        code = process.wait()
        if not code:
            return
        raise base_installer.InstallError(
            'There was an error running `{}`.'.format(install_command))
