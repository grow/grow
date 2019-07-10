"""NPM installer class."""

import subprocess
from grow.sdk import sdk_utils
from grow.sdk.installers import base_installer


INSTALL_HASH_FILE = '/node_modules/install-hash.txt'
NPM_LOCK_FILE = '/package-lock.json'
PACKAGE_FILE = '/package.json'
YARN_LOCK_FILE = '/yarn.lock'


class NpmInstaller(base_installer.BaseInstaller):
    """Grow npm and yarn installer."""

    KIND = 'npm'

    def __init__(self, pod, config):
        super(NpmInstaller, self).__init__(pod, config)
        self._using_yarn = None

    @property
    def post_install_messages(self):
        """List of messages to display after installing."""
        if self.using_yarn:
            return ['Finished: yarn']
        return ['Finished: npm']

    @property
    def should_run(self):
        """Should the installer run?"""
        if not self.pod.file_exists(PACKAGE_FILE):
            return False

        if self.config.get('force', None):
            return True

        if self.pod.file_exists(INSTALL_HASH_FILE):
            existing_hash = self.pod.read_file(INSTALL_HASH_FILE)
            current_hash = self._generate_hashes()
            if existing_hash == current_hash:
                self.pod.logger.info('Skipping npm/yarn install since no changes detected.')
                self.pod.logger.info('   Use `grow install -f` to force install.')
                return False
        return True

    @property
    def using_yarn(self):
        """Is the pod using yarn?"""
        if self._using_yarn is None:
            self._using_yarn = self.pod.file_exists(YARN_LOCK_FILE)
        return self._using_yarn

    def _check_prerequisites_npm(self):
        """Check if required prerequisites are installed or available."""
        status_command = self._nvm_command('npm --version > /dev/null 2>&1')
        not_found = subprocess.call(
            status_command, **self.subprocess_args(shell=True)) == 127
        if not_found:
            install_commands = []
            if sdk_utils.PLATFORM == 'linux':
                install_commands.append(
                    'On Linux, you can install npm using: `apt-get install nodejs`')
            elif sdk_utils.PLATFORM == 'mac':
                install_commands.append(
                    'Using brew (https://brew.sh), you can install using: `brew install node`')
                install_commands.append(('If you do not have brew, you can download '
                                         'Node.js from https://nodejs.org'))
            else:
                install_commands.append(
                    'Download Node.js from https://nodejs.org')
            raise base_installer.MissingPrerequisiteError(
                'The `npm` command was not found.', install_commands=install_commands)

    def _check_prerequisites_yarn(self):
        """Check if required prerequisites are installed or available."""
        status_command = 'yarn --version > /dev/null 2>&1'
        not_found = subprocess.call(
            status_command, **self.subprocess_args(shell=True)) == 127
        if not_found:
            install_commands = [
                'Install yarn from https://yarnpkg.com/en/docs/install']
            raise base_installer.MissingPrerequisiteError(
                'The `yarn` command was not found.', install_commands=install_commands)

    def _generate_hashes(self):
        """Create hash string based on the package and lock files."""
        hash_string = ''
        if self.pod.file_exists(PACKAGE_FILE):
            hash_string = self.pod.hash_file(PACKAGE_FILE)
        if self.pod.file_exists(YARN_LOCK_FILE):
            hash_string = '{} {}'.format(hash_string, self.pod.hash_file(YARN_LOCK_FILE))
        if self.pod.file_exists(NPM_LOCK_FILE):
            hash_string = '{} {}'.format(hash_string, self.pod.hash_file(NPM_LOCK_FILE))
        return hash_string

    def _install_npm(self):
        """Install dependencies using npm."""
        install_command = self._nvm_command('npm install')
        process = subprocess.Popen(install_command, **self.subprocess_args(shell=True))
        code = process.wait()
        if not code:
            self.pod.write_file(INSTALL_HASH_FILE, self._generate_hashes())
            return
        raise base_installer.InstallError(
            'There was an error running `npm install`.')

    def _install_yarn(self):
        """Install dependencies using npm."""
        install_command = 'yarn install'
        process = subprocess.Popen(install_command, **self.subprocess_args(shell=True))
        code = process.wait()
        if not code:
            self.pod.write_file(INSTALL_HASH_FILE, self._generate_hashes())
            return
        raise base_installer.InstallError(
            'There was an error running `yarn install`.')

    def _nvm_command(self, command):
        if self.pod.file_exists('/.nvmrc'):
            # Need to source NVM first to get the nvm command to work.
            return '. $NVM_DIR/nvm.sh && nvm exec {}'.format(command)
        return command

    def check_prerequisites(self):
        """Check if required prerequisites are installed or available."""
        if self.using_yarn:
            self._check_prerequisites_yarn()
        else:
            self._check_prerequisites_npm()

    def install(self):
        """Install dependencies."""
        if self.using_yarn:
            return self._install_yarn()
        return self._install_npm()
