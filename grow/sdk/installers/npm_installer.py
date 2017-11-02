"""NPM installer class."""

from grow.sdk.installers import base_installer


class NpmInstaller(base_installer.BaseInstaller):
    """Grow npm and yarn installer."""

    KIND = 'NPM'

    @property
    def using_yarn(self):
        """Is the pod using yarn?"""
        return self.pod.file_exists('/yarn.lock')

    @property
    def should_run(self):
        """Should the installer run?"""
        return self.pod.file_exists('/package.json')

    def check_prerequisites(self):
        """Check if required prerequisites are installed or available."""
        pass

    def install(self):
        """Install dependencies using npm."""
        pass
