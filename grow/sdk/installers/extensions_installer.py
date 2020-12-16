"""Grow extensions installer class."""

import subprocess
from grow.sdk.installers import base_installer


INSTALL_HASH_FILE_NAME = 'install-hash.txt'


class ExtensionsInstaller(base_installer.BaseInstaller):
    """Grow extensions installer."""

    KIND = 'extensions'

    def _generate_hashes(self):
        """Create hash string based on the package and lock files."""
        if not self.pod.file_exists(self.extensions_filename):
            return ''
        return self.pod.hash_file(self.extensions_filename)

    @property
    def post_install_messages(self):
        """List of messages to display after installing."""
        return ['Finished: Extensions -> {}/'.format(self.pod.extensions_dir)]

    @property
    def extensions_filename(self):
        """Filename for the install hash."""
        return '/{}'.format(self.pod.FILE_EXTENSIONS)

    @property
    def install_hash_filename(self):
        """Filename for the install hash."""
        return '/{}/{}'.format(self.pod.extensions_dir, INSTALL_HASH_FILE_NAME)

    @property
    def should_run(self):
        """Should the installer run?"""
        if not self.pod.file_exists(self.extensions_filename):
            return False

        if self.config.get('force', None):
            return True

        if self.pod.file_exists(self.install_hash_filename):
            existing_hash = self.pod.read_file(self.install_hash_filename)
            current_hash = self._generate_hashes()
            if existing_hash == current_hash:
                self.pod.logger.info('Skipping extensions install since no changes detected.')
                self.pod.logger.info('   Use `grow install -f` to force install.')
                return False
        return True

    def check_prerequisites(self):
        """Check if required prerequisites are installed or available."""
        status_command = 'pip3 --version > /dev/null 2>&1'
        not_found = subprocess.call(
            status_command, **self.subprocess_args(shell=True)) == 127
        if not_found:
            raise base_installer.MissingPrerequisiteError(
                'The `pip3` command was not found.')

    def install(self):
        """Install dependencies."""
        extensions_dir = self.pod.extensions_dir
        init_file_name = '/{}/__init__.py'.format(extensions_dir)
        if not self.pod.file_exists(init_file_name):
            self.pod.write_file(init_file_name, '')
        install_command = 'pip3 install -U -q -t {} -r {}'.format(
            extensions_dir, self.pod.FILE_EXTENSIONS)
        process = subprocess.Popen(
            install_command, **self.subprocess_args(shell=True))
        code = process.wait()
        if not code:
            self.pod.write_file(self.install_hash_filename, self._generate_hashes())
            return
        raise base_installer.InstallError(
            'There was an error running `{}`.'.format(install_command))
