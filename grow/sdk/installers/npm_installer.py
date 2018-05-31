"""NPM installer class."""

import subprocess
from grow.sdk import sdk_utils
from grow.sdk.installers import base_installer


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
        return self.pod.file_exists('/package.json')

    @property
    def using_yarn(self):
        """Is the pod using yarn?"""
        if self._using_yarn is None:
            self._using_yarn = self.pod.file_exists('/yarn.lock')
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

    def _install_npm(self):
        """Install dependencies using npm."""
        install_command = self._nvm_command('npm install')
        process = subprocess.Popen(install_command, **self.subprocess_args(shell=True))
        code = process.wait()
        if not code:
            return
        raise base_installer.InstallError(
            'There was an error running `npm install`.')

    def _install_yarn(self):
        """Install dependencies using npm."""
        install_command = 'yarn install'
        process = subprocess.Popen(install_command, **self.subprocess_args(shell=True))
        code = process.wait()
        if not code:
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
